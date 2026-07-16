#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build the tcga-lung casebank from public, de-identified TCGA-LUAD data.

This is a *recipe*, not data: it fetches real report text at run time and writes
cases into ``pack/casebank/cases/`` (which is gitignored). The raw TCGA text is
CC-BY-NC-ND, so it is never committed — only this script and the pack schema are.

Sources (public, de-identified):
  * Pathology report text + clinical fields: Lab-Rasool/TCGA on Hugging Face,
    via the datasets-server filter API (no bulk download, no embeddings).
  * Molecular alterations (best-effort enrichment): cBioPortal public API,
    study ``luad_tcga``.

Determinism: candidate cases are sorted by barcode and the first N that pass
validation (clean pathology text mentioning adenocarcinoma + a known stage) are
selected, so re-running builds the same pack from the same upstream data.

Ground truth is derived ONLY where the data determines it and the token is
verified present in the element that carries it; softer items are left empty for
physician adjudication via the review UI.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HF = "https://datasets-server.huggingface.co/filter"
DATASET = "Lab-Rasool/TCGA"
CASES_DIR = Path(__file__).parent / "pack" / "casebank" / "cases"
N_CASES = 8
DIAGNOSIS_TOKEN = "adenocarcinoma"
# Actionable lung-adenocarcinoma driver genes, with NCBI Entrez ids (cBioPortal
# requires an explicit gene list). Order = clinical priority for the "actionable
# alteration" the tumor board would name first.
ACTIONABLE_GENES = {
    "EGFR": 1956, "ALK": 238, "ROS1": 6098, "BRAF": 673,
    "KRAS": 3845, "MET": 4233, "ERBB2": 2064, "RET": 5979,
}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "tcga-lung-ingest"})
    last = None
    for attempt in range(5):  # tolerate transient upstream 5xx
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code < 500:
                raise
            for _ in range(attempt + 1):
                try:
                    urllib.request.urlopen("https://huggingface.co", timeout=10).read(1)
                except Exception:
                    pass
    raise last


def hf_filter(config: str, where: str, limit: int = 100, offset: int = 0) -> list[dict]:
    q = urllib.parse.urlencode({
        "dataset": DATASET, "config": config, "split": "gatortron",
        "where": where, "limit": limit, "offset": offset,
    })
    for _ in range(30):  # index may be warming up
        data = _get(f"{HF}?{q}")
        if "rows" in data:
            return [r["row"] for r in data["rows"]]
        if "error" in data and "loading" in data["error"].lower():
            _get("https://huggingface.co")  # latency spacer
            continue
        raise RuntimeError(f"HF filter error for {config}: {data.get('error')}")
    raise RuntimeError(f"HF filter index never became ready for {config}")


def _text(value) -> str:
    if isinstance(value, list):
        value = " ".join(str(v) for v in value)
    return (value or "").strip()


def _clinical_summary(c: dict) -> str:
    # Deliberately excludes the diagnosis wording so item_diagnosis evidence stays
    # unique to the pathology_report element (clean information-value curves).
    parts = ["Clinical summary (from TCGA structured data)."]
    site = c.get("tissue_or_organ_of_origin")
    if site:
        parts.append(f"Primary site: {site}.")
    stage = c.get("ajcc_pathologic_stage")
    if stage:
        t, n, m = c.get("ajcc_pathologic_t"), c.get("ajcc_pathologic_n"), c.get("ajcc_pathologic_m")
        tnm = " / ".join(x for x in [t, n, m] if x)
        parts.append(f"AJCC pathologic stage: {stage}." + (f" TNM: {tnm}." if tnm else ""))
    py = c.get("pack_years_smoked")
    if py:
        parts.append(f"Smoking history: {py} pack-years.")
    return " ".join(parts)


def fetch_molecular(barcode: str) -> list[str]:
    """Best-effort: somatic mutated genes for the primary tumor from cBioPortal."""
    sample = f"{barcode}-01"
    url = "https://www.cbioportal.org/api/molecular-profiles/luad_tcga_mutations/mutations/fetch?projection=DETAILED"
    body = json.dumps({"sampleIds": [sample],
                       "entrezGeneIds": list(ACTIONABLE_GENES.values())}).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": "tcga-lung-ingest"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            muts = json.loads(resp.read().decode())
    except Exception:
        return []
    genes = []
    for m in muts:
        g = (m.get("gene") or {}).get("hugoGeneSymbol")
        if g and g not in genes:
            genes.append(g)
    return genes


def build_case(barcode: str, clinical: dict, report: str) -> dict:
    elements = {"pathology_report": report, "clinical_summary": _clinical_summary(clinical)}
    ground_truth: dict = {}

    if DIAGNOSIS_TOKEN in report.lower():
        ground_truth["item_diagnosis"] = {"evidence": [DIAGNOSIS_TOKEN]}
    stage = clinical.get("ajcc_pathologic_stage")
    if stage:
        ground_truth["item_staging"] = {"evidence": [stage]}

    genes = fetch_molecular(barcode)
    if genes:
        actionable = [g for g in ACTIONABLE_GENES if g in genes]
        shown = (actionable or genes)[:6]
        elements["molecular_report"] = (
            "NGS panel (public TCGA / cBioPortal, luad_tcga). Somatic mutations "
            f"detected: {', '.join(shown)}."
        )
        marker = (actionable or shown)[0]
        ground_truth["item_molecular"] = {"evidence": [marker]}

    return {"case_id": barcode.replace("-", "_"), "elements": elements, "ground_truth": ground_truth}


def main() -> int:
    print("Fetching TCGA-LUAD clinical rows ...")
    clinical_rows = hf_filter("clinical", "\"project_id\"='TCGA-LUAD'", limit=100)
    by_barcode = {}
    for r in clinical_rows:
        bc = r.get("case_submitter_id")
        if bc and bc not in by_barcode and r.get("ajcc_pathologic_stage"):
            by_barcode[bc] = r

    selected = []
    for bc in sorted(by_barcode):
        if len(selected) >= N_CASES:
            break
        rows = hf_filter("pathology_report", f"\"PatientID\"='{bc}'", limit=1)
        if not rows:
            continue
        report = _text(rows[0].get("report_text"))
        if len(report) < 200 or DIAGNOSIS_TOKEN not in report.lower():
            continue
        selected.append((bc, by_barcode[bc], report))
        print(f"  selected {bc}  stage={by_barcode[bc].get('ajcc_pathologic_stage')}  (report {len(report)} chars)")

    if not selected:
        print("No cases selected — upstream API may be unavailable.", file=sys.stderr)
        return 1

    CASES_DIR.mkdir(parents=True, exist_ok=True)
    for existing in CASES_DIR.glob("*.json"):
        existing.unlink()
    for bc, clinical, report in selected:
        case = build_case(bc, clinical, report)
        (CASES_DIR / f"{case['case_id']}.json").write_text(
            json.dumps(case, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nWrote {len(selected)} cases to {CASES_DIR}")
    print("Selected barcodes:", ", ".join(bc for bc, _, _ in selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
