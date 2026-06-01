#!/usr/bin/env python3
"""Validate the modern enterprise architecture starter kit.

The repository intentionally avoids extra Python dependencies for quality
gates. This checker implements the small YAML and JSON Schema subset used by
the starter kit, then validates each example against its paired schema.
"""

from __future__ import annotations

import json
import sys
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
    errors: list[str] = []
    rel = schema_path.relative_to(ROOT)

    schema_type = schema.get("type")
    if schema_type != "object":
        errors.append(f"{rel}: root type must be object")

    required = schema.get("required")
    if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
        errors.append(f"{rel}: required must be a string array")

    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        errors.append(f"{rel}: properties must be an object")
        return errors

    if isinstance(required, list):
        missing_properties = sorted(set(required) - set(properties))
        if missing_properties:
            errors.append(f"{rel}: required fields missing from properties: {', '.join(missing_properties)}")

    for prop_name, prop_schema in properties.items():
        if not isinstance(prop_schema, dict):
            errors.append(f"{rel}: property '{prop_name}' schema must be an object")
            continue
        prop_type = prop_schema.get("type")
        if prop_type not in SCHEMA_TYPES:
            errors.append(f"{rel}: property '{prop_name}' has unsupported type '{prop_type}'")

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
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for item_index, item in enumerate(value):
                errors.extend(validate_instance(item_schema, item, f"{location}[{item_index}]"))

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
