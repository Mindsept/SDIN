#!/usr/bin/env python3
"""Validate an architecture v1 declaration, without executing application code.

Standard library only. Exit codes: 0 = declarative checks pass, 1 = policy
violations, 2 = invalid input/schema/path. This is not an architecture audit.
"""

import argparse
import datetime as dt
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys


SERVICES = frozenset({
    "postgres", "valkey", "s3", "openbao", "apisix", "temporal",
    "temporal-ui", "casdoor", "umami", "registry", "dozzle",
})
ROLES = frozenset({"frontend", "api", "worker", "cli", "native", "upstream"})
STYLES = frozenset({
    "static", "modular-monolith", "worker-pipeline", "durable-workflow",
    "microservices", "native-client", "cli",
})
RULES = frozenset({
    "PLAT-001", "PLAT-002", "DATA-001", "DATA-002", "ARCH-001",
    "STACK-001", "OPS-001", "READY-001",
})
WAIVABLE = frozenset({"ARCH-001", "STACK-001", "OPS-001"})
PRIVATE_SERVICES = frozenset({
    "postgres", "valkey", "openbao", "apisix", "temporal", "umami",
})
LAYERS = {"transport", "application", "domain", "persistence"}
PORT_OFFSETS = {"frontend": 0, "api": 1, "worker": 8}
TS_LANGUAGES = {"typescript", "javascript", "ts", "js"}


class InvalidJSON(ValueError):
    """Ambiguous or non-standard JSON input."""


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidJSON("Duplicate JSON key: " + repr(key))
        result[key] = value
    return result


def reject_constant(value):
    raise InvalidJSON("Non-standard JSON constant: " + value)


def iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date expected in YYYY-MM-DD format")
    return dt.date.fromisoformat(value)


def argument_date(value):
    try:
        return iso_date(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def issue(level, rule, path, message):
    return {"level": level, "rule": rule, "path": path, "message": message}


class Schema:
    def __init__(self):
        self.errors = []
        self.paths = []

    def error(self, path, message):
        self.errors.append(issue("ERROR", "SCHEMA", path, message))

    def obj(self, value, keys, path):
        if type(value) is not dict:
            self.error(path, "JSON object expected")
            return False
        missing = sorted(set(keys) - set(value))
        extra = sorted(set(value) - set(keys))
        if missing:
            self.error(path, "missing required fields: " + ", ".join(missing))
        if extra:
            self.error(path, "unknown fields: " + ", ".join(extra))
        return not missing

    def string(self, value, path, allow_empty=False):
        if type(value) is not str:
            self.error(path, "string expected")
            return False
        if not allow_empty and not value.strip():
            self.error(path, "non-empty string expected")
            return False
        return True

    def enum(self, value, choices, path):
        if self.string(value, path) and value not in choices:
            self.error(path, "expected one of: " + ", ".join(sorted(choices)))

    def boolean(self, value, path):
        if type(value) is not bool:
            self.error(path, "JSON boolean expected")

    def integer(self, value, path, nullable=False):
        if nullable and value is None:
            return
        if type(value) is not int:
            self.error(path, "JSON integer expected" + (" or null" if nullable else ""))

    def array(self, value, path, visitor):
        if type(value) is not list:
            self.error(path, "JSON list expected")
            return False
        for index, item in enumerate(value):
            visitor(item, f"{path}[{index}]")
        return True

    def strings(self, value, path, nonempty=False):
        if self.array(value, path, self.string) and nonempty and not value:
            self.error(path, "at least one non-empty string expected")

    def service_list(self, value, path):
        def check(item, location):
            self.enum(item, SERVICES, location)
        if self.array(value, path, check):
            self.unique(value, path)

    def unique(self, values, path):
        seen = set()
        for value in values:
            if type(value) is not str:
                continue
            if value in seen:
                self.error(path, "duplicate identifier: " + value)
            seen.add(value)

    def relative_path(self, value, path, source_root=False):
        if not self.string(value, path):
            return
        if ("\x00" in value or "\\" in value or PurePosixPath(value).is_absolute()
                or PureWindowsPath(value).drive or ".." in value.split("/")):
            self.error(path, "portable relative path required, without '..', drive or backslash")
            return
        self.paths.append((path, value, source_root))

    def date(self, value, path):
        try:
            iso_date(value)
        except (ValueError, TypeError):
            self.error(path, "valid calendar date expected in YYYY-MM-DD format")

    def unknown(self, value, path):
        if self.obj(value, {"question", "blocking"}, path):
            self.string(value["question"], path + ".question")
            self.boolean(value["blocking"], path + ".blocking")

    def alternative(self, value, path):
        if self.obj(value, {"option", "rejection_reason"}, path):
            self.string(value["option"], path + ".option")
            self.string(value["rejection_reason"], path + ".rejection_reason", allow_empty=True)

    def component(self, value, path):
        keys = {"id", "role", "language", "framework", "runtime", "source_root",
                "layers", "rationale", "framework_rationale", "data_access", "platform_services"}
        if not self.obj(value, keys, path):
            return
        for field in ("id", "language", "framework", "runtime"):
            self.string(value[field], path + "." + field)
        for field in ("rationale", "framework_rationale"):
            self.string(value[field], path + "." + field, allow_empty=True)
        self.enum(value["role"], ROLES, path + ".role")
        self.enum(value["data_access"], {"none", "orm", "query-builder", "sql"}, path + ".data_access")
        self.relative_path(value["source_root"], path + ".source_root", source_root=True)
        self.service_list(value["platform_services"], path + ".platform_services")
        if self.obj(value["layers"], LAYERS, path + ".layers"):
            for layer in sorted(LAYERS):
                self.array(value["layers"][layer], path + ".layers." + layer, self.relative_path)

    def waiver(self, value, path):
        keys = {"id", "rule_id", "scope", "reason", "alternatives", "compute_impact",
                "evidence", "approved_by", "approved_on", "expires_on", "rollback"}
        if not self.obj(value, keys, path):
            return
        for field in ("id", "scope", "reason", "compute_impact", "approved_by", "rollback"):
            self.string(value[field], path + "." + field)
        self.enum(value["rule_id"], RULES, path + ".rule_id")
        self.strings(value["alternatives"], path + ".alternatives", nonempty=True)
        self.strings(value["evidence"], path + ".evidence", nonempty=True)
        for field in ("approved_on", "expires_on"):
            self.date(value[field], path + "." + field)

    def validate(self, document):
        keys = {"schema_version", "status", "project", "requirements", "architecture",
                "components", "platform", "operations", "waivers"}
        if not self.obj(document, keys, "$"):
            return
        self.integer(document["schema_version"], "$.schema_version")
        if type(document["schema_version"]) is int and document["schema_version"] != 1:
            self.error("$.schema_version", "only version 1 is supported")
        self.enum(document["status"], {"draft", "ready"}, "$.status")
        project = document["project"]
        if self.obj(project, {"name", "kind", "context", "policy"}, "$.project"):
            for field in ("name", "kind"):
                self.string(project[field], "$.project." + field)
            self.enum(project["context"], {"workshop", "production", "unknown"}, "$.project.context")
            self.enum(project["policy"], {"platform-compatible", "strict-typescript"}, "$.project.policy")
        requirements = document["requirements"]
        if self.obj(requirements, {"summary", "drivers", "constraints", "unknowns", "assumptions"}, "$.requirements"):
            self.string(requirements["summary"], "$.requirements.summary", allow_empty=True)
            for field in ("drivers", "constraints", "assumptions"):
                self.strings(requirements[field], "$.requirements." + field)
            self.array(requirements["unknowns"], "$.requirements.unknowns", self.unknown)
        architecture = document["architecture"]
        if self.obj(architecture, {"style", "rationale", "compute_tradeoff", "alternatives"}, "$.architecture"):
            self.enum(architecture["style"], STYLES, "$.architecture.style")
            for field in ("rationale", "compute_tradeoff"):
                self.string(architecture[field], "$.architecture." + field, allow_empty=True)
            self.array(architecture["alternatives"], "$.architecture.alternatives", self.alternative)
        self.array(document["components"], "$.components", self.component)
        platform = document["platform"]
        if self.obj(platform, {"services", "app_port_base", "vector_enabled"}, "$.platform"):
            self.service_list(platform["services"], "$.platform.services")
            self.integer(platform["app_port_base"], "$.platform.app_port_base", nullable=True)
            self.boolean(platform["vector_enabled"], "$.platform.vector_enabled")
        operations = document["operations"]
        if self.obj(operations, {"shutdown_seconds", "health_endpoints"}, "$.operations"):
            self.integer(operations["shutdown_seconds"], "$.operations.shutdown_seconds", nullable=True)
            self.boolean(operations["health_endpoints"], "$.operations.health_endpoints")
            seconds = operations["shutdown_seconds"]
            if type(seconds) is int and seconds < 0:
                self.error("$.operations.shutdown_seconds", "negative duration is not allowed")
        self.array(document["waivers"], "$.waivers", self.waiver)
        if self.errors:
            return
        ids = [c["id"] for c in document["components"]]
        self.unique(ids, "$.components")
        if "*" in ids:
            self.error("$.components", "'*' is reserved for the global OPS-001 scope")
        self.unique([w["id"] for w in document["waivers"]], "$.waivers")
        services = set(platform["services"])
        for index, component in enumerate(document["components"]):
            unselected = set(component["platform_services"]) - services
            if unselected:
                self.error(f"$.components[{index}].platform_services",
                           "services missing from platform.services: " + ", ".join(sorted(unselected)))
        for index, waiver in enumerate(document["waivers"]):
            if waiver["scope"] != "*" and waiver["scope"] not in ids:
                self.error(f"$.waivers[{index}].scope", "nonexistent component: " + waiver["scope"])


def validate_paths(paths, repo):
    errors = []
    try:
        root = Path(repo).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("--repo must point to a directory")
    except (OSError, RuntimeError, ValueError) as exc:
        return [issue("ERROR", "PATH", "--repo", str(exc))]
    for location, relative, is_root in paths:
        try:
            candidate = (root / relative).resolve(strict=True)
            candidate.relative_to(root)
            if is_root and not candidate.is_dir():
                raise ValueError("source_root must point to a directory")
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(issue("ERROR", "PATH", location,
                                f"path missing, outside the repository or of the wrong type ({relative}): {exc}"))
    return errors


def validate(document, as_of, repo=None):
    """Return (exit_code, diagnostics) for decoded JSON and an explicit date."""
    schema = Schema()
    schema.validate(document)
    if schema.errors:
        return 2, schema.errors
    if repo is not None:
        path_errors = validate_paths(schema.paths, repo)
        if path_errors:
            return 2, path_errors
    diagnostics = []
    active_waivers = {}
    used_waivers = set()
    seen_scopes = set()
    for index, waiver in enumerate(document["waivers"]):
        location = f"$.waivers[{index}]"
        errors = []
        rule, scope = waiver["rule_id"], waiver["scope"]
        approved, expires = iso_date(waiver["approved_on"]), iso_date(waiver["expires_on"])
        if rule not in WAIVABLE:
            errors.append(f"{rule} cannot be waived in this contract")
        if scope == "*" and rule != "OPS-001":
            errors.append("scope '*' is reserved for OPS-001")
        if approved > as_of:
            errors.append("approval date is in the future relative to --as-of")
        if expires < approved:
            errors.append("expiration precedes approval")
        if expires < as_of:
            errors.append("waiver has expired as of the validation date")
        if (rule, scope) in seen_scopes:
            errors.append("duplicate waiver for the same rule and scope")
        seen_scopes.add((rule, scope))
        if errors:
            for message in errors:
                diagnostics.append(issue("ERROR", "WAIVER", location, message))
        else:
            active_waivers[(rule, scope)] = waiver

    def report(rule, path, message, component_id=None, level="ERROR"):
        waiver = active_waivers.get((rule, component_id))
        if waiver is None and rule == "OPS-001":
            waiver = active_waivers.get((rule, "*"))
        if waiver is not None and rule in WAIVABLE:
            used_waivers.add(waiver["id"])
            diagnostics.append(issue("WAIVED", rule, path,
                f"{message} — declared waiver {waiver['id']}, valid through {waiver['expires_on']}"))
        else:
            diagnostics.append(issue(level, rule, path, message))

    ready = document["status"] == "ready"
    completeness_level = "ERROR" if ready else "WARNING"
    if document["project"]["context"] == "unknown":
        report("READY-001", "$.project.context",
               "deployment context must be clarified before a ready decision",
               level=completeness_level)
    justification_fields = [
        ("$.requirements.summary", document["requirements"]["summary"]),
        ("$.architecture.rationale", document["architecture"]["rationale"]),
        ("$.architecture.compute_tradeoff", document["architecture"]["compute_tradeoff"]),
    ]
    for index, alternative in enumerate(document["architecture"]["alternatives"]):
        justification_fields.append((f"$.architecture.alternatives[{index}].rejection_reason", alternative["rejection_reason"]))
    for index, component in enumerate(document["components"]):
        for field in ("rationale", "framework_rationale"):
            justification_fields.append((f"$.components[{index}].{field}", component[field]))
    for location, value in justification_fields:
        if not value.strip():
            report("READY-001", location, "rationale or summary must be completed", level=completeness_level)
    for field, values in (("$.architecture.alternatives", document["architecture"]["alternatives"]),
                          ("$.components", document["components"])):
        if not values:
            report("READY-001", field, "at least one entry is required for a ready decision", level=completeness_level)
    if not document["requirements"]["drivers"]:
        report("READY-001", "$.requirements.drivers", "no decision criteria provided", level="WARNING")
    for index, unknown in enumerate(document["requirements"]["unknowns"]):
        level = "ERROR" if ready and unknown["blocking"] else "WARNING"
        report("READY-001", f"$.requirements.unknowns[{index}]",
               ("blocking question: " if unknown["blocking"] else "open question: ") + unknown["question"], level=level)
    if not ready:
        diagnostics.append(issue("WARNING", "READY-001", "$.status", "draft: the decision still needs to be completed and reviewed"))

    platform = document["platform"]
    if platform["vector_enabled"] and "postgres" not in platform["services"]:
        report("DATA-001", "$.platform.vector_enabled", "vector_enabled requires postgres in platform.services")
    base = platform["app_port_base"]
    if base is not None:
        if not (8000 <= base <= 8990 and base % 10 == 0 and base != 8200):
            report("PLAT-002", "$.platform.app_port_base", "block of 10: base must be a multiple of 10 between 8000 and 8990, excluding 8200")
        ports = {}
        for component in document["components"]:
            if component["role"] in PORT_OFFSETS:
                port = base + PORT_OFFSETS[component["role"]]
                if port in ports:
                    report("PLAT-002", "$.platform.app_port_base",
                           f"declared collision on port {port} between {ports[port]} and {component['id']}; v1 does not encode custom ports")
                ports[port] = component["id"]

    for index, component in enumerate(document["components"]):
        location, cid = f"$.components[{index}]", component["id"]
        consumes = set(component["platform_services"])
        if component["role"] in {"frontend", "native"}:
            forbidden = consumes & PRIVATE_SERVICES
            if forbidden:
                report("PLAT-001", location + ".platform_services",
                       "direct client access is prohibited: " + ", ".join(sorted(forbidden)), cid)
        if component["data_access"] != "none" and "postgres" not in consumes:
            report("DATA-002", location + ".data_access",
                   "data access requires postgres to be consumed by this component; another DB requires an explicit contract extension", cid)
        if component["role"] == "api":
            required_layers = {"transport", "application"}
            if "postgres" in consumes:
                required_layers.add("persistence")
            for layer in sorted(required_layers):
                if not component["layers"][layer]:
                    report("ARCH-001", location + ".layers." + layer,
                           "API: declare the paths for this responsibility", cid, completeness_level)
        if (document["project"]["policy"] == "strict-typescript"
                and component["role"] in {"api", "worker", "frontend"}
                and component["language"].strip().casefold() not in TS_LANGUAGES):
            report("STACK-001", location + ".language",
                   "strict-typescript requires TypeScript/JavaScript for this role", cid)
        if component["role"] in {"api", "worker", "upstream"}:
            seconds = document["operations"]["shutdown_seconds"]
            if seconds is None or seconds >= 10:
                report("OPS-001", "$.operations.shutdown_seconds",
                       f"{cid}: declared shutdown must be strictly less than 10 seconds", cid, completeness_level)
            if not document["operations"]["health_endpoints"]:
                report("OPS-001", "$.operations.health_endpoints",
                       f"{cid}: declare the /health and /ready health endpoints", cid, completeness_level)

    for waiver in active_waivers.values():
        if waiver["id"] not in used_waivers:
            diagnostics.append(issue("WARNING", "WAIVER", "$.waivers",
                                     "waiver without a corresponding violation: " + waiver["id"]))
    code = 1 if any(item["level"] == "ERROR" for item in diagnostics) else 0
    return code, diagnostics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path, help="v1 architecture JSON declaration")
    parser.add_argument("--as-of", type=argument_date, help="explicit validation date YYYY-MM-DD (recommended)")
    parser.add_argument("--repo", type=Path, help="check declared paths within this repository without executing its code")
    args = parser.parse_args(argv)
    as_of = args.as_of or dt.date.today()
    origin = "explicit --as-of" if args.as_of else "local system clock; --as-of recommended"
    print(f"Validation date: {as_of.isoformat()} ({origin})")
    try:
        with args.json_path.open(encoding="utf-8") as handle:
            document = json.load(handle, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(f"ERROR [SCHEMA] {args.json_path}: {exc}", file=sys.stderr)
        return 2
    code, diagnostics = validate(document, as_of, args.repo)
    for item in diagnostics:
        print(f"{item['level']} [{item['rule']}] {item['path']}: {item['message']}")
    if code == 0:
        print("Declarative compliance with v1 checks: OK" + (" (draft; see warnings)." if document["status"] == "draft" else "."))
    else:
        print("Declarative compliance: FAIL (" + ("invalid input or schema" if code == 2 else "violations") + ").")
    print("No application code executed. Actual responsibilities, permissions, approvals and behavior still require human verification.")
    if args.repo is None:
        print("Paths: syntax checked only; existence not verified without --repo.")
    return code


if __name__ == "__main__":
    sys.exit(main())
