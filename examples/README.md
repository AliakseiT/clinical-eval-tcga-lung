# Example validation dossier

`dossier-gemini-2.5-flash.html` is a **consolidated validation dossier** — a
self-contained, printable HTML report the harness generates for one run. This
snapshot is from a real `gemini-2.5-flash` run on the TCGA-LUAD pack
(`gemini_contract` battery, ablation), judged by a reference-aware
`gemini-flash-lite-latest` judge.

**To view:** open the `.html` file in a browser. **To print / save as PDF:**
Cmd/Ctrl-P (a print stylesheet is included). It is fully self-contained (no
external resources).

**It is aggregate-only** — rubric results, acceptance, the input contract
(information value per element), calibration status, and the pinned-inputs
attestation. No case text, no barcodes, no keys. That is what makes it safe to
share (and, in future, to anchor to an immutable release).

**Regenerate it** for any run:

```bash
GEMINI_API_KEY=... python run_gemini_contract.py     # produces a run
harness dossier pack --run <run_id> --out ./runs     # -> runs/runs/<id>/qms/dossier.html
```

The `.json` alongside is the structured record the HTML is rendered from.

Snapshot notes: this is one real run (LLM judging is non-deterministic, so numbers
can vary slightly between runs). The interesting finding in this snapshot: on the
real model the `pathology_report` information value is ~0 — the model still states
the diagnosis when that input is withheld (inferring it from context), so only
`molecular_report` is strictly necessary. A grounding/confabulation point worth a
tumor-board discussion.
