# Example validation dossiers

Consolidated validation dossiers the harness generates for a run — checked in so
they can be **reviewed directly in the repo/PR**, no external hosting.

| Model | Review (renders on GitHub) | Print |
|---|---|---|
| gemini-2.5-flash | [`dossier-gemini-2.5-flash.md`](dossier-gemini-2.5-flash.md) | `dossier-gemini-2.5-flash.html` |
| gemini-3.5-flash | [`dossier-gemini-3.5-flash.md`](dossier-gemini-3.5-flash.md) | `dossier-gemini-3.5-flash.html` |

- **Review:** open the `.md` — GitHub renders it inline (tables, status, info-value bars).
- **Print / save as PDF:** open the `.html` in a browser, Cmd/Ctrl-P (self-contained,
  print stylesheet included).
- The `.json` alongside is the structured record both are rendered from.

These snapshots are from real runs (`gemini-2.5-flash` / `gemini-3.5-flash` on the
`gemini_contract*` batteries, ablation; reference-aware `gemini-flash-lite-latest`
judge). **Aggregate-only** — rubric results, acceptance, input contract,
calibration, and the pinned-inputs attestation. No case text, barcodes, or keys.

**Regenerate** for any run:

```bash
GEMINI_API_KEY=... python run_gemini_contract.py [battery]   # produces a run
harness dossier pack --run <run_id> --out ./runs             # -> dossier.md + .html + .json
```

Both model versions show the same real finding: `pathology_report` information
value ≈ 0 — the model states the diagnosis even when that input is withheld
(inferring it from context); only `molecular_report` is strictly necessary. A
grounding/confabulation point worth a tumor-board discussion.

Signatures are unsigned drafts; signer roles are clinical (medical + quality
reviewer). Signing by anchoring to an immutable release is a prepared next step.
