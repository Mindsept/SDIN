"""Verify generated app provisioning against stateful doubles, never SDIN."""
import importlib.util
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'Skills/devops_and_choice/scripts/prepare_bootstrap.py'
TEMPLATE = ROOT / 'td/core-platform/templates/bootstrap.sh'
spec = importlib.util.spec_from_file_location('prepare_bootstrap', SCRIPT)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)
FLAGS = ['USE_POSTGRES', 'USE_OBJECTSTORE', 'LLM_VKEY', 'TEMPORAL_NS', 'ANALYTICS_SITE']
FAKE = r'''#!/usr/bin/env python3
import json, os, pathlib, re, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
state_path = pathlib.Path(os.environ['STATE'])
state = json.loads(state_path.read_text())
with open(os.environ['TRACE'], 'a') as log:
    log.write(json.dumps([name, args]) + '\n')
if os.environ.get('FAIL_MATCH') and os.environ['FAIL_MATCH'] in ' '.join([name] + args):
    sys.exit(1)
app = os.environ['APP']
if name == 'bao':
    if args == ['status']: sys.exit(0)
    assert args[0] == 'kv', args
    action = args[1]
    path = next(arg for arg in args[2:] if arg.startswith('secret/'))
    if action == 'get':
        field = next(arg.split('=', 1)[1] for arg in args if arg.startswith('-field='))
        value = state['secrets'].get(path, {}).get(field)
        if value is None: sys.exit(2)
        print(value); sys.exit(0)
    values = dict(arg.split('=', 1) for arg in args[2:] if '=' in arg and not arg.startswith('-'))
    if action == 'patch':
        if path not in state['secrets']: sys.exit(2)
        state['secrets'][path].update(values)
    elif action == 'put':
        if '-cas=0' in args and path in state['secrets']: sys.exit(2)
        state['secrets'][path] = values
    else: raise AssertionError(args)
elif name == 'openssl':
    print('fakecredential1234567890'); sys.exit(0)
elif name == 'podman':
    if 'psql' in args:
        sql = args[-1]
        if 'SELECT' in sql:
            if ('pg_database' in sql and state['pg_db']) or ('pg_user' in sql and state['pg_role']): print('1')
        elif 'CREATE DATABASE' in sql: state['pg_db'] = True
        elif 'CREATE USER' in sql: state['pg_role'] = True
    elif args[:2] == ['container', 'exists']:
        sys.exit(1)
    else:
        command = args[-1]
        if 's3.bucket.list' in command:
            if state['bucket']: print(app + '\tsize:0')
        elif 's3.bucket.create' in command: state['bucket'] = True
        elif 's3.configure' in command:
            state['s3_commands'].append(command)
        else: raise AssertionError(args)
elif name == 'temporal':
    if 'health' in args: print('SERVING'); sys.exit(0)
    if 'describe' in args: sys.exit(0 if state['namespace'] else 1)
    if 'create' in args: state['namespace'] = True
elif name == 'site-create.sh':
    state['secrets'][f'secret/{app}/analytics'] = {'website_id': 'fake-site'}
else: raise AssertionError((name, args))
state_path.write_text(json.dumps(state))
'''


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.script = self.base / 'bootstrap.sh'
        self.script.write_text(generator.adapt(TEMPLATE.read_text()))
        self.bin = self.base / 'bin'
        self.bin.mkdir()
        self.state_path = self.base / 'state.json'
        self.trace = self.base / 'trace'
        self.initial = dict(secrets={'secret/core/llm-vkeys': {'another-app': 'keep-me'}},
                            pg_db=False, pg_role=False, bucket=False, namespace=False, s3_commands=[])
        self.state_path.write_text(json.dumps(self.initial))
        self.env = {key: value for key, value in os.environ.items()
                    if key in ('PATH', 'SYSTEMROOT', 'TMPDIR', 'LANG')}
        self.env.update(APP='demo-app', PATH=f'{self.bin}:{os.environ["PATH"]}',
                        STATE=str(self.state_path), TRACE=str(self.trace),
                        CORE_PLATFORM=str(self.base / 'core'), BAO_BIN=str(self.bin / 'bao'))
        for name in ['bao', 'podman', 'openssl', 'temporal']:
            self.executable(self.bin / name)
        self.executable(self.base / 'core/analytics/site-create.sh')

    def executable(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(FAKE)
        path.chmod(0o755)

    def run_bootstrap(self, *args, success=True, **settings):
        result = subprocess.run(['bash', str(self.script), *args], env=self.env | settings,
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode == 0, success, result.stdout + result.stderr)
        return result

    def state(self):
        return json.loads(self.state_path.read_text())

    def calls(self):
        return self.trace.read_text().splitlines() if self.trace.exists() else []

    def test_no_selection_is_a_real_noop(self):
        result = self.run_bootstrap()
        self.assertIn('nothing to provision', result.stdout)
        self.assertEqual(self.calls(), [])

    def test_plan_never_probes_or_leaks_credentials(self):
        result = self.run_bootstrap('--plan', **dict.fromkeys(FLAGS, '1'), BAO_TOKEN='not-for-output')
        self.assertIn('secret/demo-app/temporal', result.stdout)
        self.assertNotIn('not-for-output', result.stdout + result.stderr)
        self.assertEqual(self.calls(), [])

    def test_every_service_subset_only_provisions_selected_resources(self):
        for bits in itertools.product('01', repeat=len(FLAGS)):
            with self.subTest(flags=bits):
                self.state_path.write_text(json.dumps(self.initial))
                self.trace.unlink(missing_ok=True)
                self.run_bootstrap(**dict(zip(FLAGS, bits)))
                state = self.state()
                self.assertEqual([state['pg_db'], state['bucket'],
                                  'secret/demo-app/llm' in state['secrets'], state['namespace'],
                                  'secret/demo-app/analytics' in state['secrets']],
                                 [value == '1' for value in bits])
                self.assertEqual(state['secrets']['secret/core/llm-vkeys']['another-app'], 'keep-me')
                calls = '\n'.join(self.calls())
                for selected, operation in zip(bits, ['psql', 's3.bucket', 'llm-vkeys', 'namespace', 'site-create.sh']):
                    if selected == '0': self.assertNotIn(operation, calls)

    def test_repeat_keeps_credentials_and_does_not_recreate_resources(self):
        flags = dict.fromkeys(FLAGS, '1')
        self.run_bootstrap(**flags)
        first = self.state()
        self.trace.unlink()
        self.run_bootstrap(**flags)
        self.assertEqual(first, self.state())
        calls = '\n'.join(self.calls())
        for forbidden in ['openssl', 'CREATE DATABASE', 'CREATE USER', 's3.bucket.create', 's3.configure']:
            self.assertNotIn(forbidden, calls)
        self.assertNotIn('"create"', calls)

    def test_invalid_flags_and_app_names_fail_before_any_command(self):
        for flag in FLAGS + ['PUBLIC_BUCKET']:
            for value in ['', 'yes', '2', '01']:
                with self.subTest(flag=flag, value=value):
                    self.run_bootstrap(success=False, **{flag: value})
        for app in ['../core', 'postgres', 'casdoor', 'default', 'a;whoami', 'my--app', 'a' * 41]:
            with self.subTest(app=app):
                self.run_bootstrap(success=False, APP=app)
        self.run_bootstrap('--unknown', success=False)
        self.run_bootstrap(success=False, PUBLIC_BUCKET='1')
        self.assertEqual(self.calls(), [])

    def test_public_grant_is_scoped_and_explicit(self):
        self.run_bootstrap(USE_OBJECTSTORE='1', PUBLIC_BUCKET='1')
        commands = self.state()['s3_commands']
        self.assertTrue(any('-user=anonymous -buckets=demo-app -actions=Read -apply' in cmd for cmd in commands))

    def test_postgres_partial_state_stops_without_password_rotation(self):
        self.initial['pg_db'] = True
        self.state_path.write_text(json.dumps(self.initial))
        self.run_bootstrap(success=False, USE_POSTGRES='1')
        self.assertNotIn('ALTER USER', '\n'.join(self.calls()))
        self.assertEqual(self.state(), self.initial)

    def test_s3_partial_state_stops_without_new_identity(self):
        self.initial['bucket'] = True
        self.state_path.write_text(json.dumps(self.initial))
        for public in ['0', '1']:
            self.run_bootstrap(success=False, USE_OBJECTSTORE='1', PUBLIC_BUCKET=public)
            self.assertEqual(self.state(), self.initial)

    def test_s3_listing_failure_does_not_create_a_bucket(self):
        self.run_bootstrap(success=False, USE_OBJECTSTORE='1', FAIL_MATCH='s3.bucket.list')
        self.assertFalse(self.state()['bucket'])

    def test_postgres_query_failure_does_not_create_a_database(self):
        self.run_bootstrap(success=False, USE_POSTGRES='1', FAIL_MATCH='SELECT')
        self.assertFalse(self.state()['pg_db'])

    def test_patch_failure_cannot_replace_an_existing_shared_key_map(self):
        self.run_bootstrap(success=False, LLM_VKEY='1', FAIL_MATCH='kv patch')
        self.assertEqual(self.state()['secrets'], self.initial['secrets'])

    def test_first_llm_key_can_create_an_absent_map_using_cas_zero(self):
        self.initial['secrets'] = {}
        self.state_path.write_text(json.dumps(self.initial))
        self.run_bootstrap(LLM_VKEY='1')
        self.assertIn('demo-app', self.state()['secrets']['secret/core/llm-vkeys'])
        self.assertIn('-cas=0', '\n'.join(self.calls()))

    def test_dependency_failure_stops_later_selected_steps(self):
        self.run_bootstrap(success=False, TEMPORAL_NS='1', ANALYTICS_SITE='1', FAIL_MATCH='namespace create')
        self.assertNotIn('secret/demo-app/analytics', self.state()['secrets'])

    def test_secret_store_outage_stops_before_any_resource_mutation(self):
        self.run_bootstrap(success=False, **dict.fromkeys(FLAGS, '1'), FAIL_MATCH='bao status')
        self.assertEqual(self.state(), self.initial)

    def test_resolved_symlink_cannot_write_into_td(self):
        link = self.base / 'platform-link'
        link.symlink_to(TEMPLATE.parent, target_is_directory=True)
        result = subprocess.run([sys.executable, str(SCRIPT), '--output', str(link / 'blocked-bootstrap.sh')],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((TEMPLATE.parent / 'blocked-bootstrap.sh').exists())

    def test_missing_helper_is_detected_before_creating_other_resources(self):
        (self.base / 'core/analytics/site-create.sh').unlink()
        self.run_bootstrap(success=False, USE_POSTGRES='1', ANALYTICS_SITE='1')
        self.assertEqual(self.calls(), [])

    def test_template_change_is_rejected_and_crlf_is_supported(self):
        source = TEMPLATE.read_text()
        self.assertEqual(generator.adapt(source), generator.adapt(source.replace('\n', '\r\n')))
        with self.assertRaises(ValueError): generator.adapt(source + '\n# changed\n')

    def test_secret_resolver_is_preserved_verbatim(self):
        def resolver(text): return text.split('# --8<-- [start:bao]', 1)[1].split('# --8<-- [end:bao]', 1)[0]
        self.assertEqual(resolver(TEMPLATE.read_text()), resolver(self.script.read_text()))

    def test_generator_refuses_overwrite_and_platform_output(self):
        for output in [self.script, TEMPLATE.parent / 'blocked-bootstrap.sh']:
            result = subprocess.run([sys.executable, str(SCRIPT), '--output', str(output)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        self.assertFalse((TEMPLATE.parent / 'blocked-bootstrap.sh').exists())

    def test_generator_creates_an_executable_without_running_it(self):
        output = self.base / 'new-bootstrap.sh'
        result = subprocess.run([sys.executable, str(SCRIPT), '--output', str(output)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(os.access(output, os.X_OK))
        self.assertEqual(self.calls(), [])
        subprocess.run(['bash', '-n', str(output)], check=True)
        shellcheck = shutil.which('shellcheck')
        if shellcheck:
            # The unchanged canonical resolver intentionally sets both BAO/VAULT env
            # prefixes from the same parent values; these two diagnostics are false positives.
            subprocess.run([shellcheck, '-S', 'warning', '-e', 'SC2097,SC2098', str(output)], check=True)


if __name__ == '__main__':
    unittest.main()
