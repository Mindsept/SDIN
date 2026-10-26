"""Exercise lifecycle boundaries with fake executables, never a live platform."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
REAL_FLOCK = shutil.which('flock')
FAKE = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['TRACE'], 'a') as out:
    out.write(json.dumps({'name': name, 'args': args, 'cwd': os.getcwd(),
                          'app': os.environ.get('APP'), 'tag': os.environ.get('TAG'),
                          'llm': os.environ.get('LLM_VKEY')}) + '\n')
if os.environ.get('FAIL_MATCH') and os.environ['FAIL_MATCH'] in ' '.join([name] + args):
    sys.exit(1)
if name == 'bun' and args == ['--version']: print('1.3.1')
if name == 'podman':
    if args[0] == 'info': print('true')
    if args[:2] == ['container', 'exists'] or args[:2] == ['volume', 'exists']: sys.exit(1)
    if args[:2] == ['network', 'exists']: sys.exit(0 if os.environ.get('NETWORK_EXISTS') else 1)
    if 'config' in args: print(os.environ.get('COMPOSE_SERVICES', 'frontend'))
    if 'temporal.internal' in args: print('SERVING')
    if args[0] == 'push' and not os.environ.get('NO_DIGEST'):
        pathlib.Path(args[args.index('--digestfile') + 1]).write_text('sha256:' + 'a' * 64 + '\n')
if name == 'curl':
    if os.environ.get('UNREADY'): sys.exit(22)
    if '-w' in args: print(os.environ.get('AUTH_CODE', '401'), end='')
'''


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.env = os.environ.copy()
        # Do not inherit credentials or GitHub paths from the invoking environment.
        for key in list(self.env):
            if key.startswith(('GITHUB_', 'OPENAI_', 'ANTHROPIC_', 'BAO_', 'VAULT_', 'SDI_')):
                self.env.pop(key)
        self.env.update(PATH=f'{self.bin}:{os.environ["PATH"]}', TRACE=str(self.base / 'trace'),
                        HOME=str(self.base / 'home'), SDI_STATE_DIR=str(self.base / 'state'),
                        SDI_VERIFY_ATTEMPTS='1', SDI_VERIFY_INTERVAL='0', TAG='test-sha')
        for tool in ['podman', 'curl', 'bun', 'systemctl', 'gitleaks', 'seed', 'bootstrap', 'preflight']:
            self.executable(self.bin / tool, FAKE)
        if not REAL_FLOCK:
            self.executable(self.bin / 'flock', '#!/bin/sh\nexit 0\n')

    def executable(self, path, source):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        path.chmod(0o755)

    def core(self):
        path = self.base / 'core'
        path.mkdir()
        shutil.copy(ROOT / 'td/core-platform/lifecycle.sh', path / 'lifecycle.sh')
        self.executable(path / 'preflight.sh', '#!/bin/sh\nexec preflight "$@"\n')
        for helper in ['objectstore/seed-admin.sh', 'temporal/seed-namespaces.sh',
                       'idp/seed-and-deploy.sh', 'apisix/seed-and-deploy.sh', 'analytics/seed-and-deploy.sh']:
            self.executable(path / helper, f'#!/bin/sh\nexec seed {helper}\n')
        (path / 'apisix/routes.openai.yaml').write_text('routes: []\n')
        return path / 'lifecycle.sh'

    def app(self, extra=''):
        path = self.base / 'app'
        path.mkdir()
        shutil.copy(ROOT / 'td/core-platform/templates/app-lifecycle.sh', path / 'app-lifecycle.sh')
        (path / 'app.env').write_text('APP=demo\nSERVICES="frontend"\nINTEGRATION_SERVICES=""\n'
                                    'BUN_VERSION=1.3.1\nLLM_VKEY=1\n' + extra)
        (path / 'frontend').mkdir()
        self.executable(path / 'bootstrap.sh', '#!/bin/sh\nexec bootstrap\n')
        self.executable(path / 'ci/install-gitleaks.sh', '#!/bin/sh\ncommand -v gitleaks\n')
        return path / 'app-lifecycle.sh'

    def run_script(self, script, action, ok=True, **env):
        result = subprocess.run(['bash', str(script), action], cwd=self.base,
                                env={**self.env, **env}, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def calls(self):
        trace = self.base / 'trace'
        return [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []

    def test_core_start_preserves_helpers_and_initialization_order(self):
        script = self.core()
        self.run_script(script, 'start')
        helpers = [c['args'][0] for c in self.calls() if c['name'] == 'seed']
        self.assertEqual(helpers, ['objectstore/seed-admin.sh', 'temporal/seed-namespaces.sh',
                                  'idp/seed-and-deploy.sh', 'apisix/seed-and-deploy.sh',
                                  'analytics/seed-and-deploy.sh'])
        self.assertTrue((script.parent / 'apisix/apisix.yaml').is_file())
        self.assertTrue(all(Path(c['cwd']).resolve() == script.parent.resolve() for c in self.calls()))

    def test_core_seed_failure_blocks_later_steps(self):
        self.run_script(self.core(), 'start', ok=False, FAIL_MATCH='seed idp/')
        self.assertFalse(any(c['name'] == 'seed' and c['args'][0].startswith('analytics/') for c in self.calls()))

    def test_core_authentication_check_is_blocking(self):
        self.run_script(self.core(), 'start', ok=False, AUTH_CODE='200')

    def test_core_unready_is_failure(self):
        self.run_script(self.core(), 'start', ok=False, UNREADY='1')

    def test_core_network_creation_error_is_not_treated_as_already_existing(self):
        self.run_script(self.core(), 'start', ok=False, FAIL_MATCH='podman network create')
        self.assertFalse(any(c['name'] == 'seed' for c in self.calls()))

    def test_core_stop_preserves_volumes_and_does_not_seed(self):
        self.run_script(self.core(), 'stop')
        self.assertFalse(any(c['name'] == 'seed' for c in self.calls()))
        self.assertTrue(any(c['args'] == ['compose', '-p', 'core', 'down'] for c in self.calls()))
        self.assertFalse(any('--volumes' in c['args'] for c in self.calls()))

    def test_core_purge_requires_exact_confirmation_before_any_command(self):
        self.run_script(self.core(), 'purge', ok=False, CONFIRM_PURGE='demo')
        self.assertEqual([], self.calls())

    def test_confirmed_core_purge_removes_runtime_volumes(self):
        self.run_script(self.core(), 'purge', CONFIRM_PURGE='core')
        self.assertTrue(any(c['args'] == ['compose', '-p', 'core', 'down', '--volumes'] for c in self.calls()))

    def test_core_unknown_action_is_rejected(self):
        self.run_script(self.core(), 'restart', ok=False)
        self.assertEqual([], self.calls())

    def test_core_check_detects_broken_shell_without_platform_access(self):
        script = self.core()
        (script.parent / 'broken.sh').write_text('if then\n')
        self.run_script(script, 'check', ok=False)
        self.assertEqual([], self.calls())

    def test_app_check_has_no_platform_calls(self):
        self.run_script(self.app(), 'check')
        self.assertFalse(any(c['name'] in ('podman', 'bootstrap') for c in self.calls()))
        self.assertTrue(any(c['name'] == 'gitleaks' for c in self.calls()))

    def test_failing_gate_prevents_provisioning_and_deployment(self):
        self.run_script(self.app(), 'start', ok=False, FAIL_MATCH='bun run typecheck')
        self.assertFalse(any(c['name'] in ('podman', 'bootstrap') for c in self.calls()))

    def test_invalid_or_reserved_app_never_reaches_platform(self):
        script = self.app()
        for name in ['postgres', 'core', 'template1', 'bad/name', 'demo;echo', '']:
            with self.subTest(name=name):
                (script.parent / 'app.env').write_text(f'APP="{name}"\nSERVICES=frontend\nBUN_VERSION=1.3.1\n')
                self.run_script(script, 'start', ok=False)
        self.assertEqual([], self.calls())

    def test_invalid_purge_confirmation_does_not_run_checks_or_platform(self):
        self.run_script(self.app(), 'purge', ok=False, CONFIRM_PURGE='other-app')
        self.assertEqual([], self.calls())

    def test_invalid_app_settings_fail_before_mutating_the_platform(self):
        script = self.app()
        base = (script.parent / 'app.env').read_text()
        for setting in ['PROVISION=maybe', 'APP_SECRETS="postgres ../core/idp"', 'FRONTEND_PORT=8200']:
            with self.subTest(setting=setting):
                (script.parent / 'app.env').write_text(base + setting + '\n')
                self.run_script(script, 'purge', ok=False, CONFIRM_PURGE='demo')
        self.assertEqual([], self.calls())

    def test_app_purge_does_not_delete_database_or_bucket(self):
        self.run_script(self.app(), 'purge', CONFIRM_PURGE='demo')
        calls = self.calls()
        self.assertFalse(any(c['name'] == 'bun' for c in calls))
        deletes = [c for c in calls if 'delete' in c['args']]
        self.assertEqual(len(deletes), 7)
        self.assertTrue(all(c['args'][-1].startswith('secret/demo/') for c in deletes))
        self.assertFalse(any('psql' in c['args'] or 'weed' in c['args'] for c in calls))

    def test_app_start_builds_and_pushes_selected_component_and_records_digest(self):
        self.run_script(self.app('REGISTRY=registry.example:5000\n'), 'start')
        pushes = [c for c in self.calls() if c['name'] == 'podman' and c['args'][0] == 'push']
        self.assertEqual(len(pushes), 1)
        self.assertEqual(pushes[0]['args'][-1], 'registry.example:5000/demo/frontend:test-sha')
        deploy = [c for c in self.calls() if '--force-recreate' in c['args']][0]
        self.assertEqual(deploy['tag'], 'test-sha')
        self.assertEqual((self.base / 'state/releases/demo/test-sha/frontend.digest').read_text().strip(), 'sha256:' + 'a' * 64)
        self.assertEqual([c for c in self.calls() if c['name'] == 'bootstrap'][0]['llm'], '1')

    def test_app_bootstrap_can_be_skipped(self):
        self.run_script(self.app('PROVISION=0\n'), 'start')
        self.assertFalse(any(c['name'] == 'bootstrap' for c in self.calls()))

    def test_compose_services_must_match_selection(self):
        self.run_script(self.app(), 'start', ok=False, COMPOSE_SERVICES='frontend\napi')
        self.assertFalse(any(c['name'] == 'bootstrap' for c in self.calls()))

    def test_push_failure_prevents_deployment(self):
        self.run_script(self.app(), 'start', ok=False, FAIL_MATCH='podman push')
        self.assertFalse(any('--force-recreate' in c['args'] for c in self.calls()))

    def test_missing_digest_is_not_a_successful_release(self):
        self.run_script(self.app(), 'start', ok=False, NO_DIGEST='1')
        self.assertFalse(any('--force-recreate' in c['args'] for c in self.calls()))

    def test_app_readiness_failure_is_blocking(self):
        self.run_script(self.app(), 'start', ok=False, UNREADY='1')

    def test_app_integration_failure_prevents_image_publication(self):
        script = self.app('SERVICES="frontend api"\nINTEGRATION_SERVICES=api\n')
        (script.parent / 'api').mkdir()
        self.run_script(script, 'start', ok=False, COMPOSE_SERVICES='frontend\napi', FAIL_MATCH='bun run test:integration')
        self.assertFalse(any(c['args'] and c['args'][0] == 'push' for c in self.calls()))

    @unittest.skipUnless(REAL_FLOCK, 'real flock is checked on the Linux CI runner')
    def test_shared_lock_blocks_core_and_app_mutations(self):
        state = self.base / 'state'
        state.mkdir()
        with (state / 'lifecycle.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.run_script(self.core(), 'stop', ok=False, SDI_LOCK_TIMEOUT='0')
            self.run_script(self.app(), 'stop', ok=False, SDI_LOCK_TIMEOUT='0')
        self.assertEqual([], self.calls())


if __name__ == '__main__':
    unittest.main()
