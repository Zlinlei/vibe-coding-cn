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
    "data-product",
    "ai-product",
    "catalog-component",
    "production-readiness",
    "raci",
    "tiering-policy",
    "deprecation-policy",
    "audit-evidence-index",
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
    domain = examples.get("domain")
    service = examples.get("service")
    data_product = examples.get("data-product")
    catalog_component = examples.get("catalog-component")

    if isinstance(domain, dict) and isinstance(service, dict):
        if service.get("domain") != domain.get("domain"):
            errors.append("cross-file: service.domain must match domain.domain")
        if service.get("owner") != domain.get("owner"):
            errors.append("cross-file: service.owner must match domain.owner in starter kit examples")

    if isinstance(domain, dict) and isinstance(data_product, dict):
        if data_product.get("domain") != domain.get("domain"):
            errors.append("cross-file: data-product.domain must match domain.domain")
        if data_product.get("owner") != domain.get("owner"):
            errors.append("cross-file: data-product.owner must match domain.owner in starter kit examples")

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
