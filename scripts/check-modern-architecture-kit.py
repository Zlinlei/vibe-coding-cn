#!/usr/bin/env python3
"""Validate the modern enterprise architecture starter kit.

The repository intentionally avoids extra Python dependencies for quality
gates. This checker implements the small YAML and JSON Schema subset used by
the starter kit, then validates each example against its paired schema.
"""

from __future__ import annotations

import json
import importlib.util
import re
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KIT_DIR = ROOT / "docs/references/modern-enterprise-architecture-kit"
VERSION_MANIFEST_PATH = ROOT / "docs/references/modern-enterprise-architecture-version.json"
CONTROL_CATALOG_PATH = ROOT / "docs/references/modern-enterprise-architecture-controls.json"
AUDIT_EXPORT_SCRIPT_PATH = ROOT / "scripts/export-modern-architecture-audit.py"
AUDIT_EXPORT_GATE_SCRIPT_PATH = ROOT / "scripts/check-modern-architecture-audit-export.py"
PAIR_NAMES = [
    "domain",
    "service",
    "api-contract",
    "event-contract",
    "data-product",
    "ai-product",
    "ai-tool-contract",
    "rag-index-contract",
    "fine-tuning-contract",
    "catalog-component",
    "catalog-data-product",
    "catalog-ai-product",
    "gitops-deployment",
    "release-evidence",
    "supply-chain-attestation",
    "policy-exception",
    "api-compatibility-report",
    "event-compatibility-report",
    "gitops-drift-report",
    "production-readiness",
    "raci",
    "tiering-policy",
    "deprecation-policy",
    "audit-evidence-index",
    "scorecard",
    "extension-policy",
    "feature-flag-control",
    "ai-threat-model",
    "lineage-event",
    "platform-product-metrics",
    "privacy-impact-assessment",
    "tenant-boundary",
    "recovery-drill-evidence",
    "policy-test-report",
    "genai-observability-contract",
    "cost-allocation-evidence",
    "identity-access-review",
    "secrets-rotation-evidence",
    "vulnerability-remediation-evidence",
    "incident-postmortem",
    "evidence-freshness-policy",
    "control-evidence-map",
    "audit-export-manifest",
    "control-assessment-report",
    "baseline-change-record",
    "oscal-export-profile",
    "audit-export-gate",
    "audit-export-integrity",
    "audit-export-provenance",
    "audit-export-signing-policy",
    "audit-export-signature-receipt",
]
SCHEMA_TYPES = {"object", "array", "string", "number", "integer", "boolean", "null"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")
JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"


class KitValidationError(ValueError):
    """Raised when a starter kit example cannot be parsed or validated."""


def load_version_manifest() -> dict[str, Any]:
    with VERSION_MANIFEST_PATH.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest, dict):
        raise ValueError("manifest root must be an object")
    return manifest


def load_control_catalog() -> dict[str, Any]:
    with CONTROL_CATALOG_PATH.open(encoding="utf-8") as handle:
        catalog = json.load(handle)
    if not isinstance(catalog, dict):
        raise ValueError("control catalog root must be an object")
    return catalog


def load_schema(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    if not isinstance(schema, dict):
        raise ValueError("schema root must be an object")
    return schema


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False

    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()
    return value


def parse_scalar(value: str) -> Any:
    value = strip_inline_comment(value.strip())
    if value == "":
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]

    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    try:
        if "." in value and not any(char.isspace() for char in value):
            return float(value)
    except ValueError:
        return value
    return value


def prepared_yaml_lines(path: Path) -> list[tuple[int, str, int]]:
    prepared: list[tuple[int, str, int]] = []

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if "\t" in raw_line:
            raise KitValidationError(f"{path.relative_to(ROOT)}:{lineno}: tabs are not allowed")
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        prepared.append((indent, raw_line.strip(), lineno))

    return prepared


def split_key_value(content: str, path: Path, lineno: int) -> tuple[str, str]:
    if ":" not in content:
        raise KitValidationError(f"{path.relative_to(ROOT)}:{lineno}: expected key/value pair")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise KitValidationError(f"{path.relative_to(ROOT)}:{lineno}: empty key")
    return key, value.strip()


def parse_yaml_example(path: Path) -> Any:
    lines = prepared_yaml_lines(path)
    if not lines:
        raise KitValidationError(f"{path.relative_to(ROOT)}: empty YAML example")

    document, next_index = parse_yaml_block(path, lines, 0, lines[0][0])
    if next_index != len(lines):
        _, _, lineno = lines[next_index]
        raise KitValidationError(f"{path.relative_to(ROOT)}:{lineno}: unexpected trailing YAML content")
    return document


def parse_yaml_block(path: Path, lines: list[tuple[int, str, int]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index

    current_indent, content, lineno = lines[index]
    if current_indent != indent:
        raise KitValidationError(
            f"{path.relative_to(ROOT)}:{lineno}: expected indent {indent}, got {current_indent}"
        )

    if content.startswith("- "):
        return parse_yaml_list(path, lines, index, indent)
    return parse_yaml_mapping(path, lines, index, indent)


def parse_yaml_mapping(path: Path, lines: list[tuple[int, str, int]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}

    while index < len(lines):
        current_indent, content, lineno = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise KitValidationError(
                f"{path.relative_to(ROOT)}:{lineno}: unexpected nested mapping without parent key"
            )
        if content.startswith("- "):
            break

        key, raw_value = split_key_value(content, path, lineno)
        if key in result:
            raise KitValidationError(f"{path.relative_to(ROOT)}:{lineno}: duplicate key '{key}'")

        if raw_value == "":
            if index + 1 < len(lines) and lines[index + 1][0] > indent:
                value, index = parse_yaml_block(path, lines, index + 1, lines[index + 1][0])
            else:
                value = None
                index += 1
        else:
            value = parse_scalar(raw_value)
            index += 1

        result[key] = value

    return result, index


def parse_yaml_list(path: Path, lines: list[tuple[int, str, int]], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []

    while index < len(lines):
        current_indent, content, lineno = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise KitValidationError(
                f"{path.relative_to(ROOT)}:{lineno}: unexpected nested list content"
            )
        if not content.startswith("- "):
            break

        item_text = content[2:].strip()
        if item_text == "":
            if index + 1 < len(lines) and lines[index + 1][0] > indent:
                value, index = parse_yaml_block(path, lines, index + 1, lines[index + 1][0])
            else:
                value = None
                index += 1
            result.append(value)
            continue

        if ":" in item_text:
            key, raw_value = split_key_value(item_text, path, lineno)
            item: dict[str, Any] = {}
            if raw_value == "":
                if index + 1 < len(lines) and lines[index + 1][0] > indent:
                    value, index = parse_yaml_block(path, lines, index + 1, lines[index + 1][0])
                else:
                    value = None
                    index += 1
            else:
                value = parse_scalar(raw_value)
                index += 1
            item[key] = value

            if index < len(lines) and lines[index][0] > indent:
                child, index = parse_yaml_block(path, lines, index, lines[index][0])
                if not isinstance(child, dict):
                    raise KitValidationError(
                        f"{path.relative_to(ROOT)}:{lineno}: list item continuation must be a mapping"
                    )
                overlap = set(item) & set(child)
                if overlap:
                    duplicate = sorted(overlap)[0]
                    raise KitValidationError(
                        f"{path.relative_to(ROOT)}:{lineno}: duplicate list item key '{duplicate}'"
                    )
                item.update(child)
            result.append(item)
            continue

        result.append(parse_scalar(item_text))
        index += 1

    return result, index


def matches_schema_type(expected: str, value: Any) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def validate_schema_document(schema: dict[str, Any], schema_path: Path) -> list[str]:
    rel = str(schema_path.relative_to(ROOT))
    errors: list[str] = []
    if schema.get("$schema") != JSON_SCHEMA_DRAFT:
        errors.append(f"{rel}: $schema must be {JSON_SCHEMA_DRAFT}")
    if schema.get("type") != "object":
        errors.append(f"{rel}: root type must be object")
    errors.extend(validate_schema_fragment(schema, rel))
    return errors


def validate_schema_fragment(schema: dict[str, Any], location: str) -> list[str]:
    errors: list[str] = []

    schema_type = schema.get("type")
    if schema_type not in SCHEMA_TYPES:
        errors.append(f"{location}: unsupported type '{schema_type}'")

    required = schema.get("required")
    if required is not None and (
        not isinstance(required, list) or not all(isinstance(item, str) for item in required)
    ):
        errors.append(f"{location}: required must be a string array")

    properties = schema.get("properties", {})
    if properties is not None and not isinstance(properties, dict):
        errors.append(f"{location}: properties must be an object")
        properties = {}
    additional_properties = schema.get("additionalProperties")
    if schema_type == "object" and additional_properties is not False:
        errors.append(f"{location}: additionalProperties must be false for strict starter kit schemas")

    if isinstance(required, list):
        missing_properties = sorted(set(required) - set(properties))
        if missing_properties:
            errors.append(f"{location}: required fields missing from properties: {', '.join(missing_properties)}")

    for prop_name, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            errors.append(f"{location}: property '{prop_name}' schema must be an object")
            continue
        errors.extend(validate_schema_fragment(prop_schema, f"{location}.properties.{prop_name}"))

    item_schema = schema.get("items")
    if item_schema is not None:
        if not isinstance(item_schema, dict):
            errors.append(f"{location}: items must be an object")
        else:
            errors.extend(validate_schema_fragment(item_schema, f"{location}.items"))

    pattern = schema.get("pattern")
    if pattern is not None:
        if not isinstance(pattern, str):
            errors.append(f"{location}: pattern must be a string")
        else:
            try:
                re.compile(pattern)
            except re.error as exc:
                errors.append(f"{location}: invalid pattern: {exc}")

    schema_format = schema.get("format")
    if schema_format is not None and schema_format not in {"date", "date-time"}:
        errors.append(f"{location}: unsupported format '{schema_format}'")

    for numeric_key in ("minLength", "minItems"):
        if numeric_key in schema and (
            not isinstance(schema[numeric_key], int) or isinstance(schema[numeric_key], bool) or schema[numeric_key] < 0
        ):
            errors.append(f"{location}: {numeric_key} must be a non-negative integer")

    for numeric_key in ("minimum", "maximum"):
        if numeric_key in schema and (
            not isinstance(schema[numeric_key], (int, float)) or isinstance(schema[numeric_key], bool)
        ):
            errors.append(f"{location}: {numeric_key} must be a number")

    return errors


def is_iso_date(value: str) -> bool:
    if not DATE_PATTERN.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_iso_datetime(value: str) -> bool:
    if not DATETIME_PATTERN.match(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def validate_version_manifest() -> list[str]:
    errors: list[str] = []
    rel = str(VERSION_MANIFEST_PATH.relative_to(ROOT))

    if not VERSION_MANIFEST_PATH.is_file():
        return [f"{rel}: missing version manifest"]

    try:
        manifest = load_version_manifest()
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"{rel}: invalid JSON manifest: {exc}"]

    required_fields = [
        "currentVersion",
        "releaseDate",
        "status",
        "changeLevel",
        "summary",
        "architectureDocument",
        "starterKit",
        "controlCatalog",
        "requiredMentions",
    ]
    for field in required_fields:
        if field not in manifest:
            errors.append(f"{rel}: missing required field '{field}'")

    current_version = manifest.get("currentVersion")
    if not isinstance(current_version, str) or not re.fullmatch(r"V[0-9]+\.[0-9]+", current_version):
        errors.append(f"{rel}: currentVersion must match Vx.y")

    release_date = manifest.get("releaseDate")
    if not isinstance(release_date, str) or not is_iso_date(release_date):
        errors.append(f"{rel}: releaseDate must be a YYYY-MM-DD date")

    starter_kit = manifest.get("starterKit")
    if not isinstance(starter_kit, dict):
        errors.append(f"{rel}: starterKit must be an object")
        starter_kit = {}

    kit_path = starter_kit.get("path")
    if kit_path != str(KIT_DIR.relative_to(ROOT)):
        errors.append(f"{rel}: starterKit.path must be {KIT_DIR.relative_to(ROOT)}")

    expected_pair_count = starter_kit.get("expectedPairCount")
    if expected_pair_count != len(PAIR_NAMES):
        errors.append(f"{rel}: starterKit.expectedPairCount must be {len(PAIR_NAMES)}")

    manifest_pairs = starter_kit.get("pairs")
    if not isinstance(manifest_pairs, list) or not all(isinstance(item, str) for item in manifest_pairs):
        errors.append(f"{rel}: starterKit.pairs must be a string array")
        manifest_pairs = []
    if manifest_pairs != PAIR_NAMES:
        errors.append(f"{rel}: starterKit.pairs must match checker PAIR_NAMES order")
    if len(manifest_pairs) != expected_pair_count:
        errors.append(f"{rel}: starterKit.pairs length must match expectedPairCount")

    control_catalog = manifest.get("controlCatalog")
    expected_control_count = None
    if not isinstance(control_catalog, dict):
        errors.append(f"{rel}: controlCatalog must be an object")
    else:
        control_catalog_path = control_catalog.get("path")
        if control_catalog_path != str(CONTROL_CATALOG_PATH.relative_to(ROOT)):
            errors.append(f"{rel}: controlCatalog.path must be {CONTROL_CATALOG_PATH.relative_to(ROOT)}")
        expected_control_count = control_catalog.get("expectedControlCount")
        if not isinstance(expected_control_count, int) or isinstance(expected_control_count, bool) or expected_control_count < 1:
            errors.append(f"{rel}: controlCatalog.expectedControlCount must be a positive integer")

    mentions = manifest.get("requiredMentions")
    if not isinstance(mentions, list):
        errors.append(f"{rel}: requiredMentions must be an array")
        mentions = []

    architecture_document = manifest.get("architectureDocument")
    if isinstance(architecture_document, str):
        architecture_path = ROOT / architecture_document
        if not architecture_path.is_file():
            errors.append(f"{architecture_document}: architecture document is missing")
        elif isinstance(current_version, str):
            architecture_content = architecture_path.read_text(encoding="utf-8")
            status = manifest.get("status")
            change_level = manifest.get("changeLevel")
            release_date_value = manifest.get("releaseDate")
            generated_checks = [
                f"**文档版本**：{current_version}",
                f"| `{current_version}` | `{status}` |",
                f"| `{current_version}` | {release_date_value} | {change_level} |",
                f"### 0.7 {current_version} 可执行企业标准路线图",
            ]
            for expected_text in generated_checks:
                if expected_text not in architecture_content:
                    errors.append(f"{architecture_document}: missing generated version text '{expected_text}'")
    else:
        errors.append(f"{rel}: architectureDocument must be a string")

    for index, mention in enumerate(mentions):
        if not isinstance(mention, dict):
            errors.append(f"{rel}: requiredMentions[{index}] must be an object")
            continue
        path_value = mention.get("path")
        contains = mention.get("contains")
        if not isinstance(path_value, str):
            errors.append(f"{rel}: requiredMentions[{index}].path must be a string")
            continue
        if not isinstance(contains, list) or not all(isinstance(item, str) for item in contains):
            errors.append(f"{rel}: requiredMentions[{index}].contains must be a string array")
            continue
        target_path = ROOT / path_value
        if not target_path.is_file():
            errors.append(f"{path_value}: version mention target is missing")
            continue
        content = target_path.read_text(encoding="utf-8")
        for expected_text in contains:
            if expected_text not in content:
                errors.append(f"{path_value}: missing version manifest text '{expected_text}'")

    if isinstance(current_version, str):
        errors.extend(validate_control_catalog(current_version, expected_control_count))

    return errors


def get_dotted_value(value: Any, dotted_path: str) -> Any:
    current = value
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def validate_control_catalog(expected_version: str, expected_control_count: Any) -> list[str]:
    errors: list[str] = []
    rel = str(CONTROL_CATALOG_PATH.relative_to(ROOT))

    if not CONTROL_CATALOG_PATH.is_file():
        return [f"{rel}: missing control catalog"]

    try:
        catalog = load_control_catalog()
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"{rel}: invalid JSON control catalog: {exc}"]

    if catalog.get("version") != expected_version:
        errors.append(f"{rel}: version must match version manifest currentVersion {expected_version}")
    if not is_iso_date(catalog.get("releaseDate", "")):
        errors.append(f"{rel}: releaseDate must be a YYYY-MM-DD date")

    controls = catalog.get("controls")
    if not isinstance(controls, list) or not controls:
        return errors + [f"{rel}: controls must be a non-empty array"]
    if isinstance(expected_control_count, int) and len(controls) != expected_control_count:
        errors.append(f"{rel}: controls length must match controlCatalog.expectedControlCount")

    seen_ids: set[str] = set()
    checker_text = Path(__file__).read_text(encoding="utf-8")
    required_control_fields = [
        "id",
        "category",
        "title",
        "statement",
        "requiredArtifacts",
        "schemaRequirements",
        "exampleRequirements",
        "checkerEvidence",
    ]

    for index, control in enumerate(controls):
        location = f"{rel}.controls[{index}]"
        if not isinstance(control, dict):
            errors.append(f"{location}: control must be an object")
            continue
        for field in required_control_fields:
            if field not in control:
                errors.append(f"{location}: missing required field '{field}'")

        control_id = control.get("id")
        if not isinstance(control_id, str) or not re.fullmatch(r"CTRL-[A-Z0-9-]+", control_id):
            errors.append(f"{location}: id must match CTRL-*")
        elif control_id in seen_ids:
            errors.append(f"{location}: duplicate control id '{control_id}'")
        else:
            seen_ids.add(control_id)

        artifacts = control.get("requiredArtifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"{location}: requiredArtifacts must be a non-empty string array")
        else:
            for artifact in artifacts:
                if not isinstance(artifact, str):
                    errors.append(f"{location}: requiredArtifacts entries must be strings")
                    continue
                if not (ROOT / artifact).is_file():
                    errors.append(f"{location}: required artifact is missing: {artifact}")

        schema_requirements = control.get("schemaRequirements")
        if not isinstance(schema_requirements, list):
            errors.append(f"{location}: schemaRequirements must be an array")
        else:
            for req_index, requirement in enumerate(schema_requirements):
                req_location = f"{location}.schemaRequirements[{req_index}]"
                errors.extend(validate_control_schema_requirement(requirement, req_location))

        example_requirements = control.get("exampleRequirements")
        if not isinstance(example_requirements, list):
            errors.append(f"{location}: exampleRequirements must be an array")
        else:
            for req_index, requirement in enumerate(example_requirements):
                req_location = f"{location}.exampleRequirements[{req_index}]"
                errors.extend(validate_control_example_requirement(requirement, req_location))

        checker_evidence = control.get("checkerEvidence")
        if not isinstance(checker_evidence, list) or not checker_evidence:
            errors.append(f"{location}: checkerEvidence must be a non-empty string array")
        else:
            for evidence in checker_evidence:
                if not isinstance(evidence, str):
                    errors.append(f"{location}: checkerEvidence entries must be strings")
                    continue
                if evidence not in checker_text:
                    errors.append(f"{location}: checker evidence is not present in script: {evidence}")

    return errors


def validate_audit_export_automation() -> list[str]:
    errors: list[str] = []
    makefile_path = ROOT / "Makefile"
    scripts_readme_path = ROOT / "scripts/README.md"
    root_agents_path = ROOT / "AGENTS.md"
    makefile_text = makefile_path.read_text(encoding="utf-8") if makefile_path.is_file() else ""
    scripts_readme_text = scripts_readme_path.read_text(encoding="utf-8") if scripts_readme_path.is_file() else ""
    root_agents_text = root_agents_path.read_text(encoding="utf-8") if root_agents_path.is_file() else ""

    if not AUDIT_EXPORT_SCRIPT_PATH.is_file():
        errors.append("audit export script must exist")
    if not makefile_path.is_file() or "export-modern-architecture-audit" not in makefile_text:
        errors.append("Makefile must expose export-modern-architecture-audit")
    if not scripts_readme_path.is_file() or "export-modern-architecture-audit.py" not in scripts_readme_text:
        errors.append("scripts README must mention export-modern-architecture-audit.py")
    if not root_agents_path.is_file() or "export-modern-architecture-audit" not in root_agents_text:
        errors.append("AGENTS.md must mention export-modern-architecture-audit")
    if not AUDIT_EXPORT_GATE_SCRIPT_PATH.is_file():
        errors.append("audit export gate script must exist")
    if "check-modern-architecture-audit-export" not in makefile_text:
        errors.append("Makefile must expose check-modern-architecture-audit-export")
    test_line = re.search(r"^test:\s*(.+)$", makefile_text, re.MULTILINE)
    if test_line is None or "check-modern-architecture-audit-export" not in test_line.group(1):
        errors.append("Makefile test gate must include check-modern-architecture-audit-export")
    if "check-modern-architecture-audit-export.py" not in scripts_readme_text:
        errors.append("scripts README must mention check-modern-architecture-audit-export.py")
    if "check-modern-architecture-audit-export" not in root_agents_text:
        errors.append("AGENTS.md must mention check-modern-architecture-audit-export")

    return errors


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def validate_audit_export_gate_runtime() -> list[str]:
    errors: list[str] = []
    try:
        exporter = load_module(AUDIT_EXPORT_SCRIPT_PATH, "modern_architecture_audit_exporter_runtime")
        gate = load_module(AUDIT_EXPORT_GATE_SCRIPT_PATH, "modern_architecture_audit_export_gate_runtime")
        checker = sys.modules[__name__]
        packet = exporter.build_packet(checker)
        with tempfile.TemporaryDirectory(prefix="modern-architecture-audit-") as temp_dir:
            out_dir = Path(temp_dir)
            json_path = out_dir / "audit-export.json"
            markdown_path = out_dir / "audit-export.md"
            oscal_path = out_dir / "oscal-summary.json"
            integrity_path = out_dir / "audit-export-integrity.json"
            provenance_path = out_dir / "audit-export-provenance.json"
            signing_policy_path = out_dir / "audit-export-signing-policy.json"
            exporter.write_json(packet, json_path)
            exporter.write_markdown(packet, markdown_path)
            exporter.write_oscal_summary(packet, oscal_path)
            exporter.write_integrity_manifest(packet, [json_path, markdown_path, oscal_path], integrity_path)
            exporter.write_provenance_statement(packet, [json_path, markdown_path, oscal_path, integrity_path], provenance_path)
            exporter.write_signing_policy(packet, provenance_path, signing_policy_path)
            errors.extend(
                gate.validate_packet(
                    load_json_object(json_path),
                    load_json_object(oscal_path),
                    checker,
                    load_json_object(integrity_path),
                    [json_path, markdown_path, oscal_path],
                    load_json_object(provenance_path),
                    [json_path, markdown_path, oscal_path, integrity_path],
                    load_json_object(signing_policy_path),
                    provenance_path,
                )
            )
            if not markdown_path.is_file() or markdown_path.stat().st_size == 0:
                errors.append("audit export gate runtime must generate a non-empty Markdown report")
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"audit export gate runtime invariant check failed: {exc}")
    return errors


def validate_control_schema_requirement(requirement: Any, location: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(requirement, dict):
        return [f"{location}: schema requirement must be an object"]

    path_value = requirement.get("path")
    if not isinstance(path_value, str):
        return [f"{location}: path must be a string"]
    schema_path = ROOT / path_value
    if not schema_path.is_file():
        return [f"{location}: schema path is missing: {path_value}"]

    try:
        schema = load_schema(schema_path)
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"{location}: invalid schema JSON: {exc}"]

    required = requirement.get("required", [])
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        errors.append(f"{location}: required must be a string array")
        required = []
    root_required = schema.get("required", [])
    root_properties = schema.get("properties", {})
    for field in required:
        if field not in root_required:
            errors.append(f"{location}: schema root required is missing '{field}'")
        if not isinstance(root_properties, dict) or field not in root_properties:
            errors.append(f"{location}: schema root properties is missing '{field}'")

    nested_required = requirement.get("nestedRequired", {})
    if not isinstance(nested_required, dict):
        errors.append(f"{location}: nestedRequired must be an object")
        nested_required = {}
    for field, nested_fields in nested_required.items():
        if not isinstance(field, str) or not isinstance(nested_fields, list) or not all(
            isinstance(item, str) for item in nested_fields
        ):
            errors.append(f"{location}: nestedRequired entries must map strings to string arrays")
            continue
        nested_schema = root_properties.get(field) if isinstance(root_properties, dict) else None
        if not isinstance(nested_schema, dict):
            errors.append(f"{location}: nested schema '{field}' is missing")
            continue
        nested_schema_required = nested_schema.get("required", [])
        nested_schema_properties = nested_schema.get("properties", {})
        for nested_field in nested_fields:
            if nested_field not in nested_schema_required:
                errors.append(f"{location}: nested schema '{field}' required is missing '{nested_field}'")
            if not isinstance(nested_schema_properties, dict) or nested_field not in nested_schema_properties:
                errors.append(f"{location}: nested schema '{field}' properties is missing '{nested_field}'")

    return errors


def validate_control_example_requirement(requirement: Any, location: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(requirement, dict):
        return [f"{location}: example requirement must be an object"]

    path_value = requirement.get("path")
    if not isinstance(path_value, str):
        return [f"{location}: path must be a string"]
    example_path = ROOT / path_value
    if not example_path.is_file():
        return [f"{location}: example path is missing: {path_value}"]

    try:
        example = parse_yaml_example(example_path)
    except KitValidationError as exc:
        return [f"{location}: invalid YAML example: {exc}"]

    fields = requirement.get("fields")
    if not isinstance(fields, list) or not all(isinstance(item, str) for item in fields):
        return [f"{location}: fields must be a string array"]
    for field in fields:
        if get_dotted_value(example, field) is None:
            errors.append(f"{location}: example is missing field '{field}'")

    return errors


def validate_instance(schema: dict[str, Any], value: Any, location: str) -> list[str]:
    errors: list[str] = []
    schema_type = schema.get("type")

    if isinstance(schema_type, str):
        if not matches_schema_type(schema_type, value):
            errors.append(f"{location}: expected {schema_type}, got {type(value).__name__}")
            return errors

    if "enum" in schema:
        allowed = schema["enum"]
        if isinstance(allowed, list) and value not in allowed:
            errors.append(f"{location}: value '{value}' is not in enum {allowed}")

    if schema_type == "string" and isinstance(value, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(value) < min_length:
            errors.append(f"{location}: expected string length >= {min_length}")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, value):
            errors.append(f"{location}: value '{value}' does not match pattern '{pattern}'")
        if schema.get("format") == "date" and not is_iso_date(value):
            errors.append(f"{location}: value '{value}' is not a YYYY-MM-DD date")
        if schema.get("format") == "date-time" and not is_iso_datetime(value):
            errors.append(f"{location}: value '{value}' is not an RFC 3339 date-time")

    if schema_type in {"number", "integer"} and isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{location}: value {value} is below minimum {minimum}")
        if isinstance(maximum, (int, float)) and value > maximum:
            errors.append(f"{location}: value {value} is above maximum {maximum}")

    if schema_type == "object":
        if not isinstance(value, dict):
            return errors
        required = schema.get("required", [])
        if isinstance(required, list):
            for field in required:
                if field not in value:
                    errors.append(f"{location}: missing required field '{field}'")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            additional_properties = schema.get("additionalProperties")
            if additional_properties is not False:
                errors.append(f"{location}: strict object schemas must set additionalProperties=false")
            else:
                unexpected_fields = sorted(set(value) - set(properties))
                for field in unexpected_fields:
                    errors.append(f"{location}: unexpected field '{field}'")
            for field, field_schema in properties.items():
                if field in value and isinstance(field_schema, dict):
                    errors.extend(validate_instance(field_schema, value[field], f"{location}.{field}"))

    if schema_type == "array":
        if not isinstance(value, list):
            return errors
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(value) < min_items:
            errors.append(f"{location}: expected at least {min_items} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for item_index, item in enumerate(value):
                errors.extend(validate_instance(item_schema, item, f"{location}[{item_index}]"))

    return errors


def load_examples() -> dict[str, Any]:
    examples: dict[str, Any] = {}
    for name in PAIR_NAMES:
        example_path = KIT_DIR / f"{name}.example.yaml"
        if example_path.is_file():
            examples[name] = parse_yaml_example(example_path)
    return examples


def validate_cross_file_consistency(examples: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def parse_example_date(value: Any) -> date | None:
        if not isinstance(value, str) or not is_iso_date(value):
            return None
        return date.fromisoformat(value)

    def parse_example_datetime(value: Any) -> datetime | None:
        if not isinstance(value, str) or not is_iso_datetime(value):
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def mapping_values(items: Any, key: str) -> list[Any]:
        if not isinstance(items, list):
            return []
        return [item.get(key) for item in items if isinstance(item, dict)]

    domain = examples.get("domain")
    service = examples.get("service")
    api_contract = examples.get("api-contract")
    event_contract = examples.get("event-contract")
    data_product = examples.get("data-product")
    catalog_component = examples.get("catalog-component")
    catalog_data_product = examples.get("catalog-data-product")
    ai_product = examples.get("ai-product")
    ai_tool_contract = examples.get("ai-tool-contract")
    rag_index_contract = examples.get("rag-index-contract")
    fine_tuning_contract = examples.get("fine-tuning-contract")
    catalog_ai_product = examples.get("catalog-ai-product")
    gitops_deployment = examples.get("gitops-deployment")
    release_evidence = examples.get("release-evidence")
    supply_chain_attestation = examples.get("supply-chain-attestation")
    policy_exception = examples.get("policy-exception")
    api_compatibility_report = examples.get("api-compatibility-report")
    event_compatibility_report = examples.get("event-compatibility-report")
    gitops_drift_report = examples.get("gitops-drift-report")
    audit_evidence_index = examples.get("audit-evidence-index")
    scorecard = examples.get("scorecard")
    extension_policy = examples.get("extension-policy")
    feature_flag_control = examples.get("feature-flag-control")
    ai_threat_model = examples.get("ai-threat-model")
    lineage_event = examples.get("lineage-event")
    platform_product_metrics = examples.get("platform-product-metrics")
    privacy_impact_assessment = examples.get("privacy-impact-assessment")
    tenant_boundary = examples.get("tenant-boundary")
    recovery_drill_evidence = examples.get("recovery-drill-evidence")
    policy_test_report = examples.get("policy-test-report")
    genai_observability_contract = examples.get("genai-observability-contract")
    cost_allocation_evidence = examples.get("cost-allocation-evidence")
    identity_access_review = examples.get("identity-access-review")
    secrets_rotation_evidence = examples.get("secrets-rotation-evidence")
    vulnerability_remediation_evidence = examples.get("vulnerability-remediation-evidence")
    incident_postmortem = examples.get("incident-postmortem")
    evidence_freshness_policy = examples.get("evidence-freshness-policy")
    control_evidence_map = examples.get("control-evidence-map")
    audit_export_manifest = examples.get("audit-export-manifest")
    control_assessment_report = examples.get("control-assessment-report")
    baseline_change_record = examples.get("baseline-change-record")
    oscal_export_profile = examples.get("oscal-export-profile")
    audit_export_gate = examples.get("audit-export-gate")
    audit_export_integrity = examples.get("audit-export-integrity")
    audit_export_provenance = examples.get("audit-export-provenance")
    audit_export_signing_policy = examples.get("audit-export-signing-policy")
    audit_export_signature_receipt = examples.get("audit-export-signature-receipt")
    try:
        version_manifest = load_version_manifest()
    except (json.JSONDecodeError, ValueError):
        version_manifest = {}
    try:
        control_catalog = load_control_catalog()
    except (json.JSONDecodeError, ValueError):
        control_catalog = {}
    catalog_controls = control_catalog.get("controls") if isinstance(control_catalog, dict) else None
    if not isinstance(catalog_controls, list):
        catalog_controls = []
    catalog_control_ids = [
        control.get("id") for control in catalog_controls if isinstance(control, dict) and isinstance(control.get("id"), str)
    ]

    if isinstance(domain, dict) and isinstance(service, dict):
        if service.get("domain") != domain.get("domain"):
            errors.append("cross-file: service.domain must match domain.domain")
        if service.get("owner") != domain.get("owner"):
            errors.append("cross-file: service.owner must match domain.owner in starter kit examples")
        if service.get("tier") != domain.get("sloTier"):
            errors.append("cross-file: service.tier must match domain.sloTier in starter kit examples")

    if isinstance(service, dict) and isinstance(api_contract, dict):
        if api_contract.get("domain") != service.get("domain"):
            errors.append("cross-file: api-contract.domain must match service.domain")
        if api_contract.get("owner") != service.get("owner"):
            errors.append("cross-file: api-contract.owner must match service.owner")
        if api_contract.get("producerService") != service.get("service"):
            errors.append("cross-file: api-contract.producerService must match service.service")

    if isinstance(service, dict) and isinstance(event_contract, dict):
        if event_contract.get("domain") != service.get("domain"):
            errors.append("cross-file: event-contract.domain must match service.domain")
        if event_contract.get("owner") != service.get("owner"):
            errors.append("cross-file: event-contract.owner must match service.owner")
        if event_contract.get("producerService") != service.get("service"):
            errors.append("cross-file: event-contract.producerService must match service.service")

    if isinstance(domain, dict) and isinstance(data_product, dict):
        if data_product.get("domain") != domain.get("domain"):
            errors.append("cross-file: data-product.domain must match domain.domain")
        if data_product.get("owner") != domain.get("owner"):
            errors.append("cross-file: data-product.owner must match domain.owner in starter kit examples")
        lineage = data_product.get("lineage")
        consumers = data_product.get("consumers")
        if isinstance(lineage, dict) and isinstance(consumers, list):
            downstream = lineage.get("downstream")
            if isinstance(downstream, list) and sorted(consumers) != sorted(downstream):
                errors.append("cross-file: data-product.consumers must match data-product.lineage.downstream in starter kit examples")
        cost = data_product.get("cost")
        if isinstance(cost, dict) and cost.get("owner") != data_product.get("owner"):
            errors.append("cross-file: data-product.cost.owner must match data-product.owner")
        data_slo = data_product.get("slo")
        if isinstance(data_slo, dict) and data_slo.get("freshness") != data_product.get("freshness"):
            errors.append("cross-file: data-product.slo.freshness must match data-product.freshness")

    if isinstance(data_product, dict) and isinstance(catalog_data_product, dict):
        if catalog_data_product.get("name") != data_product.get("dataProduct"):
            errors.append("cross-file: catalog-data-product.name must match data-product.dataProduct")
        if catalog_data_product.get("domain") != data_product.get("domain"):
            errors.append("cross-file: catalog-data-product.domain must match data-product.domain")
        if catalog_data_product.get("owner") != data_product.get("owner"):
            errors.append("cross-file: catalog-data-product.owner must match data-product.owner")
        data_classification = data_product.get("classification")
        if isinstance(data_classification, dict) and catalog_data_product.get("classification") != data_classification.get("level"):
            errors.append("cross-file: catalog-data-product.classification must match data-product.classification.level")

    if isinstance(service, dict) and isinstance(catalog_component, dict):
        if catalog_component.get("name") != service.get("service"):
            errors.append("cross-file: catalog-component.name must match service.service")
        if catalog_component.get("domain") != service.get("domain"):
            errors.append("cross-file: catalog-component.domain must match service.domain")
        if catalog_component.get("owner") != service.get("owner"):
            errors.append("cross-file: catalog-component.owner must match service.owner")
        runtime = catalog_component.get("runtime")
        service_runtime = service.get("runtime")
        if isinstance(runtime, dict) and isinstance(service_runtime, dict):
            if runtime.get("imageRepository") != service_runtime.get("imageRepository"):
                errors.append("cross-file: catalog runtime imageRepository must match service runtime imageRepository")

    if isinstance(catalog_component, dict) and isinstance(gitops_deployment, dict):
        runtime = catalog_component.get("runtime")
        if isinstance(runtime, dict):
            if runtime.get("namespace") != gitops_deployment.get("namespace"):
                errors.append("cross-file: catalog runtime namespace must match gitops-deployment.namespace")
            if runtime.get("deployment") != gitops_deployment.get("deployment"):
                errors.append("cross-file: catalog runtime deployment must match gitops-deployment.deployment")

    if isinstance(service, dict) and isinstance(gitops_deployment, dict):
        if gitops_deployment.get("domain") != service.get("domain"):
            errors.append("cross-file: gitops-deployment.domain must match service.domain")
        if gitops_deployment.get("service") != service.get("service"):
            errors.append("cross-file: gitops-deployment.service must match service.service")
        if gitops_deployment.get("deployment") != service.get("service"):
            errors.append("cross-file: gitops-deployment.deployment must match service.service")
        if gitops_deployment.get("serviceAccount") != service.get("service"):
            errors.append("cross-file: gitops-deployment.serviceAccount must match service.service in starter kit examples")
        service_runtime = service.get("runtime")
        deployment_image = gitops_deployment.get("image")
        if isinstance(service_runtime, dict) and isinstance(deployment_image, dict):
            if deployment_image.get("repository") != service_runtime.get("imageRepository"):
                errors.append("cross-file: gitops-deployment.image.repository must match service.runtime.imageRepository")
        scaling = gitops_deployment.get("scaling")
        if isinstance(scaling, dict):
            min_replicas = scaling.get("minReplicas")
            max_replicas = scaling.get("maxReplicas")
            if isinstance(min_replicas, int) and isinstance(max_replicas, int) and max_replicas < min_replicas:
                errors.append("cross-file: gitops-deployment.scaling.maxReplicas must be >= minReplicas")

    if isinstance(service, dict) and isinstance(release_evidence, dict):
        if release_evidence.get("subjectService") != service.get("service"):
            errors.append("cross-file: release-evidence.subjectService must match service.service")
        if release_evidence.get("domain") != service.get("domain"):
            errors.append("cross-file: release-evidence.domain must match service.domain")
        if release_evidence.get("owner") != service.get("owner"):
            errors.append("cross-file: release-evidence.owner must match service.owner")
        artifact = release_evidence.get("artifact")
        service_runtime = service.get("runtime")
        if isinstance(artifact, dict) and isinstance(service_runtime, dict):
            if artifact.get("repository") != service_runtime.get("imageRepository"):
                errors.append("cross-file: release-evidence.artifact.repository must match service.runtime.imageRepository")

    if isinstance(gitops_deployment, dict) and isinstance(release_evidence, dict):
        if release_evidence.get("environment") != gitops_deployment.get("environment"):
            errors.append("cross-file: release-evidence.environment must match gitops-deployment.environment")
        artifact = release_evidence.get("artifact")
        deployment_image = gitops_deployment.get("image")
        if isinstance(artifact, dict) and isinstance(deployment_image, dict):
            if artifact.get("digest") != deployment_image.get("digest"):
                errors.append("cross-file: release-evidence.artifact.digest must match gitops-deployment.image.digest")

    if isinstance(catalog_component, dict) and isinstance(release_evidence, dict):
        expected_component = f"catalog/components/{catalog_component.get('name')}.yaml"
        if release_evidence.get("catalogComponent") != expected_component:
            errors.append("cross-file: release-evidence.catalogComponent must point to catalog component example path")
        runtime = catalog_component.get("runtime")
        if isinstance(runtime, dict) and release_evidence.get("gitopsPath") != runtime.get("gitopsPath"):
            errors.append("cross-file: release-evidence.gitopsPath must match catalog-component.runtime.gitopsPath")

    if isinstance(release_evidence, dict) and isinstance(audit_evidence_index, dict):
        if release_evidence.get("release") != audit_evidence_index.get("evidence"):
            errors.append("cross-file: release-evidence.release must match audit-evidence-index.evidence")
        if release_evidence.get("owner") != audit_evidence_index.get("owner"):
            errors.append("cross-file: release-evidence.owner must match audit-evidence-index.owner")
        if release_evidence.get("subjectService") != audit_evidence_index.get("subject"):
            errors.append("cross-file: release-evidence.subjectService must match audit-evidence-index.subject")

    if isinstance(service, dict) and isinstance(supply_chain_attestation, dict):
        if supply_chain_attestation.get("subjectService") != service.get("service"):
            errors.append("cross-file: supply-chain-attestation.subjectService must match service.service")
        if supply_chain_attestation.get("owner") != service.get("owner"):
            errors.append("cross-file: supply-chain-attestation.owner must match service.owner")
        artifact = supply_chain_attestation.get("artifact")
        service_runtime = service.get("runtime")
        if isinstance(artifact, dict) and isinstance(service_runtime, dict):
            if artifact.get("repository") != service_runtime.get("imageRepository"):
                errors.append("cross-file: supply-chain-attestation.artifact.repository must match service.runtime.imageRepository")

    if isinstance(gitops_deployment, dict) and isinstance(supply_chain_attestation, dict):
        artifact = supply_chain_attestation.get("artifact")
        deployment_image = gitops_deployment.get("image")
        if isinstance(artifact, dict) and isinstance(deployment_image, dict):
            if artifact.get("digest") != deployment_image.get("digest"):
                errors.append("cross-file: supply-chain-attestation.artifact.digest must match gitops-deployment.image.digest")
        gitops_security = gitops_deployment.get("security")
        attestation_verification = supply_chain_attestation.get("verification")
        if isinstance(gitops_security, dict) and isinstance(attestation_verification, dict):
            if gitops_security.get("imageVerificationPolicy") != attestation_verification.get("policy"):
                errors.append(
                    "cross-file: gitops-deployment.security.imageVerificationPolicy must match supply-chain-attestation.verification.policy"
                )
        gitops_policy = gitops_deployment.get("policy")
        if isinstance(gitops_policy, dict) and gitops_deployment.get("environment") == "prod":
            for field in ("requiresSignedImage", "requiresProvenance", "requiresSbom"):
                if gitops_policy.get(field) is not True:
                    errors.append(f"cross-file: prod gitops-deployment.policy.{field} must be true")

    if isinstance(release_evidence, dict) and isinstance(supply_chain_attestation, dict):
        if supply_chain_attestation.get("source", {}).get("commit") != release_evidence.get("commit"):
            errors.append("cross-file: supply-chain-attestation.source.commit must match release-evidence.commit")
        release_supply_chain = release_evidence.get("supplyChain")
        if isinstance(release_supply_chain, dict):
            if release_supply_chain.get("attestation") != supply_chain_attestation.get("attestation"):
                errors.append("cross-file: release-evidence.supplyChain.attestation must match supply-chain-attestation.attestation")
            if release_supply_chain.get("sbom") != supply_chain_attestation.get("sbom", {}).get("location"):
                errors.append("cross-file: release-evidence.supplyChain.sbom must match supply-chain-attestation.sbom.location")
            if release_supply_chain.get("provenance") != supply_chain_attestation.get("provenance", {}).get("location"):
                errors.append(
                    "cross-file: release-evidence.supplyChain.provenance must match supply-chain-attestation.provenance.location"
                )
            if release_supply_chain.get("signature") != supply_chain_attestation.get("signature", {}).get("location"):
                errors.append(
                    "cross-file: release-evidence.supplyChain.signature must match supply-chain-attestation.signature.location"
                )
        release_verification = release_evidence.get("verification")
        attestation_verification = supply_chain_attestation.get("verification")
        if isinstance(release_verification, dict) and isinstance(attestation_verification, dict):
            if release_verification.get("policy") != attestation_verification.get("policy"):
                errors.append("cross-file: release-evidence.verification.policy must match supply-chain-attestation.verification.policy")
        vulnerability = supply_chain_attestation.get("vulnerability")
        if supply_chain_attestation.get("verification", {}).get("result") == "pass" and isinstance(vulnerability, dict):
            if vulnerability.get("criticalOpen") != 0:
                errors.append("cross-file: passing supply-chain-attestation must have zero critical vulnerabilities")
            if vulnerability.get("highOpen") != 0:
                errors.append("cross-file: passing supply-chain-attestation must have zero high vulnerabilities")
        scorecard_result = supply_chain_attestation.get("scorecard")
        if isinstance(scorecard_result, dict):
            minimum_score = scorecard_result.get("minimumScore")
            actual_score = scorecard_result.get("actualScore")
            if isinstance(minimum_score, int) and isinstance(actual_score, int) and actual_score < minimum_score:
                errors.append("cross-file: supply-chain-attestation.scorecard.actualScore must be >= minimumScore")

    if isinstance(service, dict) and isinstance(policy_exception, dict):
        if policy_exception.get("subject") != service.get("service"):
            errors.append("cross-file: policy-exception.subject must match service.service")
        if policy_exception.get("owner") != service.get("owner"):
            errors.append("cross-file: policy-exception.owner must match service.owner")

    if isinstance(policy_exception, dict) and isinstance(supply_chain_attestation, dict):
        if policy_exception.get("policy") != supply_chain_attestation.get("verification", {}).get("policy"):
            errors.append("cross-file: policy-exception.policy must match supply-chain-attestation.verification.policy")
        approved_at = parse_example_date(policy_exception.get("approvedAt"))
        expires_on = parse_example_date(policy_exception.get("expiresOn"))
        remediation = policy_exception.get("remediation")
        due_date = parse_example_date(remediation.get("dueDate")) if isinstance(remediation, dict) else None
        if approved_at is not None and expires_on is not None and expires_on <= approved_at:
            errors.append("cross-file: policy-exception.expiresOn must be after approvedAt")
        if due_date is not None and expires_on is not None and due_date > expires_on:
            errors.append("cross-file: policy-exception.remediation.dueDate must be on or before expiresOn")

    if isinstance(api_contract, dict) and isinstance(ai_tool_contract, dict):
        if ai_tool_contract.get("backingApi") != api_contract.get("api"):
            errors.append("cross-file: ai-tool-contract.backingApi must match api-contract.api")

    if isinstance(api_contract, dict) and isinstance(api_compatibility_report, dict):
        if api_compatibility_report.get("api") != api_contract.get("api"):
            errors.append("cross-file: api-compatibility-report.api must match api-contract.api")
        if api_compatibility_report.get("owner") != api_contract.get("owner"):
            errors.append("cross-file: api-compatibility-report.owner must match api-contract.owner")
        if api_compatibility_report.get("candidateVersion") != api_contract.get("version"):
            errors.append("cross-file: api-compatibility-report.candidateVersion must match api-contract.version")
        if api_compatibility_report.get("spec") != api_contract.get("spec"):
            errors.append("cross-file: api-compatibility-report.spec must match api-contract.spec")
        api_consumers = sorted(api_contract.get("consumers", [])) if isinstance(api_contract.get("consumers"), list) else []
        impact_consumers = sorted(mapping_values(api_compatibility_report.get("consumerImpact"), "consumer"))
        if api_consumers != impact_consumers:
            errors.append("cross-file: api-compatibility-report.consumerImpact consumers must match api-contract.consumers")

    if isinstance(event_contract, dict) and isinstance(event_compatibility_report, dict):
        if event_compatibility_report.get("event") != event_contract.get("event"):
            errors.append("cross-file: event-compatibility-report.event must match event-contract.event")
        if event_compatibility_report.get("owner") != event_contract.get("owner"):
            errors.append("cross-file: event-compatibility-report.owner must match event-contract.owner")
        if event_compatibility_report.get("candidateVersion") != event_contract.get("version"):
            errors.append("cross-file: event-compatibility-report.candidateVersion must match event-contract.version")
        if event_compatibility_report.get("schema") != event_contract.get("schema"):
            errors.append("cross-file: event-compatibility-report.schema must match event-contract.schema")
        event_consumers = sorted(event_contract.get("consumers", [])) if isinstance(event_contract.get("consumers"), list) else []
        impact_consumers = sorted(mapping_values(event_compatibility_report.get("consumerImpact"), "consumer"))
        if event_consumers != impact_consumers:
            errors.append("cross-file: event-compatibility-report.consumerImpact consumers must match event-contract.consumers")

    if isinstance(gitops_deployment, dict) and isinstance(gitops_drift_report, dict):
        if gitops_drift_report.get("environment") != gitops_deployment.get("environment"):
            errors.append("cross-file: gitops-drift-report.environment must match gitops-deployment.environment")
        if gitops_drift_report.get("service") != gitops_deployment.get("service"):
            errors.append("cross-file: gitops-drift-report.service must match gitops-deployment.service")
        if gitops_drift_report.get("domain") != gitops_deployment.get("domain"):
            errors.append("cross-file: gitops-drift-report.domain must match gitops-deployment.domain")
        if isinstance(service, dict) and gitops_drift_report.get("owner") != service.get("owner"):
            errors.append("cross-file: gitops-drift-report.owner must match service.owner")
        expected = gitops_drift_report.get("expected")
        deployment_image = gitops_deployment.get("image")
        if isinstance(expected, dict) and isinstance(deployment_image, dict):
            if expected.get("imageDigest") != deployment_image.get("digest"):
                errors.append("cross-file: gitops-drift-report.expected.imageDigest must match gitops-deployment.image.digest")
            if expected.get("namespace") != gitops_deployment.get("namespace"):
                errors.append("cross-file: gitops-drift-report.expected.namespace must match gitops-deployment.namespace")
            if expected.get("replicas") != gitops_deployment.get("replicas"):
                errors.append("cross-file: gitops-drift-report.expected.replicas must match gitops-deployment.replicas")
        observed = gitops_drift_report.get("observed")
        if gitops_drift_report.get("decision") == "no-drift" and isinstance(expected, dict) and isinstance(observed, dict):
            for field in ("namespace", "imageDigest", "replicas", "configHash", "serviceAccount", "policyHash"):
                if expected.get(field) != observed.get(field):
                    errors.append(f"cross-file: gitops-drift-report.observed.{field} must match expected.{field} when decision is no-drift")

    if isinstance(ai_product, dict) and isinstance(ai_tool_contract, dict):
        tools = ai_product.get("tools")
        registered_tools = []
        tool_entries = []
        if isinstance(tools, list):
            tool_entries = [item for item in tools if isinstance(item, dict)]
            registered_tools = [item.get("tool") for item in tool_entries]
        if ai_tool_contract.get("tool") not in registered_tools:
            errors.append("cross-file: ai-tool-contract.tool must be listed in ai-product.tools")
        matching_tool_entries = [item for item in tool_entries if item.get("tool") == ai_tool_contract.get("tool")]
        if matching_tool_entries:
            ai_tool_entry = matching_tool_entries[0]
            runtime_controls = ai_tool_contract.get("runtimeControls")
            if isinstance(runtime_controls, dict):
                if ai_tool_entry.get("requiresHumanApproval") != runtime_controls.get("requiresHumanApproval"):
                    errors.append(
                        "cross-file: ai-product.tools.requiresHumanApproval must match ai-tool-contract.runtimeControls.requiresHumanApproval"
                    )
            expected_risk_level = {
                "R1": "low",
                "R2": "medium",
                "R3": "high",
                "R4": "critical",
                "R5": "critical",
            }.get(ai_tool_contract.get("riskTier"))
            if expected_risk_level and ai_tool_entry.get("riskLevel") != expected_risk_level:
                errors.append("cross-file: ai-product.tools.riskLevel must match ai-tool-contract.riskTier mapping")

    if isinstance(ai_product, dict) and isinstance(rag_index_contract, dict):
        rag = ai_product.get("rag")
        if isinstance(rag, dict) and rag_index_contract.get("indexId") != rag.get("vectorIndex"):
            errors.append("cross-file: rag-index-contract.indexId must match ai-product.rag.vectorIndex")

    if isinstance(ai_product, dict) and isinstance(fine_tuning_contract, dict):
        if fine_tuning_contract.get("owner") != ai_product.get("owner"):
            errors.append("cross-file: fine-tuning-contract.owner must match ai-product.owner")

    if isinstance(ai_product, dict) and isinstance(catalog_ai_product, dict):
        if catalog_ai_product.get("name") != ai_product.get("aiProduct"):
            errors.append("cross-file: catalog-ai-product.name must match ai-product.aiProduct")
        if catalog_ai_product.get("owner") != ai_product.get("owner"):
            errors.append("cross-file: catalog-ai-product.owner must match ai-product.owner")
        if catalog_ai_product.get("lifecycle") != ai_product.get("lifecycle"):
            errors.append("cross-file: catalog-ai-product.lifecycle must match ai-product.lifecycle")
        if catalog_ai_product.get("riskTier") != ai_product.get("riskTier"):
            errors.append("cross-file: catalog-ai-product.riskTier must match ai-product.riskTier")
        runtime = catalog_ai_product.get("runtime")
        model = ai_product.get("model")
        rag = ai_product.get("rag")
        if isinstance(runtime, dict) and isinstance(model, dict):
            if runtime.get("gatewayRoute") != model.get("gatewayRoute"):
                errors.append("cross-file: catalog-ai-product.runtime.gatewayRoute must match ai-product.model.gatewayRoute")
        if isinstance(runtime, dict) and isinstance(rag, dict):
            if runtime.get("ragIndex") != rag.get("vectorIndex"):
                errors.append("cross-file: catalog-ai-product.runtime.ragIndex must match ai-product.rag.vectorIndex")
        budget = ai_product.get("budget")
        if isinstance(budget, dict) and budget.get("owner") != ai_product.get("owner"):
            errors.append("cross-file: ai-product.budget.owner must match ai-product.owner")

    if isinstance(service, dict) and isinstance(scorecard, dict):
        if scorecard.get("subject") != service.get("service"):
            errors.append("cross-file: scorecard.subject must match service.service")
        if scorecard.get("owner") != service.get("owner"):
            errors.append("cross-file: scorecard.owner must match service.owner")
        if scorecard.get("lifecycle") != service.get("lifecycle"):
            errors.append("cross-file: scorecard.lifecycle must match service.lifecycle")

    if isinstance(extension_policy, dict):
        validation = extension_policy.get("validation")
        if isinstance(validation, dict):
            if validation.get("defaultDecision") != "reject":
                errors.append("cross-file: extension-policy.validation.defaultDecision must be reject")
            if validation.get("unknownFieldBehavior") != "fail":
                errors.append("cross-file: extension-policy.validation.unknownFieldBehavior must be fail")
        allowed_prefixes = extension_policy.get("allowedPrefixes")
        if isinstance(allowed_prefixes, list) and "x-company-" not in allowed_prefixes:
            errors.append("cross-file: extension-policy.allowedPrefixes must include x-company-")

    if isinstance(service, dict) and isinstance(feature_flag_control, dict):
        if feature_flag_control.get("domain") != service.get("domain"):
            errors.append("cross-file: feature-flag-control.domain must match service.domain")
        if feature_flag_control.get("service") != service.get("service"):
            errors.append("cross-file: feature-flag-control.service must match service.service")
        if feature_flag_control.get("owner") != service.get("owner"):
            errors.append("cross-file: feature-flag-control.owner must match service.owner")
        flag_guardrails = feature_flag_control.get("guardrails")
        if isinstance(flag_guardrails, dict):
            if flag_guardrails.get("killSwitch") is not True:
                errors.append("cross-file: feature-flag-control.guardrails.killSwitch must be true")
            if flag_guardrails.get("rollbackOnSloBurn") is not True:
                errors.append("cross-file: feature-flag-control.guardrails.rollbackOnSloBurn must be true")

    if isinstance(ai_product, dict) and isinstance(ai_threat_model, dict):
        if ai_threat_model.get("aiProduct") != ai_product.get("aiProduct"):
            errors.append("cross-file: ai-threat-model.aiProduct must match ai-product.aiProduct")
        if ai_threat_model.get("owner") != ai_product.get("owner"):
            errors.append("cross-file: ai-threat-model.owner must match ai-product.owner")
        if ai_threat_model.get("riskTier") != ai_product.get("riskTier"):
            errors.append("cross-file: ai-threat-model.riskTier must match ai-product.riskTier")
        scope = ai_threat_model.get("scope")
        if isinstance(scope, dict) and isinstance(ai_tool_contract, dict):
            scoped_tools = scope.get("tools")
            if isinstance(scoped_tools, list) and ai_tool_contract.get("tool") not in scoped_tools:
                errors.append("cross-file: ai-threat-model.scope.tools must include ai-tool-contract.tool")
        threat_controls = ai_threat_model.get("controls")
        if isinstance(threat_controls, dict):
            if threat_controls.get("toolConsentRequired") is not True:
                errors.append("cross-file: ai-threat-model.controls.toolConsentRequired must be true")
            if isinstance(ai_tool_contract, dict):
                runtime_controls = ai_tool_contract.get("runtimeControls")
                if isinstance(runtime_controls, dict):
                    if threat_controls.get("humanApprovalRequired") != runtime_controls.get("requiresHumanApproval"):
                        errors.append(
                            "cross-file: ai-threat-model.controls.humanApprovalRequired must match ai-tool-contract.runtimeControls.requiresHumanApproval"
                        )

    if isinstance(data_product, dict) and isinstance(lineage_event, dict):
        if lineage_event.get("dataProduct") != data_product.get("dataProduct"):
            errors.append("cross-file: lineage-event.dataProduct must match data-product.dataProduct")
        if lineage_event.get("domain") != data_product.get("domain"):
            errors.append("cross-file: lineage-event.domain must match data-product.domain")
        if lineage_event.get("owner") != data_product.get("owner"):
            errors.append("cross-file: lineage-event.owner must match data-product.owner")
        if lineage_event.get("outputDataProduct") != data_product.get("dataProduct"):
            errors.append("cross-file: lineage-event.outputDataProduct must match data-product.dataProduct")
        run = lineage_event.get("run")
        if isinstance(run, dict) and run.get("state") != "COMPLETE":
            errors.append("cross-file: lineage-event.run.state must be COMPLETE in starter kit examples")

    if isinstance(platform_product_metrics, dict):
        metrics = platform_product_metrics.get("metrics")
        if isinstance(metrics, dict):
            if metrics.get("developerSatisfaction") is None:
                errors.append("cross-file: platform-product-metrics.metrics.developerSatisfaction must be present")
            if metrics.get("cognitiveLoadScore") is None:
                errors.append("cross-file: platform-product-metrics.metrics.cognitiveLoadScore must be present")
            if metrics.get("selfServiceCompletionRate") is None:
                errors.append("cross-file: platform-product-metrics.metrics.selfServiceCompletionRate must be present")

    if isinstance(data_product, dict) and isinstance(privacy_impact_assessment, dict):
        if privacy_impact_assessment.get("dataProduct") != data_product.get("dataProduct"):
            errors.append("cross-file: privacy-impact-assessment.dataProduct must match data-product.dataProduct")
        if privacy_impact_assessment.get("domain") != data_product.get("domain"):
            errors.append("cross-file: privacy-impact-assessment.domain must match data-product.domain")
        if privacy_impact_assessment.get("owner") != data_product.get("owner"):
            errors.append("cross-file: privacy-impact-assessment.owner must match data-product.owner")
        data_classification = data_product.get("classification")
        assessment_classification = privacy_impact_assessment.get("classification")
        if isinstance(data_classification, dict) and isinstance(assessment_classification, dict):
            if assessment_classification.get("level") != data_classification.get("level"):
                errors.append("cross-file: privacy-impact-assessment.classification.level must match data-product.classification.level")
            pii_fields = data_classification.get("pii")
            if isinstance(pii_fields, list) and pii_fields:
                review = privacy_impact_assessment.get("review")
                if isinstance(review, dict) and review.get("dpiaRequired") is not True:
                    errors.append("cross-file: privacy-impact-assessment.review.dpiaRequired must be true when data-product has pii")
        deletion = privacy_impact_assessment.get("deletion")
        if isinstance(deletion, dict) and isinstance(rag_index_contract, dict):
            if deletion.get("vectorIndex") != rag_index_contract.get("indexId"):
                errors.append("cross-file: privacy-impact-assessment.deletion.vectorIndex must match rag-index-contract.indexId")
        controls = privacy_impact_assessment.get("controls")
        if isinstance(controls, dict):
            if controls.get("subjectDeletePropagation") is not True:
                errors.append("cross-file: privacy-impact-assessment.controls.subjectDeletePropagation must be true")
        review = privacy_impact_assessment.get("review")
        if isinstance(review, dict) and review.get("approved") is not True:
            errors.append("cross-file: privacy-impact-assessment.review.approved must be true")

    if isinstance(service, dict) and isinstance(tenant_boundary, dict):
        if tenant_boundary.get("domain") != service.get("domain"):
            errors.append("cross-file: tenant-boundary.domain must match service.domain")
        if tenant_boundary.get("service") != service.get("service"):
            errors.append("cross-file: tenant-boundary.service must match service.service")
        if tenant_boundary.get("owner") != service.get("owner"):
            errors.append("cross-file: tenant-boundary.owner must match service.owner")
        if isinstance(gitops_deployment, dict):
            if tenant_boundary.get("namespace") != gitops_deployment.get("namespace"):
                errors.append("cross-file: tenant-boundary.namespace must match gitops-deployment.namespace")
        network_policy = tenant_boundary.get("networkPolicy")
        if isinstance(network_policy, dict) and network_policy.get("defaultDeny") is not True:
            errors.append("cross-file: tenant-boundary.networkPolicy.defaultDeny must be true")
        resource_quota = tenant_boundary.get("resourceQuota")
        if isinstance(resource_quota, dict) and resource_quota.get("podLimit", 0) < 1:
            errors.append("cross-file: tenant-boundary.resourceQuota.podLimit must be >= 1")

    if isinstance(service, dict) and isinstance(recovery_drill_evidence, dict):
        if recovery_drill_evidence.get("service") != service.get("service"):
            errors.append("cross-file: recovery-drill-evidence.service must match service.service")
        if recovery_drill_evidence.get("domain") != service.get("domain"):
            errors.append("cross-file: recovery-drill-evidence.domain must match service.domain")
        if recovery_drill_evidence.get("owner") != service.get("owner"):
            errors.append("cross-file: recovery-drill-evidence.owner must match service.owner")
        if recovery_drill_evidence.get("tier") != service.get("tier"):
            errors.append("cross-file: recovery-drill-evidence.tier must match service.tier")
        recovery = recovery_drill_evidence.get("recovery")
        target = recovery_drill_evidence.get("target")
        if isinstance(recovery, dict):
            if recovery.get("status") != "pass":
                errors.append("cross-file: recovery-drill-evidence.recovery.status must be pass")
            if recovery.get("dataLossValidated") is not True:
                errors.append("cross-file: recovery-drill-evidence.recovery.dataLossValidated must be true")
            if isinstance(target, dict):
                achieved_rto = recovery.get("achievedRtoMinutes")
                target_rto = target.get("rtoMinutes")
                achieved_rpo = recovery.get("achievedRpoMinutes")
                target_rpo = target.get("rpoMinutes")
                if isinstance(achieved_rto, int) and isinstance(target_rto, int) and achieved_rto > target_rto:
                    errors.append("cross-file: recovery-drill-evidence.recovery.achievedRtoMinutes must be <= target.rtoMinutes")
                if isinstance(achieved_rpo, int) and isinstance(target_rpo, int) and achieved_rpo > target_rpo:
                    errors.append("cross-file: recovery-drill-evidence.recovery.achievedRpoMinutes must be <= target.rpoMinutes")

    if isinstance(service, dict) and isinstance(policy_test_report, dict):
        if policy_test_report.get("subject") != service.get("service"):
            errors.append("cross-file: policy-test-report.subject must match service.service")
        if policy_test_report.get("owner") != service.get("owner"):
            errors.append("cross-file: policy-test-report.owner must match service.owner")
        if isinstance(supply_chain_attestation, dict):
            if policy_test_report.get("policy") != supply_chain_attestation.get("verification", {}).get("policy"):
                errors.append("cross-file: policy-test-report.policy must match supply-chain-attestation.verification.policy")
        tests = policy_test_report.get("tests")
        result = policy_test_report.get("result")
        if isinstance(tests, dict):
            if tests.get("failed") != 0:
                errors.append("cross-file: policy-test-report.tests.failed must be 0")
            total = tests.get("total")
            passed = tests.get("passed")
            failed = tests.get("failed")
            if isinstance(total, int) and isinstance(passed, int) and isinstance(failed, int) and total != passed + failed:
                errors.append("cross-file: policy-test-report.tests.total must equal passed + failed")
        if isinstance(result, dict) and result.get("decision") != "pass":
            errors.append("cross-file: policy-test-report.result.decision must be pass")

    if isinstance(ai_product, dict) and isinstance(genai_observability_contract, dict):
        if genai_observability_contract.get("aiProduct") != ai_product.get("aiProduct"):
            errors.append("cross-file: genai-observability-contract.aiProduct must match ai-product.aiProduct")
        if genai_observability_contract.get("owner") != ai_product.get("owner"):
            errors.append("cross-file: genai-observability-contract.owner must match ai-product.owner")
        contract_model = genai_observability_contract.get("model")
        ai_model = ai_product.get("model")
        if isinstance(contract_model, dict) and isinstance(ai_model, dict):
            if contract_model.get("gatewayRoute") != ai_model.get("gatewayRoute"):
                errors.append("cross-file: genai-observability-contract.model.gatewayRoute must match ai-product.model.gatewayRoute")
        telemetry = genai_observability_contract.get("telemetry")
        if isinstance(telemetry, dict):
            if telemetry.get("traceEnabled") is not True:
                errors.append("cross-file: genai-observability-contract.telemetry.traceEnabled must be true")
            if telemetry.get("tokenMetrics") is not True:
                errors.append("cross-file: genai-observability-contract.telemetry.tokenMetrics must be true")
            if telemetry.get("costMetrics") is not True:
                errors.append("cross-file: genai-observability-contract.telemetry.costMetrics must be true")
            if telemetry.get("toolCallSpans") is not True:
                errors.append("cross-file: genai-observability-contract.telemetry.toolCallSpans must be true")
            if telemetry.get("ragSpans") is not True:
                errors.append("cross-file: genai-observability-contract.telemetry.ragSpans must be true")
        privacy = genai_observability_contract.get("privacy")
        if isinstance(privacy, dict) and privacy.get("piiRedaction") is not True:
            errors.append("cross-file: genai-observability-contract.privacy.piiRedaction must be true")

    if isinstance(data_product, dict) and isinstance(cost_allocation_evidence, dict):
        if cost_allocation_evidence.get("domain") != data_product.get("domain"):
            errors.append("cross-file: cost-allocation-evidence.domain must match data-product.domain")
        data_cost = data_product.get("cost")
        if isinstance(data_cost, dict):
            if cost_allocation_evidence.get("owner") != data_cost.get("owner"):
                errors.append("cross-file: cost-allocation-evidence.owner must match data-product.cost.owner")
            if cost_allocation_evidence.get("allocationTag") != data_cost.get("allocationTag"):
                errors.append("cross-file: cost-allocation-evidence.allocationTag must match data-product.cost.allocationTag")
        coverage = cost_allocation_evidence.get("coverage")
        if isinstance(coverage, dict):
            if coverage.get("taggedResourceRate") != 100:
                errors.append("cross-file: cost-allocation-evidence.coverage.taggedResourceRate must be 100")
            if coverage.get("unallocatedCostUsd") != 0:
                errors.append("cross-file: cost-allocation-evidence.coverage.unallocatedCostUsd must be 0")
        costs = cost_allocation_evidence.get("costs")
        if isinstance(costs, dict):
            subtotal = 0
            for field in ("cloudUsd", "aiUsd", "dataUsd"):
                value = costs.get(field)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    subtotal += value
            if isinstance(costs.get("totalUsd"), (int, float)) and costs.get("totalUsd") != subtotal:
                errors.append("cross-file: cost-allocation-evidence.costs.totalUsd must equal cloudUsd + aiUsd + dataUsd")

    if isinstance(service, dict) and isinstance(identity_access_review, dict):
        if identity_access_review.get("service") != service.get("service"):
            errors.append("cross-file: identity-access-review.service must match service.service")
        if identity_access_review.get("domain") != service.get("domain"):
            errors.append("cross-file: identity-access-review.domain must match service.domain")
        if identity_access_review.get("owner") != service.get("owner"):
            errors.append("cross-file: identity-access-review.owner must match service.owner")
        if isinstance(gitops_deployment, dict) and identity_access_review.get("namespace") != gitops_deployment.get("namespace"):
            errors.append("cross-file: identity-access-review.namespace must match gitops-deployment.namespace")
        break_glass = identity_access_review.get("breakGlass")
        if isinstance(break_glass, dict):
            if break_glass.get("mfaRequired") is not True:
                errors.append("cross-file: identity-access-review.breakGlass.mfaRequired must be true")
            if break_glass.get("maxDurationHours", 0) > 8:
                errors.append("cross-file: identity-access-review.breakGlass.maxDurationHours must be <= 8")
        review = identity_access_review.get("review")
        if isinstance(review, dict) and review.get("decision") != "pass":
            errors.append("cross-file: identity-access-review.review.decision must be pass")

    if isinstance(service, dict) and isinstance(secrets_rotation_evidence, dict):
        if secrets_rotation_evidence.get("service") != service.get("service"):
            errors.append("cross-file: secrets-rotation-evidence.service must match service.service")
        if secrets_rotation_evidence.get("domain") != service.get("domain"):
            errors.append("cross-file: secrets-rotation-evidence.domain must match service.domain")
        if secrets_rotation_evidence.get("owner") != service.get("owner"):
            errors.append("cross-file: secrets-rotation-evidence.owner must match service.owner")
        if isinstance(gitops_deployment, dict):
            if secrets_rotation_evidence.get("namespace") != gitops_deployment.get("namespace"):
                errors.append("cross-file: secrets-rotation-evidence.namespace must match gitops-deployment.namespace")
        crypto = secrets_rotation_evidence.get("crypto")
        if isinstance(crypto, dict) and crypto.get("encryptionAtRest") is not True:
            errors.append("cross-file: secrets-rotation-evidence.crypto.encryptionAtRest must be true")
        rotation = secrets_rotation_evidence.get("rotation")
        if isinstance(rotation, dict):
            if rotation.get("status") != "pass":
                errors.append("cross-file: secrets-rotation-evidence.rotation.status must be pass")
            last_rotated = parse_example_date(rotation.get("lastRotatedOn"))
            next_rotation = parse_example_date(rotation.get("nextRotationOn"))
            if last_rotated is not None and next_rotation is not None and next_rotation <= last_rotated:
                errors.append("cross-file: secrets-rotation-evidence.rotation.nextRotationOn must be after lastRotatedOn")
        exposure = secrets_rotation_evidence.get("exposure")
        if isinstance(exposure, dict) and exposure.get("detected") is not False:
            errors.append("cross-file: secrets-rotation-evidence.exposure.detected must be false")

    if isinstance(service, dict) and isinstance(vulnerability_remediation_evidence, dict):
        if vulnerability_remediation_evidence.get("subjectService") != service.get("service"):
            errors.append("cross-file: vulnerability-remediation-evidence.subjectService must match service.service")
        if vulnerability_remediation_evidence.get("domain") != service.get("domain"):
            errors.append("cross-file: vulnerability-remediation-evidence.domain must match service.domain")
        if vulnerability_remediation_evidence.get("owner") != service.get("owner"):
            errors.append("cross-file: vulnerability-remediation-evidence.owner must match service.owner")
        remediation = vulnerability_remediation_evidence.get("remediation")
        if isinstance(remediation, dict):
            if remediation.get("status") not in {"fixed", "mitigated"}:
                errors.append("cross-file: vulnerability-remediation-evidence.remediation.status must be fixed or mitigated")
            due_date = parse_example_date(remediation.get("dueDate"))
            remediated_on = parse_example_date(remediation.get("remediatedOn"))
            if due_date is not None and remediated_on is not None and remediated_on > due_date:
                errors.append("cross-file: vulnerability-remediation-evidence.remediation.remediatedOn must be on or before dueDate")
        residual = vulnerability_remediation_evidence.get("residual")
        if isinstance(residual, dict):
            if residual.get("criticalOpen") != 0:
                errors.append("cross-file: vulnerability-remediation-evidence.residual.criticalOpen must be 0")
            if residual.get("highOpen") != 0:
                errors.append("cross-file: vulnerability-remediation-evidence.residual.highOpen must be 0")
        decision = vulnerability_remediation_evidence.get("decision")
        if isinstance(decision, dict) and decision.get("releaseAllowed") is not True:
            errors.append("cross-file: vulnerability-remediation-evidence.decision.releaseAllowed must be true")

    if isinstance(service, dict) and isinstance(incident_postmortem, dict):
        if incident_postmortem.get("service") != service.get("service"):
            errors.append("cross-file: incident-postmortem.service must match service.service")
        if incident_postmortem.get("domain") != service.get("domain"):
            errors.append("cross-file: incident-postmortem.domain must match service.domain")
        if incident_postmortem.get("owner") != service.get("owner"):
            errors.append("cross-file: incident-postmortem.owner must match service.owner")
        incident = incident_postmortem.get("incident")
        if isinstance(incident, dict):
            detected_at = parse_example_datetime(incident.get("detectedAt"))
            resolved_at = parse_example_datetime(incident.get("resolvedAt"))
            if detected_at is not None and resolved_at is not None and resolved_at <= detected_at:
                errors.append("cross-file: incident-postmortem.incident.resolvedAt must be after detectedAt")
        prevention = incident_postmortem.get("prevention")
        if isinstance(prevention, dict):
            if prevention.get("runbookUpdated") is not True:
                errors.append("cross-file: incident-postmortem.prevention.runbookUpdated must be true")
            if prevention.get("gateUpdated") is not True:
                errors.append("cross-file: incident-postmortem.prevention.gateUpdated must be true")
        closure = incident_postmortem.get("closure")
        if isinstance(closure, dict) and closure.get("status") != "closed":
            errors.append("cross-file: incident-postmortem.closure.status must be closed")

    if isinstance(evidence_freshness_policy, dict):
        defaults = evidence_freshness_policy.get("defaults")
        if isinstance(defaults, dict):
            if defaults.get("expiryAction") != "block":
                errors.append("cross-file: evidence-freshness-policy.defaults.expiryAction must be block")
            if defaults.get("maxAgeDays", 0) > 90:
                errors.append("cross-file: evidence-freshness-policy.defaults.maxAgeDays must be <= 90")
        evidence_types = evidence_freshness_policy.get("evidenceTypes")
        if isinstance(evidence_types, list):
            for item in evidence_types:
                if isinstance(item, dict) and item.get("required") is not True:
                    errors.append("cross-file: evidence-freshness-policy.evidenceTypes.required must be true")
                    break
        automation = evidence_freshness_policy.get("automation")
        if isinstance(automation, dict) and automation.get("ciEnforced") is not True:
            errors.append("cross-file: evidence-freshness-policy.automation.ciEnforced must be true")

    if isinstance(control_evidence_map, dict):
        if control_evidence_map.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: control-evidence-map.version must match currentVersion")
        if control_evidence_map.get("controlCount") != len(catalog_control_ids):
            errors.append("cross-file: control-evidence-map.controlCount must match control catalog length")
        mapped_controls = control_evidence_map.get("controls")
        if isinstance(mapped_controls, list):
            mapped_ids: list[str] = []
            for item in mapped_controls:
                if not isinstance(item, dict):
                    continue
                control_id = item.get("id")
                if isinstance(control_id, str):
                    mapped_ids.append(control_id)
                if item.get("status") != "pass":
                    errors.append("cross-file: control-evidence-map.controls.status must be pass")
                if item.get("required") is not True:
                    errors.append("cross-file: control-evidence-map.controls.required must be true")
                if item.get("fresh") is not True:
                    errors.append("cross-file: control-evidence-map.controls.fresh must be true")
                if item.get("blocking") is not True:
                    errors.append("cross-file: control-evidence-map.controls.blocking must be true")
                evidence_items = item.get("evidence")
                if isinstance(evidence_items, list):
                    for evidence_item in evidence_items:
                        if not isinstance(evidence_item, dict):
                            continue
                        evidence_path = evidence_item.get("path")
                        if isinstance(evidence_path, str) and not (ROOT / evidence_path).is_file():
                            errors.append("cross-file: control-evidence-map.evidence.path must exist")
            if sorted(mapped_ids) != sorted(catalog_control_ids):
                errors.append("cross-file: control-evidence-map.controls must cover every control catalog id")
            if len(mapped_ids) != len(set(mapped_ids)):
                errors.append("cross-file: control-evidence-map.controls must not contain duplicate control ids")
        freshness = control_evidence_map.get("freshness")
        if isinstance(freshness, dict):
            if freshness.get("expiryAction") != "block":
                errors.append("cross-file: control-evidence-map.freshness.expiryAction must be block")
            if freshness.get("maxAgeDays", 0) > 90:
                errors.append("cross-file: control-evidence-map.freshness.maxAgeDays must be <= 90")

    if isinstance(audit_export_manifest, dict):
        scope = audit_export_manifest.get("scope")
        if isinstance(scope, dict):
            if scope.get("architectureVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: audit-export-manifest.scope.architectureVersion must match currentVersion")
            if scope.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: audit-export-manifest.scope.controlCount must match control catalog length")
            if scope.get("starterKitPairs") != len(PAIR_NAMES):
                errors.append("cross-file: audit-export-manifest.scope.starterKitPairs must match starter kit pair count")
        contents = audit_export_manifest.get("contents")
        if isinstance(contents, list):
            content_paths: set[str] = set()
            for item in contents:
                if not isinstance(item, dict):
                    continue
                path_value = item.get("path")
                if isinstance(path_value, str):
                    content_paths.add(path_value)
                    if item.get("required") is True and not (ROOT / path_value).is_file():
                        errors.append("cross-file: audit-export-manifest.contents.path must exist")
            required_content_paths = {
                "docs/references/modern-enterprise-architecture-template.md",
                "docs/references/modern-enterprise-architecture-version.json",
                "docs/references/modern-enterprise-architecture-controls.json",
                "docs/references/modern-enterprise-architecture-kit/control-evidence-map.example.yaml",
                "docs/references/modern-enterprise-architecture-kit/control-assessment-report.example.yaml",
                "docs/references/modern-enterprise-architecture-kit/oscal-export-profile.example.yaml",
                "docs/references/modern-enterprise-architecture-kit/audit-export-gate.example.yaml",
                "docs/references/modern-enterprise-architecture-kit/audit-export-integrity.example.yaml",
                "docs/references/modern-enterprise-architecture-kit/audit-export-provenance.example.yaml",
                "docs/references/modern-enterprise-architecture-kit/audit-export-signing-policy.example.yaml",
                "docs/references/modern-enterprise-architecture-kit/audit-export-signature-receipt.example.yaml",
                "scripts/check-modern-architecture-kit.py",
                "scripts/export-modern-architecture-audit.py",
                "scripts/check-modern-architecture-audit-export.py",
            }
            if not required_content_paths.issubset(content_paths):
                errors.append("cross-file: audit-export-manifest.contents must include required audit artifacts")
        verification = audit_export_manifest.get("verification")
        if isinstance(verification, dict):
            if verification.get("command") != "make check-modern-architecture-audit-export":
                errors.append(
                    "cross-file: audit-export-manifest.verification.command must be make check-modern-architecture-audit-export"
                )
            if verification.get("result") != "pass":
                errors.append("cross-file: audit-export-manifest.verification.result must be pass")
        signing = audit_export_manifest.get("signing")
        if isinstance(signing, dict) and signing.get("required") is not True:
            errors.append("cross-file: audit-export-manifest.signing.required must be true")
        generated_on = parse_example_date(audit_export_manifest.get("generatedOn"))
        retention = audit_export_manifest.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if generated_on is not None and review_on is not None and review_on <= generated_on:
                errors.append("cross-file: audit-export-manifest.retention.reviewOn must be after generatedOn")

    if isinstance(control_assessment_report, dict):
        if control_assessment_report.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: control-assessment-report.version must match currentVersion")
        scope = control_assessment_report.get("scope")
        if isinstance(scope, dict):
            if scope.get("architectureVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: control-assessment-report.scope.architectureVersion must match currentVersion")
            if scope.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: control-assessment-report.scope.controlCount must match control catalog length")
            if scope.get("controlCatalog") != str(CONTROL_CATALOG_PATH.relative_to(ROOT)):
                errors.append("cross-file: control-assessment-report.scope.controlCatalog must point to control catalog")
            if scope.get("evidenceMap") != "docs/references/modern-enterprise-architecture-kit/control-evidence-map.example.yaml":
                errors.append("cross-file: control-assessment-report.scope.evidenceMap must point to control evidence map example")
            if scope.get("auditExportManifest") != "docs/references/modern-enterprise-architecture-kit/audit-export-manifest.example.yaml":
                errors.append("cross-file: control-assessment-report.scope.auditExportManifest must point to audit export manifest example")
        summary = control_assessment_report.get("summary")
        control_results = control_assessment_report.get("controlResults")
        result_ids: list[str] = []
        pass_count = 0
        fail_count = 0
        if isinstance(control_results, list):
            for item in control_results:
                if not isinstance(item, dict):
                    continue
                control_id = item.get("id")
                if isinstance(control_id, str):
                    result_ids.append(control_id)
                status = item.get("status")
                if status == "pass":
                    pass_count += 1
                if status == "fail":
                    fail_count += 1
                evidence_items = item.get("evidence")
                if isinstance(evidence_items, list):
                    for evidence_path in evidence_items:
                        if isinstance(evidence_path, str) and not (ROOT / evidence_path).is_file():
                            errors.append("cross-file: control-assessment-report.controlResults.evidence must exist")
            if sorted(result_ids) != sorted(catalog_control_ids):
                errors.append("cross-file: control-assessment-report.controlResults must cover every control catalog id")
            if len(result_ids) != len(set(result_ids)):
                errors.append("cross-file: control-assessment-report.controlResults must not contain duplicate control ids")
        if isinstance(summary, dict):
            if summary.get("result") != "pass":
                errors.append("cross-file: control-assessment-report.summary.result must be pass")
            if summary.get("assessedControls") != len(catalog_control_ids):
                errors.append("cross-file: control-assessment-report.summary.assessedControls must match control catalog length")
            if summary.get("passedControls") != pass_count:
                errors.append("cross-file: control-assessment-report.summary.passedControls must match pass results")
            if summary.get("failedControls") != fail_count:
                errors.append("cross-file: control-assessment-report.summary.failedControls must match fail results")
            if summary.get("openFindings") != 0:
                errors.append("cross-file: control-assessment-report.summary.openFindings must be 0")
            if summary.get("blockingFindings") != 0:
                errors.append("cross-file: control-assessment-report.summary.blockingFindings must be 0")
        findings = control_assessment_report.get("findings")
        if isinstance(findings, list):
            for finding in findings:
                if not isinstance(finding, dict):
                    continue
                if finding.get("status") == "open":
                    errors.append("cross-file: control-assessment-report.findings.status must not be open")
                due_date = parse_example_date(finding.get("dueDate"))
                closed_on = parse_example_date(finding.get("closedOn"))
                if closed_on is not None and due_date is not None and closed_on > due_date:
                    errors.append("cross-file: control-assessment-report.findings.closedOn must be on or before dueDate")
        assessed_on = parse_example_date(control_assessment_report.get("assessedOn"))
        sign_off = control_assessment_report.get("signOff")
        if isinstance(sign_off, dict):
            if sign_off.get("status") != "approved":
                errors.append("cross-file: control-assessment-report.signOff.status must be approved")
            signed_on = parse_example_date(sign_off.get("signedOn"))
            next_assessment_on = parse_example_date(sign_off.get("nextAssessmentOn"))
            if assessed_on is not None and signed_on is not None and signed_on < assessed_on:
                errors.append("cross-file: control-assessment-report.signOff.signedOn must be on or after assessedOn")
            if signed_on is not None and next_assessment_on is not None and next_assessment_on <= signed_on:
                errors.append("cross-file: control-assessment-report.signOff.nextAssessmentOn must be after signedOn")

    if isinstance(baseline_change_record, dict):
        if baseline_change_record.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: baseline-change-record.version must match currentVersion")
        if baseline_change_record.get("changeLevel") != version_manifest.get("changeLevel"):
            errors.append("cross-file: baseline-change-record.changeLevel must match version manifest changeLevel")
        if baseline_change_record.get("status") != "implemented":
            errors.append("cross-file: baseline-change-record.status must be implemented")
        requested_on = parse_example_date(baseline_change_record.get("requestedOn"))
        approved_on = parse_example_date(baseline_change_record.get("approvedOn"))
        if requested_on is not None and approved_on is not None and approved_on < requested_on:
            errors.append("cross-file: baseline-change-record.approvedOn must be on or after requestedOn")
        scope = baseline_change_record.get("scope")
        if isinstance(scope, dict):
            if scope.get("architectureDocument") != version_manifest.get("architectureDocument"):
                errors.append("cross-file: baseline-change-record.scope.architectureDocument must match version manifest")
            if scope.get("versionManifest") != str(VERSION_MANIFEST_PATH.relative_to(ROOT)):
                errors.append("cross-file: baseline-change-record.scope.versionManifest must point to version manifest")
            if scope.get("controlCatalog") != str(CONTROL_CATALOG_PATH.relative_to(ROOT)):
                errors.append("cross-file: baseline-change-record.scope.controlCatalog must point to control catalog")
            if scope.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: baseline-change-record.scope.controlCount must match control catalog length")
            if scope.get("starterKitPairs") != len(PAIR_NAMES):
                errors.append("cross-file: baseline-change-record.scope.starterKitPairs must match starter kit pair count")
            changed_artifacts = scope.get("changedArtifacts")
            if isinstance(changed_artifacts, list):
                required_changed_artifacts = {
                    str(VERSION_MANIFEST_PATH.relative_to(ROOT)),
                    str(CONTROL_CATALOG_PATH.relative_to(ROOT)),
                    "docs/references/modern-enterprise-architecture-kit/baseline-change-record.schema.json",
                    "docs/references/modern-enterprise-architecture-kit/baseline-change-record.example.yaml",
                    "scripts/check-modern-architecture-kit.py",
                }
                artifact_set = {item for item in changed_artifacts if isinstance(item, str)}
                if not required_changed_artifacts.issubset(artifact_set):
                    errors.append("cross-file: baseline-change-record.scope.changedArtifacts must include required baseline artifacts")
                for artifact_path in artifact_set:
                    if not (ROOT / artifact_path).is_file():
                        errors.append("cross-file: baseline-change-record.scope.changedArtifacts must exist")
        validation = baseline_change_record.get("validation")
        if isinstance(validation, dict):
            if validation.get("result") != "pass":
                errors.append("cross-file: baseline-change-record.validation.result must be pass")
            commands = validation.get("commands")
            if isinstance(commands, list):
                required_commands = {
                    "make check-modern-architecture-kit",
                    "make check-modern-architecture-audit-export",
                    "make export-modern-architecture-audit",
                    "make test",
                }
                command_set = {item for item in commands if isinstance(item, str)}
                if not required_commands.issubset(command_set):
                    errors.append("cross-file: baseline-change-record.validation.commands must include required gates")
        rollback = baseline_change_record.get("rollback")
        if isinstance(rollback, dict):
            if rollback.get("supported") is not True:
                errors.append("cross-file: baseline-change-record.rollback.supported must be true")
            previous_commit = rollback.get("previousCommit")
            if not isinstance(previous_commit, str) or not re.fullmatch(r"[0-9a-f]{7,40}", previous_commit):
                errors.append("cross-file: baseline-change-record.rollback.previousCommit must be a git commit hash")
        approvals = baseline_change_record.get("approvals")
        if isinstance(approvals, list):
            roles = set()
            for approval in approvals:
                if not isinstance(approval, dict):
                    continue
                role = approval.get("role")
                if isinstance(role, str):
                    roles.add(role)
                if approval.get("status") != "approved":
                    errors.append("cross-file: baseline-change-record.approvals.status must be approved")
                approval_date = parse_example_date(approval.get("approvedOn"))
                if approved_on is not None and approval_date is not None and approval_date < approved_on:
                    errors.append("cross-file: baseline-change-record.approvals.approvedOn must be on or after approvedOn")
            required_roles = {"architecture-governance", "platform", "security"}
            if not required_roles.issubset(roles):
                errors.append("cross-file: baseline-change-record.approvals must include architecture-governance, platform and security")
        retention = baseline_change_record.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if approved_on is not None and review_on is not None and review_on <= approved_on:
                errors.append("cross-file: baseline-change-record.retention.reviewOn must be after approvedOn")

    if isinstance(oscal_export_profile, dict):
        if oscal_export_profile.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: oscal-export-profile.version must match currentVersion")
        target = oscal_export_profile.get("target")
        if isinstance(target, dict):
            if target.get("standard") != "NIST OSCAL":
                errors.append("cross-file: oscal-export-profile.target.standard must be NIST OSCAL")
            if target.get("machineReadable") is not True:
                errors.append("cross-file: oscal-export-profile.target.machineReadable must be true")
        source_artifacts = oscal_export_profile.get("sourceArtifacts")
        if isinstance(source_artifacts, dict):
            expected_sources = {
                "versionManifest": str(VERSION_MANIFEST_PATH.relative_to(ROOT)),
                "controlCatalog": str(CONTROL_CATALOG_PATH.relative_to(ROOT)),
                "controlEvidenceMap": "docs/references/modern-enterprise-architecture-kit/control-evidence-map.example.yaml",
                "auditExportManifest": "docs/references/modern-enterprise-architecture-kit/audit-export-manifest.example.yaml",
                "controlAssessmentReport": "docs/references/modern-enterprise-architecture-kit/control-assessment-report.example.yaml",
                "baselineChangeRecord": "docs/references/modern-enterprise-architecture-kit/baseline-change-record.example.yaml",
                "auditExportGate": "docs/references/modern-enterprise-architecture-kit/audit-export-gate.example.yaml",
                "auditExportIntegrity": "docs/references/modern-enterprise-architecture-kit/audit-export-integrity.example.yaml",
                "auditExportProvenance": "docs/references/modern-enterprise-architecture-kit/audit-export-provenance.example.yaml",
                "auditExportSigningPolicy": "docs/references/modern-enterprise-architecture-kit/audit-export-signing-policy.example.yaml",
                "auditExportSignatureReceipt": "docs/references/modern-enterprise-architecture-kit/audit-export-signature-receipt.example.yaml",
            }
            for key, expected_path in expected_sources.items():
                if source_artifacts.get(key) != expected_path:
                    errors.append(f"cross-file: oscal-export-profile.sourceArtifacts.{key} must point to {expected_path}")
                if not (ROOT / expected_path).is_file():
                    errors.append("cross-file: oscal-export-profile.sourceArtifacts paths must exist")
        model_mapping = oscal_export_profile.get("modelMapping")
        if isinstance(model_mapping, list):
            required_models = {
                "catalog",
                "component-definition",
                "system-security-plan",
                "assessment-results",
                "plan-of-action-and-milestones",
            }
            mapped_models = set()
            for item in model_mapping:
                if not isinstance(item, dict):
                    continue
                model = item.get("model")
                if isinstance(model, str):
                    mapped_models.add(model)
                if item.get("required") is not True:
                    errors.append("cross-file: oscal-export-profile.modelMapping.required must be true")
                source_path = item.get("source")
                if isinstance(source_path, str) and not (ROOT / source_path).is_file():
                    errors.append("cross-file: oscal-export-profile.modelMapping.source must exist")
            if mapped_models != required_models:
                errors.append("cross-file: oscal-export-profile.modelMapping must cover OSCAL catalog, component-definition, system-security-plan, assessment-results and POA&M")
        controls = oscal_export_profile.get("controls")
        if isinstance(controls, dict):
            if controls.get("count") != len(catalog_control_ids):
                errors.append("cross-file: oscal-export-profile.controls.count must match control catalog length")
            if controls.get("selectionSource") != str(CONTROL_CATALOG_PATH.relative_to(ROOT)):
                errors.append("cross-file: oscal-export-profile.controls.selectionSource must point to control catalog")
        assessment = oscal_export_profile.get("assessment")
        if isinstance(assessment, dict):
            assessment_summary = control_assessment_report.get("summary") if isinstance(control_assessment_report, dict) else {}
            if assessment.get("source") != "docs/references/modern-enterprise-architecture-kit/control-assessment-report.example.yaml":
                errors.append("cross-file: oscal-export-profile.assessment.source must point to control assessment report")
            if isinstance(assessment_summary, dict):
                if assessment.get("result") != assessment_summary.get("result"):
                    errors.append("cross-file: oscal-export-profile.assessment.result must match control assessment summary")
                if assessment.get("openFindings") != assessment_summary.get("openFindings"):
                    errors.append("cross-file: oscal-export-profile.assessment.openFindings must match control assessment summary")
                if assessment.get("poamRequired") != (assessment_summary.get("openFindings") != 0):
                    errors.append("cross-file: oscal-export-profile.assessment.poamRequired must match open findings")
        validation = oscal_export_profile.get("validation")
        if isinstance(validation, dict):
            if validation.get("command") != "make export-modern-architecture-audit":
                errors.append("cross-file: oscal-export-profile.validation.command must be make export-modern-architecture-audit")
            if validation.get("result") != "pass":
                errors.append("cross-file: oscal-export-profile.validation.result must be pass")
            if validation.get("output") != "build/modern-enterprise-architecture-audit/oscal-summary.json":
                errors.append("cross-file: oscal-export-profile.validation.output must be oscal-summary.json")
        generated_on = parse_example_date(oscal_export_profile.get("generatedOn"))
        retention = oscal_export_profile.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if generated_on is not None and review_on is not None and review_on <= generated_on:
                errors.append("cross-file: oscal-export-profile.retention.reviewOn must be after generatedOn")

    if isinstance(audit_export_gate, dict):
        if audit_export_gate.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: audit-export-gate.version must match currentVersion")
        command = audit_export_gate.get("command")
        if isinstance(command, dict):
            if command.get("local") != "make check-modern-architecture-audit-export":
                errors.append("cross-file: audit-export-gate.command.local must be make check-modern-architecture-audit-export")
            if command.get("export") != "make export-modern-architecture-audit":
                errors.append("cross-file: audit-export-gate.command.export must be make export-modern-architecture-audit")
            if command.get("preflight") != "make check-modern-architecture-kit":
                errors.append("cross-file: audit-export-gate.command.preflight must be make check-modern-architecture-kit")
        expectations = audit_export_gate.get("expectations")
        if isinstance(expectations, dict):
            if expectations.get("architectureVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: audit-export-gate.expectations.architectureVersion must match currentVersion")
            if expectations.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: audit-export-gate.expectations.controlCount must match control catalog length")
            if expectations.get("starterKitPairs") != len(PAIR_NAMES):
                errors.append("cross-file: audit-export-gate.expectations.starterKitPairs must match starter kit pair count")
            if expectations.get("verificationCommand") != "make check-modern-architecture-kit":
                errors.append(
                    "cross-file: audit-export-gate.expectations.verificationCommand must be make check-modern-architecture-kit"
                )
            if expectations.get("verificationResult") != "pass":
                errors.append("cross-file: audit-export-gate.expectations.verificationResult must be pass")
            if expectations.get("integrityManifestRequired") is not True:
                errors.append("cross-file: audit-export-gate.expectations.integrityManifestRequired must be true")
            if expectations.get("generatedOutputDigestsMatch") is not True:
                errors.append("cross-file: audit-export-gate.expectations.generatedOutputDigestsMatch must be true")
            if expectations.get("provenanceStatementRequired") is not True:
                errors.append("cross-file: audit-export-gate.expectations.provenanceStatementRequired must be true")
            if expectations.get("provenanceSubjectDigestsMatch") is not True:
                errors.append("cross-file: audit-export-gate.expectations.provenanceSubjectDigestsMatch must be true")
            if expectations.get("signingPolicyRequired") is not True:
                errors.append("cross-file: audit-export-gate.expectations.signingPolicyRequired must be true")
            if expectations.get("signingPayloadDigestMatches") is not True:
                errors.append("cross-file: audit-export-gate.expectations.signingPayloadDigestMatches must be true")
            if expectations.get("signatureReceiptRequired") is not True:
                errors.append("cross-file: audit-export-gate.expectations.signatureReceiptRequired must be true")
            if expectations.get("signatureReceiptExternal") is not True:
                errors.append("cross-file: audit-export-gate.expectations.signatureReceiptExternal must be true")
        outputs = audit_export_gate.get("outputs")
        if isinstance(outputs, list):
            output_paths = {item.get("path") for item in outputs if isinstance(item, dict) and isinstance(item.get("path"), str)}
            required_outputs = {
                "build/modern-enterprise-architecture-audit/audit-export.json",
                "build/modern-enterprise-architecture-audit/audit-export.md",
                "build/modern-enterprise-architecture-audit/oscal-summary.json",
                "build/modern-enterprise-architecture-audit/audit-export-integrity.json",
                "build/modern-enterprise-architecture-audit/audit-export-provenance.json",
                "build/modern-enterprise-architecture-audit/audit-export-signing-policy.json",
            }
            if not required_outputs.issubset(output_paths):
                errors.append(
                    "cross-file: audit-export-gate.outputs must include audit JSON, Markdown, OSCAL summary, integrity manifest, provenance statement and signing policy"
                )
            for item in outputs:
                if isinstance(item, dict) and item.get("required") is not True:
                    errors.append("cross-file: audit-export-gate.outputs.required must be true")
                    break
        quality_gate = audit_export_gate.get("qualityGate")
        if isinstance(quality_gate, dict):
            if quality_gate.get("requiredInMakeTest") is not True:
                errors.append("cross-file: audit-export-gate.qualityGate.requiredInMakeTest must be true")
            if quality_gate.get("zeroDependency") is not True:
                errors.append("cross-file: audit-export-gate.qualityGate.zeroDependency must be true")
        ci_integration = audit_export_gate.get("ciIntegration")
        if isinstance(ci_integration, dict):
            if ci_integration.get("localGate") != "make test":
                errors.append("cross-file: audit-export-gate.ciIntegration.localGate must be make test")
            if ci_integration.get("makefileTarget") != "check-modern-architecture-audit-export":
                errors.append(
                    "cross-file: audit-export-gate.ciIntegration.makefileTarget must be check-modern-architecture-audit-export"
                )
            if ci_integration.get("script") != str(AUDIT_EXPORT_GATE_SCRIPT_PATH.relative_to(ROOT)):
                errors.append("cross-file: audit-export-gate.ciIntegration.script must point to audit export gate script")
        generated_on = parse_example_date(audit_export_gate.get("generatedOn"))
        retention = audit_export_gate.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if generated_on is not None and review_on is not None and review_on <= generated_on:
                errors.append("cross-file: audit-export-gate.retention.reviewOn must be after generatedOn")

    if isinstance(audit_export_integrity, dict):
        if audit_export_integrity.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: audit-export-integrity.version must match currentVersion")
        scope = audit_export_integrity.get("scope")
        if isinstance(scope, dict):
            if scope.get("architectureVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: audit-export-integrity.scope.architectureVersion must match currentVersion")
            if scope.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: audit-export-integrity.scope.controlCount must match control catalog length")
            if scope.get("starterKitPairs") != len(PAIR_NAMES):
                errors.append("cross-file: audit-export-integrity.scope.starterKitPairs must match starter kit pair count")
        if audit_export_integrity.get("algorithm") != "sha256":
            errors.append("cross-file: audit-export-integrity.algorithm must be sha256")
        outputs = audit_export_integrity.get("outputs")
        if isinstance(outputs, list):
            output_paths = {item.get("path") for item in outputs if isinstance(item, dict) and isinstance(item.get("path"), str)}
            required_outputs = {
                "build/modern-enterprise-architecture-audit/audit-export.json",
                "build/modern-enterprise-architecture-audit/audit-export.md",
                "build/modern-enterprise-architecture-audit/oscal-summary.json",
            }
            if not required_outputs.issubset(output_paths):
                errors.append(
                    "cross-file: audit-export-integrity.outputs must include audit JSON, Markdown and OSCAL summary"
                )
            for item in outputs:
                if not isinstance(item, dict):
                    continue
                if item.get("required") is not True:
                    errors.append("cross-file: audit-export-integrity.outputs.required must be true")
                    break
                if item.get("digestRequired") is not True:
                    errors.append("cross-file: audit-export-integrity.outputs.digestRequired must be true")
                    break
        verification = audit_export_integrity.get("verification")
        if isinstance(verification, dict):
            if verification.get("command") != "make check-modern-architecture-audit-export":
                errors.append(
                    "cross-file: audit-export-integrity.verification.command must be make check-modern-architecture-audit-export"
                )
            if verification.get("result") != "pass":
                errors.append("cross-file: audit-export-integrity.verification.result must be pass")
            if verification.get("checker") != str(AUDIT_EXPORT_GATE_SCRIPT_PATH.relative_to(ROOT)):
                errors.append("cross-file: audit-export-integrity.verification.checker must point to audit export gate checker")
        tamper_evidence = audit_export_integrity.get("tamperEvidence")
        if isinstance(tamper_evidence, dict):
            if tamper_evidence.get("includesGeneratedOutputs") is not True:
                errors.append("cross-file: audit-export-integrity.tamperEvidence.includesGeneratedOutputs must be true")
            if tamper_evidence.get("includesSourceArtifacts") is not True:
                errors.append("cross-file: audit-export-integrity.tamperEvidence.includesSourceArtifacts must be true")
            if tamper_evidence.get("blocksOnMismatch") is not True:
                errors.append("cross-file: audit-export-integrity.tamperEvidence.blocksOnMismatch must be true")
        generated_on = parse_example_date(audit_export_integrity.get("generatedOn"))
        retention = audit_export_integrity.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if generated_on is not None and review_on is not None and review_on <= generated_on:
                errors.append("cross-file: audit-export-integrity.retention.reviewOn must be after generatedOn")

    if isinstance(audit_export_provenance, dict):
        if audit_export_provenance.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: audit-export-provenance.version must match currentVersion")
        scope = audit_export_provenance.get("scope")
        if isinstance(scope, dict):
            if scope.get("architectureVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: audit-export-provenance.scope.architectureVersion must match currentVersion")
            if scope.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: audit-export-provenance.scope.controlCount must match control catalog length")
            if scope.get("starterKitPairs") != len(PAIR_NAMES):
                errors.append("cross-file: audit-export-provenance.scope.starterKitPairs must match starter kit pair count")
        provenance_format = audit_export_provenance.get("format")
        if isinstance(provenance_format, dict):
            if provenance_format.get("statementType") != "https://in-toto.io/Statement/v1":
                errors.append("cross-file: audit-export-provenance.format.statementType must be in-toto Statement v1")
            if provenance_format.get("predicateType") != "https://slsa.dev/provenance/v1":
                errors.append("cross-file: audit-export-provenance.format.predicateType must be SLSA provenance v1")
        subjects = audit_export_provenance.get("subjects")
        if isinstance(subjects, list):
            subject_paths = {item.get("path") for item in subjects if isinstance(item, dict) and isinstance(item.get("path"), str)}
            required_subjects = {
                "build/modern-enterprise-architecture-audit/audit-export.json",
                "build/modern-enterprise-architecture-audit/audit-export.md",
                "build/modern-enterprise-architecture-audit/oscal-summary.json",
                "build/modern-enterprise-architecture-audit/audit-export-integrity.json",
            }
            if not required_subjects.issubset(subject_paths):
                errors.append(
                    "cross-file: audit-export-provenance.subjects must include audit JSON, Markdown, OSCAL summary and integrity manifest"
                )
            for item in subjects:
                if not isinstance(item, dict):
                    continue
                if item.get("required") is not True:
                    errors.append("cross-file: audit-export-provenance.subjects.required must be true")
                    break
                if item.get("digestAlgorithm") != "sha256":
                    errors.append("cross-file: audit-export-provenance.subjects.digestAlgorithm must be sha256")
                    break
        build_definition = audit_export_provenance.get("buildDefinition")
        if isinstance(build_definition, dict):
            if build_definition.get("buildType") != "https://github.com/tradecatlabs/vibe-coding-cn/modern-enterprise-architecture/audit-export@v2":
                errors.append("cross-file: audit-export-provenance.buildDefinition.buildType must identify audit export builder")
            if build_definition.get("exportCommand") != "make export-modern-architecture-audit":
                errors.append("cross-file: audit-export-provenance.buildDefinition.exportCommand must be make export-modern-architecture-audit")
            if build_definition.get("verificationCommand") != "make check-modern-architecture-audit-export":
                errors.append(
                    "cross-file: audit-export-provenance.buildDefinition.verificationCommand must be make check-modern-architecture-audit-export"
                )
            if build_definition.get("resolvedDependenciesRequired") is not True:
                errors.append("cross-file: audit-export-provenance.buildDefinition.resolvedDependenciesRequired must be true")
        run_details = audit_export_provenance.get("runDetails")
        if isinstance(run_details, dict):
            if run_details.get("builderId") != "vibe-coding-cn:scripts/export-modern-architecture-audit.py":
                errors.append("cross-file: audit-export-provenance.runDetails.builderId must identify exporter script")
            if run_details.get("sourceRepositoryRequired") is not True:
                errors.append("cross-file: audit-export-provenance.runDetails.sourceRepositoryRequired must be true")
            if run_details.get("sourceCommitRequired") is not True:
                errors.append("cross-file: audit-export-provenance.runDetails.sourceCommitRequired must be true")
        generated_on = parse_example_date(audit_export_provenance.get("generatedOn"))
        retention = audit_export_provenance.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if generated_on is not None and review_on is not None and review_on <= generated_on:
                errors.append("cross-file: audit-export-provenance.retention.reviewOn must be after generatedOn")

    if isinstance(audit_export_signing_policy, dict):
        if audit_export_signing_policy.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: audit-export-signing-policy.version must match currentVersion")
        scope = audit_export_signing_policy.get("scope")
        if isinstance(scope, dict):
            if scope.get("architectureVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: audit-export-signing-policy.scope.architectureVersion must match currentVersion")
            if scope.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: audit-export-signing-policy.scope.controlCount must match control catalog length")
            if scope.get("starterKitPairs") != len(PAIR_NAMES):
                errors.append("cross-file: audit-export-signing-policy.scope.starterKitPairs must match starter kit pair count")
        payload = audit_export_signing_policy.get("payload")
        if isinstance(payload, dict):
            if payload.get("path") != "build/modern-enterprise-architecture-audit/audit-export-provenance.json":
                errors.append("cross-file: audit-export-signing-policy.payload.path must point to audit-export-provenance.json")
            if payload.get("digestAlgorithm") != "sha256":
                errors.append("cross-file: audit-export-signing-policy.payload.digestAlgorithm must be sha256")
            if payload.get("predicateType") != "https://slsa.dev/provenance/v1":
                errors.append("cross-file: audit-export-signing-policy.payload.predicateType must be SLSA provenance v1")
        signature = audit_export_signing_policy.get("signature")
        if isinstance(signature, dict):
            if signature.get("required") is not True:
                errors.append("cross-file: audit-export-signing-policy.signature.required must be true")
            if signature.get("method") != "sigstore-cosign-or-enterprise-signing":
                errors.append("cross-file: audit-export-signing-policy.signature.method must be sigstore-cosign-or-enterprise-signing")
            if signature.get("transparencyLogRequired") is not True:
                errors.append("cross-file: audit-export-signing-policy.signature.transparencyLogRequired must be true")
        commands = audit_export_signing_policy.get("commands")
        if isinstance(commands, dict):
            sign_command = commands.get("sign")
            verify_command = commands.get("verify")
            if not isinstance(sign_command, str) or "cosign sign-blob --bundle" not in sign_command:
                errors.append("cross-file: audit-export-signing-policy.commands.sign must use cosign sign-blob --bundle")
            if not isinstance(verify_command, str) or "cosign verify-blob --bundle" not in verify_command:
                errors.append("cross-file: audit-export-signing-policy.commands.verify must use cosign verify-blob --bundle")
        local_gate = audit_export_signing_policy.get("localGate")
        if isinstance(local_gate, dict):
            if local_gate.get("verifiesPayloadDigest") is not True:
                errors.append("cross-file: audit-export-signing-policy.localGate.verifiesPayloadDigest must be true")
            if local_gate.get("doesNotForgeSignature") is not True:
                errors.append("cross-file: audit-export-signing-policy.localGate.doesNotForgeSignature must be true")
        generated_on = parse_example_date(audit_export_signing_policy.get("generatedOn"))
        retention = audit_export_signing_policy.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if generated_on is not None and review_on is not None and review_on <= generated_on:
                errors.append("cross-file: audit-export-signing-policy.retention.reviewOn must be after generatedOn")

    if isinstance(audit_export_signature_receipt, dict):
        if audit_export_signature_receipt.get("version") != version_manifest.get("currentVersion"):
            errors.append("cross-file: audit-export-signature-receipt.version must match currentVersion")
        scope = audit_export_signature_receipt.get("scope")
        if isinstance(scope, dict):
            if scope.get("architectureVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: audit-export-signature-receipt.scope.architectureVersion must match currentVersion")
            if scope.get("controlCount") != len(catalog_control_ids):
                errors.append("cross-file: audit-export-signature-receipt.scope.controlCount must match control catalog length")
            if scope.get("starterKitPairs") != len(PAIR_NAMES):
                errors.append("cross-file: audit-export-signature-receipt.scope.starterKitPairs must match starter kit pair count")
        policy_binding = audit_export_signature_receipt.get("policyBinding")
        if isinstance(policy_binding, dict):
            if policy_binding.get("signingPolicy") != "docs/references/modern-enterprise-architecture-kit/audit-export-signing-policy.example.yaml":
                errors.append("cross-file: audit-export-signature-receipt.policyBinding.signingPolicy must point to signing policy example")
            if policy_binding.get("signingPolicyVersion") != version_manifest.get("currentVersion"):
                errors.append("cross-file: audit-export-signature-receipt.policyBinding.signingPolicyVersion must match currentVersion")
            if policy_binding.get("signingPolicyStatus") != "external-signature-required":
                errors.append("cross-file: audit-export-signature-receipt.policyBinding.signingPolicyStatus must be external-signature-required")
        payload = audit_export_signature_receipt.get("payload")
        signing_payload = audit_export_signing_policy.get("payload") if isinstance(audit_export_signing_policy, dict) else {}
        if isinstance(payload, dict):
            if isinstance(signing_payload, dict) and payload.get("path") != signing_payload.get("path"):
                errors.append("cross-file: audit-export-signature-receipt.payload.path must match signing policy payload path")
            if payload.get("digestAlgorithm") != "sha256":
                errors.append("cross-file: audit-export-signature-receipt.payload.digestAlgorithm must be sha256")
            if payload.get("digestSource") != "build/modern-enterprise-architecture-audit/audit-export-signing-policy.json#/payload/sha256":
                errors.append("cross-file: audit-export-signature-receipt.payload.digestSource must point to generated signing policy payload sha256")
        signature = audit_export_signature_receipt.get("signature")
        signing_signature = audit_export_signing_policy.get("signature") if isinstance(audit_export_signing_policy, dict) else {}
        if isinstance(signature, dict):
            if isinstance(signing_signature, dict) and signature.get("method") != signing_signature.get("method"):
                errors.append("cross-file: audit-export-signature-receipt.signature.method must match signing policy method")
            if isinstance(signing_signature, dict) and signature.get("bundlePath") != signing_signature.get("bundlePath"):
                errors.append("cross-file: audit-export-signature-receipt.signature.bundlePath must match signing policy bundlePath")
            if isinstance(signing_signature, dict) and signature.get("oidcIssuer") != signing_signature.get("issuer"):
                errors.append("cross-file: audit-export-signature-receipt.signature.oidcIssuer must match signing policy issuer")
            if signature.get("transparencyLogRequired") is not True:
                errors.append("cross-file: audit-export-signature-receipt.signature.transparencyLogRequired must be true")
            if not isinstance(signature.get("transparencyLogEntries"), int) or signature.get("transparencyLogEntries") < 1:
                errors.append("cross-file: audit-export-signature-receipt.signature.transparencyLogEntries must be at least 1")
        verification = audit_export_signature_receipt.get("verification")
        if isinstance(verification, dict):
            verify_command = verification.get("command")
            if not isinstance(verify_command, str) or "cosign verify-blob --bundle" not in verify_command:
                errors.append("cross-file: audit-export-signature-receipt.verification.command must use cosign verify-blob --bundle")
            if verification.get("result") != "pass":
                errors.append("cross-file: audit-export-signature-receipt.verification.result must be pass")
            if verification.get("tool") != "cosign":
                errors.append("cross-file: audit-export-signature-receipt.verification.tool must be cosign")
            if verification.get("toolVersionRequired") is not True:
                errors.append("cross-file: audit-export-signature-receipt.verification.toolVersionRequired must be true")
        verified_on = parse_example_date(audit_export_signature_receipt.get("verifiedOn"))
        retention = audit_export_signature_receipt.get("retention")
        if isinstance(retention, dict):
            review_on = parse_example_date(retention.get("reviewOn"))
            if verified_on is not None and review_on is not None and review_on <= verified_on:
                errors.append("cross-file: audit-export-signature-receipt.retention.reviewOn must be after verifiedOn")

    return errors


def validate_pair(name: str) -> list[str]:
    errors: list[str] = []
    schema_path = KIT_DIR / f"{name}.schema.json"
    example_path = KIT_DIR / f"{name}.example.yaml"

    if not schema_path.is_file():
        return [f"{schema_path.relative_to(ROOT)}: missing schema"]
    if not example_path.is_file():
        return [f"{example_path.relative_to(ROOT)}: missing example"]

    try:
        schema = load_schema(schema_path)
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"{schema_path.relative_to(ROOT)}: invalid JSON schema: {exc}"]

    errors.extend(validate_schema_document(schema, schema_path))

    try:
        example = parse_yaml_example(example_path)
    except KitValidationError as exc:
        return [str(exc)]

    errors.extend(validate_instance(schema, example, str(example_path.relative_to(ROOT))))

    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_version_manifest())
    errors.extend(validate_audit_export_automation())

    for required_doc in ("README.md", "AGENTS.md"):
        path = KIT_DIR / required_doc
        if not path.is_file():
            errors.append(f"{path.relative_to(ROOT)}: missing required directory document")

    for name in PAIR_NAMES:
        errors.extend(validate_pair(name))

    if not errors:
        try:
            errors.extend(validate_cross_file_consistency(load_examples()))
        except KitValidationError as exc:
            errors.append(str(exc))
    if not errors:
        errors.extend(validate_audit_export_gate_runtime())

    discovered_schemas = {path.stem.removesuffix(".schema") for path in KIT_DIR.glob("*.schema.json")}
    unexpected = sorted(discovered_schemas - set(PAIR_NAMES))
    if unexpected:
        errors.append(f"{KIT_DIR.relative_to(ROOT)}: schemas missing from checker: {', '.join(unexpected)}")

    discovered_examples = {path.stem.removesuffix(".example") for path in KIT_DIR.glob("*.example.yaml")}
    unexpected_examples = sorted(discovered_examples - set(PAIR_NAMES))
    if unexpected_examples:
        errors.append(f"{KIT_DIR.relative_to(ROOT)}: examples missing from checker: {', '.join(unexpected_examples)}")

    if errors:
        print("MODERN_ARCHITECTURE_KIT_ERRORS")
        for error in errors:
            print(error)
        print(f"TOTAL={len(errors)}")
        return 1

    print(f"OK modern enterprise architecture kit checked: {len(PAIR_NAMES)} schema/example pairs and control catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
