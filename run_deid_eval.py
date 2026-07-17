#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""De-identification recall record for the TCGA-LUAD ingestion config.

Injects synthetic PHI into the real (already-de-identified) TCGA-LUAD pathology
notes and measures how much the lightweight Presidio pseudonymizer redacts, per
PHI type, with and without the clinical/Swiss recognizers — the before/after
recall lift. Also checks clinical signal (EGFR/KRAS/…) survives.

Offline & deterministic (local Presidio, deterministic encrypt); no API key.
Writes a validation record under records/. HONEST: this is an upper bound on
synthetic injections, not ground-truth real-note recall (see the record).
"""

from __future__ import annotations

import json
from pathlib import Path

from harness.ingest.deid_eval import PhiItem, measure_deid, render_deid_md

ROOT = Path(__file__).parent
CASES = ROOT / "pack" / "casebank" / "cases"
OUT = ROOT / "records" / "verification_validation"

# Fixed synthetic PHI (the gold that must be redacted). Swiss-flavoured.
PHI = [
    PhiItem("PERSON", "Erika Mustermann"),
    PhiItem("PERSON", "Dr. Hans Meier"),
    PhiItem("CH_AHV", "756.1234.5678.90"),
    PhiItem("MEDICAL_RECORD_NUMBER", "MRN 7654321"),
    PhiItem("EMAIL_ADDRESS", "erika.mustermann@example.ch"),
    PhiItem("DATE_TIME", "2026-03-14"),
    PhiItem("LOCATION", "Winterthur"),
]
# Clinical signal that must SURVIVE pseudonymization (utility axis).
UTILITY = ["EGFR", "KRAS", "BRAF", "adenocarcinoma", "Stage"]


def _notes() -> list[str]:
    texts = []
    for f in sorted(CASES.glob("*.json")):
        c = json.loads(f.read_text())
        t = c.get("elements", {}).get("pathology_report")
        if t:
            texts.append(t)
    return texts


def main() -> int:
    import os
    os.environ.setdefault("HARNESS_REID_KEY", "demo-reid-key-01")  # throwaway demo AES key
    from harness.ingest.presidio_backend import PresidioPseudonymizer

    notes = _notes()
    if not notes:
        print("No cases — run ingest_tcga_lung.py first."); return 1

    reports = {}
    for clinical in (False, True):
        p = PresidioPseudonymizer(clinical=clinical)
        reports[clinical] = measure_deid(
            p, notes, PHI, UTILITY,
            config={"backend": "presidio", "model": "en_core_web_sm",
                    "clinical_recognizers": clinical, "n_phi_types": len({x.entity_type for x in PHI})},
        )

    base, clin = reports[False], reports[True]
    print("=== de-id recall (synthetic injections; UPPER BOUND) ===")
    print(f"  overall recall: baseline {base['overall_recall']:.0%} -> +clinical {clin['overall_recall']:.0%}")
    print(f"  clinical-signal retention (+clinical): {clin['utility_retention']:.0%}")
    for t in sorted(clin["per_type_recall"]):
        b = base["per_type_recall"][t]["recall"]; c = clin["per_type_recall"][t]["recall"]
        print(f"    {t:24} {b:.0%} -> {c:.0%}")

    OUT.mkdir(parents=True, exist_ok=True)
    md = ["# De-identification validation record — tcga-lung ingestion", "",
          "> **DRAFT — unsigned.** Signer roles: medical_reviewer, quality_reviewer.",
          "",
          "Before/after the clinical/Swiss recognizers, on synthetic PHI injected into "
          "the real TCGA-LUAD notes.", "",
          "## Baseline (Presidio defaults)", "", render_deid_md(base),
          "## With clinical + Swiss recognizers", "", render_deid_md(clin)]
    (OUT / "deid-recall-evaluation.md").write_text("\n".join(md), encoding="utf-8")
    (OUT / "deid-recall-evaluation.json").write_text(
        json.dumps({"baseline": base, "with_clinical": clin}, indent=2, sort_keys=True))
    print(f"\n  record: {OUT / 'deid-recall-evaluation.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
