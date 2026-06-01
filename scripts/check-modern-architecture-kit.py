#!/usr/bin/env python3
"""Validate the modern enterprise architecture starter kit.

The repository intentionally avoids extra Python dependencies for quality
gates. This checker implements the small YAML and JSON Schema subset used by
the starter kit, then validates each example against its paired schema.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KIT_DIR = ROOT / "docs/references/modern-enterprise-architecture-kit"
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
]
SCHEMA_TYPES = {"object", "array", "string", "number", "integer", "boolean", "null"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"


class KitValidationError(ValueError):
    """Raised when a starter kit example cannot be parsed or validated."""


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
    if schema_format is not None and schema_format != "date":
        errors.append(f"{location}: unsupported format '{schema_format}'")

    for numeric_key in ("minLength", "minItems"):
        if numeric_key in schema and (
            not isinstance(schema[numeric_key], int) or isinstance(schema[numeric_key], bool) or schema[numeric_key] < 0
        ):
            errors.append(f"{location}: {numeric_key} must be a non-negative integer")

    return errors


def is_iso_date(value: str) -> bool:
    if not DATE_PATTERN.match(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


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

    if isinstance(domain, dict) and isinstance(service, dict):
        if service.get("domain") != domain.get("domain"):
            errors.append("cross-file: service.domain must match domain.domain")
        if service.get("owner") != domain.get("owner"):
            errors.append("cross-file: service.owner must match domain.owner in starter kit examples")

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

    if isinstance(data_product, dict) and isinstance(catalog_data_product, dict):
        if catalog_data_product.get("name") != data_product.get("dataProduct"):
            errors.append("cross-file: catalog-data-product.name must match data-product.dataProduct")
        if catalog_data_product.get("domain") != data_product.get("domain"):
            errors.append("cross-file: catalog-data-product.domain must match data-product.domain")
        if catalog_data_product.get("owner") != data_product.get("owner"):
            errors.append("cross-file: catalog-data-product.owner must match data-product.owner")

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
        service_runtime = service.get("runtime")
        deployment_image = gitops_deployment.get("image")
        if isinstance(service_runtime, dict) and isinstance(deployment_image, dict):
            if deployment_image.get("repository") != service_runtime.get("imageRepository"):
                errors.append("cross-file: gitops-deployment.image.repository must match service.runtime.imageRepository")

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
        if isinstance(tools, list):
            registered_tools = [item.get("tool") for item in tools if isinstance(item, dict)]
        if ai_tool_contract.get("tool") not in registered_tools:
            errors.append("cross-file: ai-tool-contract.tool must be listed in ai-product.tools")

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

    if isinstance(service, dict) and isinstance(scorecard, dict):
        if scorecard.get("subject") != service.get("service"):
            errors.append("cross-file: scorecard.subject must match service.service")
        if scorecard.get("owner") != service.get("owner"):
            errors.append("cross-file: scorecard.owner must match service.owner")
        if scorecard.get("lifecycle") != service.get("lifecycle"):
            errors.append("cross-file: scorecard.lifecycle must match service.lifecycle")

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

    print(f"OK modern enterprise architecture kit checked: {len(PAIR_NAMES)} schema/example pairs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
