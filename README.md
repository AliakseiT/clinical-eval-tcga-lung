# clinical-eval-tcga-lung

An **example project repo produced by the Harness Factory** — a real-data
demonstration for a lung-adenocarcinoma molecular tumor board. The whole repo is
the example; the documents *inside* it (under `records/`) are stored exactly as
they would be in a real deployment, not as "examples".

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

## Real-model results (Google Gemini)

Run against real Gemini models via the OpenAI-compatible endpoint (needs
`GEMINI_API_KEY`; grading by a pinned, reference-aware `gemini-flash-lite-latest`
judge). Two runnable scripts:

```bash
GEMINI_API_KEY=... python run_gemini_eval.py       # validate + compare two models
GEMINI_API_KEY=... python run_gemini_contract.py   # input contract on a real model
```

**Validation + version comparison** (`gemini_compare`, 8 baseline cases):

| Model | mean score | acceptance |
|---|---|---|
| gemini-2.5-flash | 1.00 | PASS |
| gemini-3.5-flash | 1.00 | PASS |

RegressionDiff `2.5-flash → 3.5-flash` (a new model version): **no regression**
(Δ 0.00, 0 item regressions / 0 improvements). Real finding: on this extraction
task the new version is **at parity** — safe to upgrade with no measured loss.
(A model version swap is a *change event* → a QMS change request is emitted, not
a monitoring "trend".) Note: LLM judging is non-deterministic, so an occasional
transient `judge_error` occurs; it is recorded distinctly and **excluded** from
scores and the override projection (never counted as a failure).

**Input contract on the real model** (`gemini_contract`, gemini-2.5-flash,
ablation): information value — `pathology_report` **0.00**, `clinical_summary`
0.04, `molecular_report` **0.21**; minimal sufficient set = **`molecular_report`
only**. Real finding worth discussing with clinicians: the model still states the
diagnosis and stage *even when those inputs are withheld* (it infers them from
context) — only the specific molecular driver genuinely requires its input. This
is the opposite of the fake-model contract above, and surfaces a grounding /
confabulation question the tumor board should weigh.

**Monitoring, honestly:** M5 is already complete as an engine capability. A real
validation run is **not** production telemetry, so `run_gemini_eval.py` prints a
clearly-labelled *projection* of the override rate you would expect if the weaker
model were deployed (modelled from its measured error) — the *shape* of signal
M5 consumes, never a claim of real monitoring.

## De-identification recall (ingestion boundary)

The ingestion boundary pseudonymizes source text before it reaches the engine
(lightweight Presidio: small spaCy model + regex + clinical/Swiss recognizers,
reversible `encrypt`, key from env — no HF/transformer models). Its redaction is
*measured*, not assumed:

```bash
python run_deid_eval.py     # -> records/verification_validation/deid-recall-evaluation.md
```

It injects synthetic PHI into the real TCGA-LUAD notes and reports **per-PHI-type
leakage-recall** before/after the clinical recognizers, plus **clinical-signal
retention** (does EGFR/KRAS/stage survive?). On this config: overall **86% →
100%** (the lift is the Swiss AHV: 0% → 100%), retention **100%**.

**Read the caveat in the record:** this is an *upper bound* on synthetic
injections in a header slot — organic clinical PHI is harder, and TCGA is already
de-identified, so it is not ground-truth real-note recall (that needs
gold-annotated data such as i2b2/n2c2, DUA-gated). The value is establishing the
boundary + a per-type, measured, reproducible record; a higher-recall domain NER
(OpenMed) is the next step only if the measured gap justifies it.

### Enforced ingestion exists in the engine — but is not exercised here

The engine ships an **enforced ingestion boundary** (`harness ingest`): raw case →
pseudonymize → casebank, with structured-field PII classes
(`identifier` / `free_text` / `non_phi`) and a fail-closed residual gate that
refuses to write a case if a declared identifier survives anywhere in it. Re-id
material is kept hospital-side, never in the store.

**That path is deliberately not run in this demo.** TCGA-LUAD is *already
de-identified* and has **no structured identifier field** (no MRN, name, or
accession element) — so the identifier-capture → scrub → fail-closed flow has
nothing to act on here. Exercising it would only show NER on free text, which the
recall record above already measures directly. The enforcement is tested in the
engine (unit + live end-to-end); this repo simply doesn't have the input shape
that would make it meaningful.

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
