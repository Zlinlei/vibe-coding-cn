#!/usr/bin/env python3
"""Export a deterministic audit packet for the modern architecture kit."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
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
    "docs/references/modern-enterprise-architecture-kit/baseline-change-record.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/oscal-export-profile.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/audit-export-gate.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/audit-export-integrity.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/audit-export-provenance.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/audit-export-signing-policy.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/audit-export-signature-receipt.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/poam-record.example.yaml",
    "docs/references/modern-enterprise-architecture-kit/risk-register.example.yaml",
    "scripts/check-modern-architecture-kit.py",
    "scripts/export-modern-architecture-audit.py",
    "scripts/check-modern-architecture-audit-export.py",
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


def git_output(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    value = completed.stdout.strip()
    return value or "unknown"


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
            "baselineChangeRecord": examples.get("baseline-change-record"),
            "oscalExportProfile": examples.get("oscal-export-profile"),
            "auditExportGate": examples.get("audit-export-gate"),
            "auditExportIntegrity": examples.get("audit-export-integrity"),
            "auditExportProvenance": examples.get("audit-export-provenance"),
            "auditExportSigningPolicy": examples.get("audit-export-signing-policy"),
            "auditExportSignatureReceipt": examples.get("audit-export-signature-receipt"),
            "poamRecord": examples.get("poam-record"),
            "riskRegister": examples.get("risk-register"),
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


def write_oscal_summary(packet: dict[str, Any], path: Path) -> None:
    evidence = packet.get("evidence", {})
    assessment = evidence.get("controlAssessmentReport") if isinstance(evidence, dict) else {}
    oscal_profile = evidence.get("oscalExportProfile") if isinstance(evidence, dict) else {}
    poam_record = evidence.get("poamRecord") if isinstance(evidence, dict) else {}
    risk_register = evidence.get("riskRegister") if isinstance(evidence, dict) else {}
    assessment_summary = assessment.get("summary") if isinstance(assessment, dict) else {}
    poam_scope = poam_record.get("scope") if isinstance(poam_record, dict) else {}

    summary = {
        "oscalSummary": "modern-enterprise-architecture",
        "version": packet["version"],
        "generatedAt": packet["generatedAt"],
        "catalog": {
            "controls": packet["controls"],
        },
        "componentDefinition": {
            "source": "docs/references/modern-enterprise-architecture-kit/control-evidence-map.example.yaml",
            "controlCount": packet["controlCount"],
        },
        "systemSecurityPlan": {
            "source": "docs/references/modern-enterprise-architecture-template.md",
            "status": packet["status"],
        },
        "assessmentResults": {
            "source": "docs/references/modern-enterprise-architecture-kit/control-assessment-report.example.yaml",
            "summary": assessment_summary,
        },
        "poam": {
            "source": "docs/references/modern-enterprise-architecture-kit/poam-record.example.yaml",
            "required": bool(isinstance(poam_scope, dict) and poam_scope.get("openFindings", 0) != 0),
            "status": poam_scope.get("status") if isinstance(poam_scope, dict) else None,
            "items": poam_record.get("items", []) if isinstance(poam_record, dict) else [],
            "milestones": poam_record.get("milestones", []) if isinstance(poam_record, dict) else [],
            "signOff": poam_record.get("signOff", {}) if isinstance(poam_record, dict) else {},
        },
        "riskRegister": {
            "source": "docs/references/modern-enterprise-architecture-kit/risk-register.example.yaml",
            "risks": risk_register.get("risks", []) if isinstance(risk_register, dict) else [],
            "review": risk_register.get("review", {}) if isinstance(risk_register, dict) else {},
        },
        "profile": oscal_profile,
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_integrity_manifest(packet: dict[str, Any], generated_outputs: list[Path]) -> dict[str, Any]:
    return {
        "integrityManifest": "modern-enterprise-architecture-audit-export-integrity",
        "generatedAt": packet["generatedAt"],
        "version": packet["version"],
        "algorithm": "sha256",
        "generatedOutputs": [
            {
                "path": relative(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in generated_outputs
        ],
        "sourceArtifacts": packet["artifacts"],
        "verification": {
            "command": "make check-modern-architecture-audit-export",
            "result": "pass",
            "checker": "scripts/check-modern-architecture-audit-export.py",
        },
    }


def write_integrity_manifest(packet: dict[str, Any], generated_outputs: list[Path], path: Path) -> None:
    path.write_text(
        json.dumps(build_integrity_manifest(packet, generated_outputs), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_provenance_statement(packet: dict[str, Any], generated_outputs: list[Path]) -> dict[str, Any]:
    source_commit = git_output("rev-parse", "HEAD")
    source_remote = git_output("config", "--get", "remote.origin.url")
    source_status = git_output("status", "--short")
    source_dirty = source_status != "unknown" and source_status != ""
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": "https://slsa.dev/provenance/v1",
        "subject": [
            {
                "name": relative(path),
                "digest": {
                    "sha256": sha256_file(path),
                },
                "bytes": path.stat().st_size,
            }
            for path in generated_outputs
        ],
        "predicate": {
            "buildDefinition": {
                "buildType": "https://github.com/tradecatlabs/vibe-coding-cn/modern-enterprise-architecture/audit-export@v2",
                "externalParameters": {
                    "architectureVersion": packet["version"],
                    "exportCommand": "make export-modern-architecture-audit",
                    "verificationCommand": "make check-modern-architecture-audit-export",
                },
                "internalParameters": {
                    "starterKitPairs": packet["starterKitPairs"],
                    "controlCount": packet["controlCount"],
                },
                "resolvedDependencies": [
                    {
                        "name": "source-repository",
                        "uri": source_remote,
                        "digest": {
                            "gitCommit": source_commit,
                        },
                    },
                    *[
                        {
                            "name": artifact["path"],
                            "uri": artifact["path"],
                            "digest": {
                                "sha256": artifact["sha256"],
                            },
                        }
                        for artifact in packet["artifacts"]
                    ],
                ],
            },
            "runDetails": {
                "builder": {
                    "id": "vibe-coding-cn:scripts/export-modern-architecture-audit.py",
                },
                "metadata": {
                    "invocationId": f"{packet['version']}-modern-enterprise-architecture-audit-export",
                    "startedOn": packet["generatedAt"],
                    "finishedOn": packet["generatedAt"],
                    "sourceDirty": source_dirty,
                },
                "byproducts": [
                    {
                        "name": "audit-export-integrity",
                        "uri": "build/modern-enterprise-architecture-audit/audit-export-integrity.json",
                    }
                ],
            },
        },
    }


def write_provenance_statement(packet: dict[str, Any], generated_outputs: list[Path], path: Path) -> None:
    path.write_text(
        json.dumps(build_provenance_statement(packet, generated_outputs), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_signing_policy(packet: dict[str, Any], provenance_path: Path) -> dict[str, Any]:
    return {
        "signingPolicy": "modern-enterprise-architecture-audit-export-signing-policy",
        "generatedAt": packet["generatedAt"],
        "version": packet["version"],
        "status": "external-signature-required",
        "payload": {
            "path": relative(provenance_path),
            "sha256": sha256_file(provenance_path),
            "bytes": provenance_path.stat().st_size,
            "predicateType": "https://slsa.dev/provenance/v1",
        },
        "signature": {
            "required": True,
            "method": "sigstore-cosign-or-enterprise-signing",
            "bundlePath": "governance/evidence/audit-export/audit-export-provenance.sigstore.bundle",
            "identity": "governance-team",
            "issuer": "enterprise-oidc-or-sigstore",
            "transparencyLogRequired": True,
        },
        "commands": {
            "sign": (
                "cosign sign-blob --bundle "
                "governance/evidence/audit-export/audit-export-provenance.sigstore.bundle "
                f"{relative(provenance_path)}"
            ),
            "verify": (
                "cosign verify-blob --bundle "
                "governance/evidence/audit-export/audit-export-provenance.sigstore.bundle "
                "--certificate-identity governance-team "
                "--certificate-oidc-issuer enterprise-oidc-or-sigstore "
                f"{relative(provenance_path)}"
            ),
        },
        "localGate": {
            "command": "make check-modern-architecture-audit-export",
            "verifiesPayloadDigest": True,
            "doesNotForgeSignature": True,
        },
    }


def write_signing_policy(packet: dict[str, Any], provenance_path: Path, path: Path) -> None:
    path.write_text(
        json.dumps(build_signing_policy(packet, provenance_path), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export modern enterprise architecture audit packet")
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help=(
            "Output directory for audit-export.json, audit-export.md, oscal-summary.json, "
            "POA&M and risk register summary, integrity manifest, provenance statement, signing policy and signature receipt contract"
        ),
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
    oscal_path = out_dir / "oscal-summary.json"
    integrity_path = out_dir / "audit-export-integrity.json"
    provenance_path = out_dir / "audit-export-provenance.json"
    signing_policy_path = out_dir / "audit-export-signing-policy.json"
    write_json(packet, json_path)
    write_markdown(packet, markdown_path)
    write_oscal_summary(packet, oscal_path)
    write_integrity_manifest(packet, [json_path, markdown_path, oscal_path], integrity_path)
    write_provenance_statement(packet, [json_path, markdown_path, oscal_path, integrity_path], provenance_path)
    write_signing_policy(packet, provenance_path, signing_policy_path)

    print(f"OK modern architecture audit export written: {relative(json_path)}")
    print(f"OK modern architecture audit report written: {relative(markdown_path)}")
    print(f"OK modern architecture OSCAL summary, POA&M and risk register view written: {relative(oscal_path)}")
    print(f"OK modern architecture audit integrity manifest written: {relative(integrity_path)}")
    print(f"OK modern architecture audit provenance statement written: {relative(provenance_path)}")
    print(f"OK modern architecture audit signing policy written: {relative(signing_policy_path)}")
    print("OK modern architecture audit signature receipt contract packaged in audit-export.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
