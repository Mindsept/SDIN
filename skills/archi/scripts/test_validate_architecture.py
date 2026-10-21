#!/usr/bin/env python3
"""Behavioral checks for the read-only declaration validator (stdlib only)."""

import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("validate_architecture.py")
EXAMPLE = SCRIPT.parent.parent / "assets" / "architecture.example.json"
SPEC = importlib.util.spec_from_file_location("architecture_validator", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
AS_OF = dt.date(2026, 10, 14)


class DeclarationTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def check(self, expected, rule=None, document=None, repo=None):
        code, diagnostics = validator.validate(document or self.document, AS_OF, repo)
        self.assertEqual(expected, code, diagnostics)
        if rule:
            self.assertTrue(any(d["rule"] == rule and d["level"] == "ERROR" for d in diagnostics), diagnostics)
        return diagnostics

    def waiver(self, rule="STACK-001", scope="backend"):
        return {
            "id": "decision-test", "rule_id": rule, "scope": scope,
            "reason": "Interoperability requirement recorded for this test fixture.",
            "alternatives": ["Rewrite evaluated and rejected in the fixture ADR."],
            "compute_impact": "No additional long-running process.",
            "evidence": ["Test fixture only; no real human approval is asserted."],
            "approved_by": "Human reviewer in test fixture",
            "approved_on": "2026-10-01", "expires_on": "2026-11-01",
            "rollback": "Migrate the implementation after the compatibility constraint ends."
        }

    def test_ready_django_without_waiver_in_compatible_policy(self):
        self.check(0)

    def test_unknown_context_is_representable_in_draft_but_blocks_ready(self):
        self.document["project"]["context"] = "unknown"
        self.check(1, "READY-001")
        self.document["status"] = "draft"
        diagnostics = self.check(0)
        self.assertTrue(any(d["path"] == "$.project.context" and d["level"] == "WARNING"
                            for d in diagnostics))
        self.document["project"]["context"] = "unrecognized-context"
        self.check(2, "SCHEMA")

    def test_draft_can_record_missing_decisions_and_blocking_unknown(self):
        self.document["status"] = "draft"
        self.document["requirements"]["summary"] = ""
        self.document["requirements"]["unknowns"] = [{"question": "What volume?", "blocking": True}]
        self.document["architecture"]["rationale"] = ""
        self.document["architecture"]["alternatives"] = []
        self.document["components"] = []
        self.document["platform"]["services"] = []
        diagnostics = self.check(0)
        self.assertTrue(any(d["level"] == "WARNING" for d in diagnostics))

    def test_ready_rejects_blocking_unknown_but_allows_nonblocking(self):
        question = {"question": "Which color theme?", "blocking": False}
        self.document["requirements"]["unknowns"] = [question]
        self.check(0)
        question["blocking"] = True
        self.check(1, "READY-001")

    def test_ready_cannot_omit_justification_or_alternatives(self):
        for field in ("rationale", "compute_tradeoff", "alternatives"):
            with self.subTest(field=field):
                document = copy.deepcopy(self.document)
                document["architecture"][field] = [] if field == "alternatives" else "  "
                self.check(1, "READY-001", document)
        self.document["components"][1]["framework_rationale"] = ""
        self.check(1, "READY-001")

    def test_schema_rejects_unknown_missing_and_wrong_typed_fields(self):
        cases = [
            lambda d: d.update(unknown=True),
            lambda d: d["project"].update(extra="wrong"),
            lambda d: d["operations"].pop("health_endpoints"),
            lambda d: d.update(schema_version=True),
            lambda d: d["platform"].update(app_port_base=True),
            lambda d: d["operations"].update(shutdown_seconds=False),
            lambda d: d["operations"].update(health_endpoints=1),
            lambda d: d["components"][0].update(layers=[]),
            lambda d: d["requirements"].update(unknowns=[{"question": "q", "blocking": 0}]),
            lambda d: d["components"][0].update(framework=""),
            lambda d: d.update(components=None),
            lambda d: d["operations"].update(shutdown_seconds=-1),
        ]
        for mutate in cases:
            document = copy.deepcopy(self.document)
            mutate(document)
            with self.subTest(document=document):
                self.check(2, "SCHEMA", document)

    def test_ids_and_references_are_unambiguous(self):
        cases = [
            lambda d: d["components"][1].update(id="web"),
            lambda d: d["components"][0].update(platform_services=["redis"]),
            lambda d: d["platform"].update(services=["postgres", "postgres"]),
            lambda d: d["components"][0].update(platform_services=["valkey"]),
            lambda d: d["components"][0].update(id="*"),
        ]
        for mutate in cases:
            document = copy.deepcopy(self.document)
            mutate(document)
            self.check(2, "SCHEMA", document)

    def test_clients_must_not_consume_private_services_directly(self):
        for role in ("frontend", "native"):
            for service in validator.PRIVATE_SERVICES:
                document = copy.deepcopy(self.document)
                document["components"][0]["role"] = role
                document["components"][0]["platform_services"] = [service]
                document["platform"]["services"] = sorted(set(document["platform"]["services"]) | {service})
                with self.subTest(role=role, service=service):
                    self.check(1, "PLAT-001", document)
        self.document["components"][0]["platform_services"] = ["s3", "casdoor"]
        self.check(0)

    def test_port_range_reserved_block_and_collisions(self):
        for base in (7990, 8001, 8200, 9000, -1):
            self.document["platform"]["app_port_base"] = base
            self.check(1, "PLAT-002")
        for base in (None, 8000, 8190, 8210, 8990):
            self.document["platform"]["app_port_base"] = base
            self.check(0)
        duplicate = copy.deepcopy(self.document["components"][1])
        duplicate["id"] = "second-api"
        self.document["components"].append(duplicate)
        self.check(1, "PLAT-002")
        self.document["platform"]["app_port_base"] = None
        self.check(0)

    def test_vector_requires_selected_postgres(self):
        self.document["platform"]["vector_enabled"] = True
        self.check(0)
        self.document["platform"]["services"].remove("postgres")
        self.document["components"][1]["platform_services"].remove("postgres")
        self.document["components"][1]["data_access"] = "none"
        self.check(1, "DATA-001")

    def test_data_access_requires_postgres_on_the_component(self):
        self.document["components"][1]["platform_services"].remove("postgres")
        for access in ("orm", "query-builder", "sql"):
            self.document["components"][1]["data_access"] = access
            self.check(1, "DATA-002")
        self.document["components"][1]["data_access"] = "none"
        self.check(0)

    def test_api_layers_ready_error_draft_warning(self):
        for layer in ("transport", "application", "persistence"):
            document = copy.deepcopy(self.document)
            document["components"][1]["layers"][layer] = []
            self.check(1, "ARCH-001", document)
            document["status"] = "draft"
            diagnostics = self.check(0, document=document)
            self.assertTrue(any(d["rule"] == "ARCH-001" and d["level"] == "WARNING" for d in diagnostics))

    def test_strict_typescript_needs_scoped_valid_waiver_for_python(self):
        self.document["project"]["policy"] = "strict-typescript"
        self.check(1, "STACK-001")
        self.document["waivers"] = [self.waiver()]
        diagnostics = self.check(0)
        self.assertTrue(any(d["level"] == "WAIVED" and d["rule"] == "STACK-001" for d in diagnostics))
        self.document["waivers"][0]["scope"] = "web"
        self.check(1, "STACK-001")

    def test_architecture_waiver_does_not_bypass_ready_justification(self):
        self.document["components"][1]["layers"]["application"] = []
        self.document["waivers"] = [self.waiver("ARCH-001")]
        self.check(0)
        self.document["components"][1]["rationale"] = ""
        self.check(1, "READY-001")

    def test_unknown_rules_missing_scope_and_incomplete_approval_rejected(self):
        for field, value in (("rule_id", "UNKNOWN"), ("scope", "missing"), ("approved_by", " "),
                             ("evidence", []), ("alternatives", "none"), ("approved_on", "2026-02-30")):
            document = copy.deepcopy(self.document)
            waiver = self.waiver()
            waiver[field] = value
            document["waivers"] = [waiver]
            self.check(2, "SCHEMA", document)

    def test_waiver_expiry_future_and_chronology_even_for_draft(self):
        self.document["status"] = "draft"
        for approved, expires in (("2026-10-01", "2026-10-13"), ("2026-10-15", "2026-11-01"),
                                  ("2026-10-01", "2026-09-30")):
            waiver = self.waiver()
            waiver.update(approved_on=approved, expires_on=expires)
            self.document["waivers"] = [waiver]
            self.check(1, "WAIVER")
        waiver = self.waiver()
        waiver["expires_on"] = AS_OF.isoformat()
        self.document["waivers"] = [waiver]
        self.check(0)

    def test_nonderogable_rule_cannot_be_bypassed_by_json(self):
        for rule in sorted(validator.RULES - validator.WAIVABLE):
            self.document["waivers"] = [self.waiver(rule)]
            self.check(1, "WAIVER")

    def test_global_scope_only_for_operations_and_no_duplicate_waivers(self):
        self.document["waivers"] = [self.waiver(scope="*")]
        self.check(1, "WAIVER")
        self.document["waivers"] = [self.waiver(), self.waiver()]
        self.check(2, "SCHEMA")
        self.document["waivers"][1]["id"] = "second"
        self.check(1, "WAIVER")

    def test_operations_are_required_only_for_server_roles_when_ready(self):
        self.document["operations"] = {"shutdown_seconds": 10, "health_endpoints": False}
        self.check(1, "OPS-001")
        self.document["status"] = "draft"
        self.check(0)
        self.document["status"] = "ready"
        self.document["waivers"] = [self.waiver("OPS-001", "*")]
        self.check(0)
        self.document["waivers"] = []
        self.document["components"] = self.document["components"][:1]
        self.check(0)

    def test_component_operations_waiver_does_not_cover_another_server(self):
        self.document["operations"]["health_endpoints"] = False
        self.document["waivers"] = [self.waiver("OPS-001")]
        self.check(0)
        worker = copy.deepcopy(self.document["components"][1])
        worker.update(id="jobs", role="worker")
        self.document["components"].append(worker)
        self.check(1, "OPS-001")

    def test_lexical_paths_cannot_escape_without_repo_flag(self):
        for path in ("../outside", "backend/../../outside", "/etc", "C:\\outside", "C:outside", "a\\b", "bad\x00path"):
            document = copy.deepcopy(self.document)
            document["components"][0]["source_root"] = path
            self.check(2, "SCHEMA", document)
        self.document["components"][1]["layers"]["transport"] = ["../outside"]
        self.check(2, "SCHEMA")

    def test_repo_paths_exist_without_application_execution_or_external_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            for component in self.document["components"]:
                (root / component["source_root"]).mkdir(parents=True, exist_ok=True)
                for paths in component["layers"].values():
                    for relative in paths:
                        (root / relative).mkdir(parents=True, exist_ok=True)
            marker = root / "executed"
            (root / "backend" / "__init__.py").write_text(
                "from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n", encoding="utf-8")
            self.check(0, repo=root)
            self.assertFalse(marker.exists())
            missing = copy.deepcopy(self.document)
            missing["components"][1]["layers"]["transport"] = ["backend/does-not-exist"]
            self.check(2, "PATH", missing, root)
            outside = Path(directory) / "outside"
            outside.mkdir()
            (root / "escape").symlink_to(outside, target_is_directory=True)
            escaped = copy.deepcopy(self.document)
            escaped["components"][0]["source_root"] = "escape"
            self.check(2, "PATH", escaped, root)
            escaped = copy.deepcopy(self.document)
            escaped["components"][1]["layers"]["transport"] = ["escape"]
            self.check(2, "PATH", escaped, root)
            (root / "inside-link").symlink_to(root / "backend", target_is_directory=True)
            safe = copy.deepcopy(self.document)
            safe["components"][1]["source_root"] = "inside-link"
            self.check(0, document=safe, repo=root)

    def run_cli(self, content, *args):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "architecture.json"
            path.write_text(content, encoding="utf-8")
            return subprocess.run([sys.executable, "-B", str(SCRIPT), str(path), *args],
                                  capture_output=True, text=True, check=False)

    def test_cli_exit_status_and_explicit_date_are_reproducible(self):
        result = self.run_cli(json.dumps(self.document), "--as-of", "2026-10-14")
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertIn("2026-10-14 (explicit --as-of)", result.stdout)
        self.document["requirements"]["unknowns"] = [{"question": "Volume?", "blocking": True}]
        result = self.run_cli(json.dumps(self.document), "--as-of", "2026-10-14")
        self.assertEqual(1, result.returncode)
        self.assertNotIn("v1 checks: OK", result.stdout)

    def test_cli_malformed_json_duplicates_and_constants_are_not_success(self):
        for content in ('{', '{"schema_version":1,"schema_version":1}', '{"x":NaN}', '[]', 'null'):
            result = self.run_cli(content, "--as-of", "2026-10-14")
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("v1 checks: OK", result.stdout)

    def test_cli_missing_date_announces_system_clock_invalid_date_is_usage_error(self):
        result = self.run_cli(json.dumps(self.document))
        self.assertEqual(0, result.returncode)
        self.assertIn("local system clock", result.stdout)
        result = self.run_cli(json.dumps(self.document), "--as-of", "2026-2-01")
        self.assertEqual(2, result.returncode)

    def test_repo_flag_cannot_confirm_hypothetical_example_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(json.dumps(self.document), "--as-of", "2026-10-14", "--repo", directory)
        self.assertEqual(2, result.returncode)
        self.assertIn("[PATH]", result.stdout)
        self.assertNotIn("v1 checks: OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
