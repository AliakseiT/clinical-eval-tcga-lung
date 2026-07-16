# clinical-eval-tcga-lung

An **example project repo produced by the Harness Factory** — a toy, real-data
evaluation pack for a lung-adenocarcinoma molecular tumor board, meant for
showing clinicians what the harness measures.

It follows the factory's two-repo model: the **engine** ([harness-factory](https://github.com/AliakseiT/clinical-llm-eval-engine))
is use-case-agnostic; this **project repo** holds one intended use — a pack, an
ingestion recipe, and (locally) its run outputs. It was scaffolded with
`harness new`, then the synthetic pack was swapped for the TCGA one.

## Data provenance & license — why the data is not in this repo

The cases are built from **public, de-identified TCGA lung adenocarcinoma (LUAD)**:

- **Pathology report text + clinical fields** — [`Lab-Rasool/TCGA`](https://huggingface.co/datasets/Lab-Rasool/TCGA)
  on Hugging Face (built on [TCGA-Reports](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10935496/), Kefeli et al., *Cell Patterns* 2024).
- **Molecular alterations** — [cBioPortal](https://www.cbioportal.org/) public API, study `luad_tcga`.

That text is **CC-BY-NC-ND 4.0**, so it is **never committed here**. Only the
*recipe* (`ingest_tcga_lung.py`) and the pack schema/rubric are versioned; running
the recipe rebuilds the identical casebank locally (cases are gitignored). This
also mirrors the product's rule: real case content is project data, not shared.

## Build & run

```bash
pip install harness-factory            # the engine (or: pip install -e ../factory)
python ingest_tcga_lung.py             # fetches ~8 LUAD cases -> pack/casebank/cases/ (gitignored)

harness lint pack
harness run pack --battery smoke --out ./runs --seed 1
# open runs/runs/<run_id>/contract.json  -> the input contract, measured on real data
harness ui  pack --out ./runs           # adjudicate cases / calibrate (needs the [ui] extra)
```

## What this demonstrates (two distinct beats — keep them separate)

1. **The instrument, on real inputs.** With the deterministic *fake* model + fake
   judge, `harness run` extracts the **input contract** and information-value
   curves on real LUAD reports: pathology carries the diagnosis, the clinical
   summary carries the stage, the molecular report carries the driver. This shows
   *what the harness measures* — it is **not** validating a model.
2. **The validation beat.** A clinician blind-**adjudicates** cases in the review
   UI (that becomes the gold), then you point a **real model** at an
   OpenAI-compatible endpoint (`suts.yaml`) and get a signed validation report +
   regression diff against the physician's standard. ("You set the truth; the
   harness measures the model against it.")

## Honest notes for the conversation

- **8 LUAD cases**; the molecular driver (EGFR/KRAS/BRAF/ERBB2 …) is present in
  ~5 of 8 — real MTB data where not every case has an actionable alteration in
  the panel. Cases without it leave `item_molecular` **unadjudicated**, for the
  physician to fill — which is exactly the point.
- Ground truth is derived **only where the data determines it and the token is
  verified present** (diagnosis from the pathology text; AJCC stage from the
  structured record; the driver gene from cBioPortal). Softer judgements are left
  to adjudication, not fabricated.
- Pathology text is real OCR from TCGA PDFs — occasionally noisy; some reports
  were machine-translated at source.

FOR DEMONSTRATION AND DISCUSSION WITH CLINICIANS — not a clinical device.
AGPL-3.0-or-later (this repo's code); the TCGA data it fetches is CC-BY-NC-ND 4.0.
