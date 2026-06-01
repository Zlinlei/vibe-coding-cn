#!/usr/bin/env python3
"""Validate generated audit export output invariants.

This gate intentionally reuses the repository-local starter kit checker and
exporter instead of adding runtime dependencies. It proves that the audit
packet can be generated and that the generated JSON/OSCAL summaries agree with
the version manifest, control catalog, and audit-export-gate contract.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "scripts/check-modern-architecture-kit.py"
EXPORTER_PATH = ROOT / "scripts/export-modern-architecture-audit.py"
DEFAULT_OUT_DIR = ROOT / "build/modern-enterprise-architecture-audit"


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


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


def validate_integrity_manifest(
    integrity: dict[str, Any],
    packet: dict[str, Any],
    generated_outputs: list[Path],
) -> list[str]:
    errors: list[str] = []
    if integrity.get("integrityManifest") != "modern-enterprise-architecture-audit-export-integrity":
        errors.append("audit-export-integrity.json integrityManifest must be modern-enterprise-architecture-audit-export-integrity")
    if integrity.get("version") != packet.get("version"):
        errors.append("audit-export-integrity.json version must match audit-export.json version")
    if integrity.get("algorithm") != "sha256":
        errors.append("audit-export-integrity.json algorithm must be sha256")

    generated_entries = integrity.get("generatedOutputs")
    if not isinstance(generated_entries, list):
        errors.append("audit-export-integrity.json generatedOutputs must be an array")
        generated_entries = []
    entries_by_path = {entry.get("path"): entry for entry in generated_entries if isinstance(entry, dict)}
    for path in generated_outputs:
        path_value = relative(path)
        entry = entries_by_path.get(path_value)
        if not isinstance(entry, dict):
            errors.append(f"audit-export-integrity.json generatedOutputs must include {path_value}")
            continue
        if entry.get("sha256") != sha256_file(path):
            errors.append(f"audit-export-integrity.json generatedOutputs sha256 mismatch for {path_value}")
        if entry.get("bytes") != path.stat().st_size:
            errors.append(f"audit-export-integrity.json generatedOutputs bytes mismatch for {path_value}")

    source_artifacts = integrity.get("sourceArtifacts")
    if source_artifacts != packet.get("artifacts"):
        errors.append("audit-export-integrity.json sourceArtifacts must match audit-export.json artifacts")

    verification = integrity.get("verification")
    if not isinstance(verification, dict):
        errors.append("audit-export-integrity.json verification must be an object")
    else:
        if verification.get("command") != "make check-modern-architecture-audit-export":
            errors.append(
                "audit-export-integrity.json verification.command must be make check-modern-architecture-audit-export"
            )
        if verification.get("result") != "pass":
            errors.append("audit-export-integrity.json verification.result must be pass")
        if verification.get("checker") != "scripts/check-modern-architecture-audit-export.py":
            errors.append("audit-export-integrity.json verification.checker must point to audit export checker")
    return errors


def validate_provenance_statement(
    provenance: dict[str, Any],
    packet: dict[str, Any],
    generated_outputs: list[Path],
) -> list[str]:
    errors: list[str] = []
    if provenance.get("_type") != "https://in-toto.io/Statement/v1":
        errors.append("audit-export-provenance.json _type must be https://in-toto.io/Statement/v1")
    if provenance.get("predicateType") != "https://slsa.dev/provenance/v1":
        errors.append("audit-export-provenance.json predicateType must be https://slsa.dev/provenance/v1")

    subjects = provenance.get("subject")
    if not isinstance(subjects, list):
        errors.append("audit-export-provenance.json subject must be an array")
        subjects = []
    subjects_by_name = {item.get("name"): item for item in subjects if isinstance(item, dict)}
    for path in generated_outputs:
        path_value = relative(path)
        subject = subjects_by_name.get(path_value)
        if not isinstance(subject, dict):
            errors.append(f"audit-export-provenance.json subject must include {path_value}")
            continue
        digest = subject.get("digest")
        if not isinstance(digest, dict) or digest.get("sha256") != sha256_file(path):
            errors.append(f"audit-export-provenance.json subject sha256 mismatch for {path_value}")
        if subject.get("bytes") != path.stat().st_size:
            errors.append(f"audit-export-provenance.json subject bytes mismatch for {path_value}")

    predicate = provenance.get("predicate")
    if not isinstance(predicate, dict):
        errors.append("audit-export-provenance.json predicate must be an object")
        return errors
    build_definition = predicate.get("buildDefinition")
    if not isinstance(build_definition, dict):
        errors.append("audit-export-provenance.json predicate.buildDefinition must be an object")
        build_definition = {}
    if build_definition.get("buildType") != "https://github.com/tradecatlabs/vibe-coding-cn/modern-enterprise-architecture/audit-export@v2":
        errors.append("audit-export-provenance.json buildDefinition.buildType must identify audit export builder")
    external = build_definition.get("externalParameters")
    if not isinstance(external, dict):
        errors.append("audit-export-provenance.json buildDefinition.externalParameters must be an object")
        external = {}
    if external.get("architectureVersion") != packet.get("version"):
        errors.append("audit-export-provenance.json externalParameters.architectureVersion must match audit-export.json version")
    if external.get("exportCommand") != "make export-modern-architecture-audit":
        errors.append("audit-export-provenance.json externalParameters.exportCommand must be make export-modern-architecture-audit")
    if external.get("verificationCommand") != "make check-modern-architecture-audit-export":
        errors.append(
            "audit-export-provenance.json externalParameters.verificationCommand must be make check-modern-architecture-audit-export"
        )
    internal = build_definition.get("internalParameters")
    if not isinstance(internal, dict):
        errors.append("audit-export-provenance.json buildDefinition.internalParameters must be an object")
        internal = {}
    if internal.get("starterKitPairs") != packet.get("starterKitPairs"):
        errors.append("audit-export-provenance.json internalParameters.starterKitPairs must match audit-export.json")
    if internal.get("controlCount") != packet.get("controlCount"):
        errors.append("audit-export-provenance.json internalParameters.controlCount must match audit-export.json")

    dependencies = build_definition.get("resolvedDependencies")
    if not isinstance(dependencies, list):
        errors.append("audit-export-provenance.json buildDefinition.resolvedDependencies must be an array")
        dependencies = []
    dependency_names = {item.get("name") for item in dependencies if isinstance(item, dict)}
    if "source-repository" not in dependency_names:
        errors.append("audit-export-provenance.json resolvedDependencies must include source-repository")
    artifact_paths = {item.get("path") for item in packet.get("artifacts", []) if isinstance(item, dict)}
    if not artifact_paths.issubset(dependency_names):
        errors.append("audit-export-provenance.json resolvedDependencies must include every audit-export artifact")

    run_details = predicate.get("runDetails")
    if not isinstance(run_details, dict):
        errors.append("audit-export-provenance.json predicate.runDetails must be an object")
        return errors
    builder = run_details.get("builder")
    if not isinstance(builder, dict) or builder.get("id") != "vibe-coding-cn:scripts/export-modern-architecture-audit.py":
        errors.append("audit-export-provenance.json runDetails.builder.id must identify exporter script")
    metadata = run_details.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("audit-export-provenance.json runDetails.metadata must be an object")
    elif metadata.get("invocationId") != f"{packet.get('version')}-modern-enterprise-architecture-audit-export":
        errors.append("audit-export-provenance.json runDetails.metadata.invocationId must include architecture version")
    return errors


def validate_packet(
    packet: dict[str, Any],
    oscal: dict[str, Any],
    checker: Any,
    integrity: dict[str, Any] | None = None,
    generated_outputs: list[Path] | None = None,
    provenance: dict[str, Any] | None = None,
    provenance_outputs: list[Path] | None = None,
) -> list[str]:
    errors: list[str] = []
    version_manifest = checker.load_version_manifest()
    control_catalog = checker.load_control_catalog()
    examples = checker.load_examples()
    controls = control_catalog.get("controls")
    if not isinstance(controls, list):
        controls = []

    expected_version = version_manifest.get("currentVersion")
    expected_pair_count = len(checker.PAIR_NAMES)
    expected_control_count = len(controls)

    if packet.get("package") != "modern-enterprise-architecture-audit-export":
        errors.append("audit-export.json package must be modern-enterprise-architecture-audit-export")
    if packet.get("version") != expected_version:
        errors.append("audit-export.json version must match currentVersion")
    if packet.get("starterKitPairs") != expected_pair_count:
        errors.append("audit-export.json starterKitPairs must match checker PAIR_NAMES")
    if packet.get("controlCount") != expected_control_count:
        errors.append("audit-export.json controlCount must match control catalog length")

    verification = packet.get("verification")
    if not isinstance(verification, dict):
        errors.append("audit-export.json verification must be an object")
    else:
        if verification.get("command") != "make check-modern-architecture-kit":
            errors.append("audit-export.json verification.command must be make check-modern-architecture-kit")
        if verification.get("result") != "pass":
            errors.append("audit-export.json verification.result must be pass")

    artifacts = packet.get("artifacts")
    artifact_paths = {item.get("path") for item in artifacts if isinstance(item, dict)} if isinstance(artifacts, list) else set()
    required_artifacts = {
        "docs/references/modern-enterprise-architecture-kit/audit-export-gate.example.yaml",
        "docs/references/modern-enterprise-architecture-kit/audit-export-integrity.example.yaml",
        "docs/references/modern-enterprise-architecture-kit/audit-export-provenance.example.yaml",
        "scripts/check-modern-architecture-audit-export.py",
    }
    if not required_artifacts.issubset(artifact_paths):
        errors.append("audit-export.json artifacts must include audit export gate contract and checker")

    evidence = packet.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("audit-export.json evidence must be an object")
    else:
        audit_export_gate = evidence.get("auditExportGate")
        if audit_export_gate != examples.get("audit-export-gate"):
            errors.append("audit-export.json evidence.auditExportGate must match starter kit example")
        if isinstance(audit_export_gate, dict):
            expectations = audit_export_gate.get("expectations")
            if isinstance(expectations, dict):
                if expectations.get("architectureVersion") != expected_version:
                    errors.append("auditExportGate expectations architectureVersion must match currentVersion")
                if expectations.get("starterKitPairs") != expected_pair_count:
                    errors.append("auditExportGate expectations starterKitPairs must match pair count")
                if expectations.get("controlCount") != expected_control_count:
                    errors.append("auditExportGate expectations controlCount must match control catalog length")
            quality_gate = audit_export_gate.get("qualityGate")
            if isinstance(quality_gate, dict) and quality_gate.get("requiredInMakeTest") is not True:
                errors.append("auditExportGate qualityGate.requiredInMakeTest must be true")
            outputs = audit_export_gate.get("outputs")
            if isinstance(outputs, list):
                output_paths = {item.get("path") for item in outputs if isinstance(item, dict)}
                if "build/modern-enterprise-architecture-audit/audit-export-integrity.json" not in output_paths:
                    errors.append("auditExportGate outputs must include audit-export-integrity.json")
                if "build/modern-enterprise-architecture-audit/audit-export-provenance.json" not in output_paths:
                    errors.append("auditExportGate outputs must include audit-export-provenance.json")
            expectations = audit_export_gate.get("expectations")
            if isinstance(expectations, dict):
                if expectations.get("integrityManifestRequired") is not True:
                    errors.append("auditExportGate expectations.integrityManifestRequired must be true")
                if expectations.get("generatedOutputDigestsMatch") is not True:
                    errors.append("auditExportGate expectations.generatedOutputDigestsMatch must be true")
                if expectations.get("provenanceStatementRequired") is not True:
                    errors.append("auditExportGate expectations.provenanceStatementRequired must be true")
                if expectations.get("provenanceSubjectDigestsMatch") is not True:
                    errors.append("auditExportGate expectations.provenanceSubjectDigestsMatch must be true")
        audit_export_provenance = evidence.get("auditExportProvenance")
        if audit_export_provenance != examples.get("audit-export-provenance"):
            errors.append("audit-export.json evidence.auditExportProvenance must match starter kit example")

    if oscal.get("version") != expected_version:
        errors.append("oscal-summary.json version must match currentVersion")
    catalog = oscal.get("catalog")
    oscal_controls = catalog.get("controls") if isinstance(catalog, dict) else None
    if not isinstance(oscal_controls, list) or len(oscal_controls) != expected_control_count:
        errors.append("oscal-summary.json catalog.controls must match control catalog length")
    component_definition = oscal.get("componentDefinition")
    if isinstance(component_definition, dict) and component_definition.get("controlCount") != expected_control_count:
        errors.append("oscal-summary.json componentDefinition.controlCount must match control catalog length")
    profile = oscal.get("profile")
    if not isinstance(profile, dict) or profile.get("version") != expected_version:
        errors.append("oscal-summary.json profile.version must match currentVersion")

    assessment = examples.get("control-assessment-report")
    assessment_summary = assessment.get("summary") if isinstance(assessment, dict) else {}
    poam = oscal.get("poam")
    if isinstance(poam, dict) and isinstance(assessment_summary, dict):
        expected_poam_required = assessment_summary.get("openFindings") != 0
        if poam.get("required") != expected_poam_required:
            errors.append("oscal-summary.json poam.required must follow openFindings")

    if integrity is None or generated_outputs is None:
        errors.append("audit-export-integrity.json must be generated and validated")
    else:
        errors.extend(validate_integrity_manifest(integrity, packet, generated_outputs))
    if provenance is None or provenance_outputs is None:
        errors.append("audit-export-provenance.json must be generated and validated")
    else:
        errors.extend(validate_provenance_statement(provenance, packet, provenance_outputs))

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check modern architecture audit export output")
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUT_DIR),
        help="Output directory for audit-export.json, audit-export.md, oscal-summary.json and provenance outputs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    checker = load_module(CHECKER_PATH, "modern_architecture_checker")
    exporter = load_module(EXPORTER_PATH, "modern_architecture_audit_exporter")
    packet = exporter.build_packet(checker)

    json_path = out_dir / "audit-export.json"
    markdown_path = out_dir / "audit-export.md"
    oscal_path = out_dir / "oscal-summary.json"
    integrity_path = out_dir / "audit-export-integrity.json"
    provenance_path = out_dir / "audit-export-provenance.json"
    exporter.write_json(packet, json_path)
    exporter.write_markdown(packet, markdown_path)
    exporter.write_oscal_summary(packet, oscal_path)
    exporter.write_integrity_manifest(packet, [json_path, markdown_path, oscal_path], integrity_path)
    exporter.write_provenance_statement(packet, [json_path, markdown_path, oscal_path, integrity_path], provenance_path)

    loaded_packet = load_json(json_path)
    loaded_oscal = load_json(oscal_path)
    loaded_integrity = load_json(integrity_path)
    loaded_provenance = load_json(provenance_path)
    errors = validate_packet(
        loaded_packet,
        loaded_oscal,
        checker,
        loaded_integrity,
        [json_path, markdown_path, oscal_path],
        loaded_provenance,
        [json_path, markdown_path, oscal_path, integrity_path],
    )
    if errors:
        print("MODERN_ARCHITECTURE_AUDIT_EXPORT_ERRORS")
        for error in errors:
            print(error)
        print(f"TOTAL={len(errors)}")
        return 1

    version = loaded_packet.get("version")
    pair_count = loaded_packet.get("starterKitPairs")
    control_count = loaded_packet.get("controlCount")
    print(
        "OK modern architecture audit export gate checked: "
        f"{version}, {pair_count} schema/example pairs, {control_count} controls, integrity and provenance"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
