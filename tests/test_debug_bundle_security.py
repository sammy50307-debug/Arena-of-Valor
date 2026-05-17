from __future__ import annotations

import json
from pathlib import Path

from analyzer.run_manifest import build_manifest, write_manifest
from scripts.debug_bundle import write_debug_bundle


def test_debug_bundle_does_not_embed_raw_content_or_unsafe_extra(tmp_path: Path):
    payload = 'RAW_SECRET_PAYLOAD_<script>alert("bundle")</script>'
    data_dir = tmp_path / "data"
    raw_path = data_dir / "raw_20260517.json"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(json.dumps([{"content": payload}], ensure_ascii=False), encoding="utf-8")

    manifest = build_manifest(
        run_date="2026-05-17",
        mode="production",
        raw_path=raw_path,
        analysis_path=data_dir / "analysis_20260517.json",
        report_path=data_dir / "reports" / "aov_report_2026-05-17.html",
    )
    manifest_path = write_manifest(data_dir, manifest)

    bundle_path = write_debug_bundle(
        data_dir=data_dir,
        repo_root=tmp_path,
        run_date="2026-05-17",
        status="failed",
        error="test",
        analysis_path=None,
        raw_path=raw_path,
        report_path=None,
        manifest_path=manifest_path,
        extra={
            "expected_mode": "any",
            "raw_content": payload,
            "nested": {"content": payload},
        },
    )

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    serialized = json.dumps(bundle, ensure_ascii=False)

    assert bundle["paths"]["raw"].endswith("raw_20260517.json")
    assert bundle["extra"] == {"expected_mode": "any"}
    assert payload not in serialized
    assert "raw_content" not in serialized
