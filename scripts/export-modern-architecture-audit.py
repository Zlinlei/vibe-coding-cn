#!/usr/bin/env python3
"""Export a deterministic audit packet for the modern architecture kit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts/check-modern-architecture-kit.py"
DEFAULT_OUT_DIR = ROOT / "build/modern-enterprise-architecture-audit"
REQUIRED_EXPORT_ARTIFACTS = [
    "docs/references/modern-enterprise-architecture-template.md",
    "docs/references/modern-enterprise-architecture-version.json",
    "docs/references/modern-enterprise-architecture-controls.json",
    "docs/references/modern-enterprise-architecture-kit/README.md",
    "docs/references/modern-enterprise-architecture-kit/control-evidence-map.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/audit-export-manifest.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/control-assessment-report.example.yaml",
    "scripts/check-modern-architecture-kit.py",
    "scripts/export-modern-architecture-audit.py",
]


def load_checker() -> Any:
    spec = importlib.util.spec_from_file_location("modern_architecture_checker", CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load checker from {CHECKER_PATH.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def collect_artifact(path_value: str) -> dict[str, Any]:
    path = ROOT / path_value
    if not path.is_file():
        raise FileNotFoundError(path_value)
    return {
        "path": path_value,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def build_packet(checker: Any) -> dict[str, Any]:
    validation_errors: list[str] = []
    validation_errors.extend(checker.validate_version_manifest())
    for name in checker.PAIR_NAMES:
        validation_errors.extend(checker.validate_pair(name))
    if not validation_errors:
        validation_errors.extend(checker.validate_cross_file_consistency(checker.load_examples()))
    if validation_errors:
        raise RuntimeError("modern architecture kit validation failed before export:\n" + "\n".join(validation_errors))

    version_manifest = checker.load_version_manifest()
    control_catalog = checker.load_control_catalog()
    examples = checker.load_examples()
    controls = control_catalog.get("controls", [])
    if not isinstance(controls, list):
        raise RuntimeError("control catalog controls must be an array")

    artifacts = [collect_artifact(path_value) for path_value in REQUIRED_EXPORT_ARTIFACTS]
    required_artifacts = []
    for control in controls:
        if not isinstance(control, dict):
            continue
        for path_value in control.get("requiredArtifacts", []):
            if isinstance(path_value, str):
                required_artifacts.append(path_value)
    for path_value in sorted(set(required_artifacts)):
        artifact = collect_artifact(path_value)
        if artifact not in artifacts:
            artifacts.append(artifact)

    return {
        "package": "modern-enterprise-architecture-audit-export",
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "version": version_manifest.get("currentVersion"),
        "status": version_manifest.get("status"),
        "summary": version_manifest.get("summary"),
        "starterKitPairs": len(checker.PAIR_NAMES),
        "controlCount": len(controls),
        "controls": [
            {
                "id": control.get("id"),
                "category": control.get("category"),
                "title": control.get("title"),
                "requiredArtifacts": control.get("requiredArtifacts", []),
            }
            for control in controls
            if isinstance(control, dict)
        ],
        "evidence": {
            "controlEvidenceMap": examples.get("control-evidence-map"),
            "auditExportManifest": examples.get("audit-export-manifest"),
            "controlAssessmentReport": examples.get("control-assessment-report"),
        },
        "artifacts": artifacts,
        "verification": {
            "command": "make check-modern-architecture-kit",
            "result": "pass",
            "checker": relative(CHECKER_PATH),
        },
    }


def write_json(packet: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(packet: dict[str, Any], path: Path) -> None:
    lines = [
        "# Modern Enterprise Architecture Audit Export",
        "",
        f"- Version: `{packet['version']}`",
        f"- Status: `{packet['status']}`",
        f"- Generated At: `{packet['generatedAt']}`",
        f"- Starter Kit Pairs: `{packet['starterKitPairs']}`",
        f"- Control Count: `{packet['controlCount']}`",
        f"- Verification: `{packet['verification']['command']}` -> `{packet['verification']['result']}`",
        "",
        "## Controls",
        "",
        "| Control | Category | Title |",
        "| ------- | -------- | ----- |",
    ]
    for control in packet["controls"]:
        lines.append(f"| `{control['id']}` | `{control['category']}` | {control['title']} |")
    lines.extend([
        "",
        "## Artifacts",
        "",
        "| Path | SHA-256 | Bytes |",
        "| ---- | ------- | ----- |",
    ])
    for artifact in packet["artifacts"]:
        lines.append(f"| `{artifact['path']}` | `{artifact['sha256']}` | `{artifact['bytes']}` |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export modern enterprise architecture audit packet")
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Output directory for audit-export.json and audit-export.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    checker = load_checker()
    packet = build_packet(checker)
    json_path = out_dir / "audit-export.json"
    markdown_path = out_dir / "audit-export.md"
    write_json(packet, json_path)
    write_markdown(packet, markdown_path)

    print(f"OK modern architecture audit export written: {relative(json_path)}")
    print(f"OK modern architecture audit report written: {relative(markdown_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
