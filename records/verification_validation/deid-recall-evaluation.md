# De-identification validation record — tcga-lung ingestion

> **DRAFT — unsigned.** Signer roles: medical_reviewer, quality_reviewer.

Before/after the clinical/Swiss recognizers, on synthetic PHI injected into the real TCGA-LUAD notes.

## Baseline (Presidio defaults)

# De-identification recall evaluation

*config `1a1e08a9083a69e7` · 8 notes*

> **Upper bound, not real-note recall.** Synthetic PHI injected into de-identified notes; leakage-recall = fraction of injected values absent from the pseudonymized output, per PHI type. UPPER BOUND (synthetic-in-slot is easier than organic PHI; TCGA is already de-identified). Ground-truth real-note recall needs gold-annotated data (i2b2/n2c2, DUA-gated). 'Absent' is a leakage proxy, not span-level detection.

**Overall leakage-recall: 86%**
 · clinical-signal retention: 100% (n=15)

| PHI type | n | leakage-recall |
| --- | --- | --- |
| CH_AHV | 8 | 0% |
| DATE_TIME | 8 | 100% |
| EMAIL_ADDRESS | 8 | 100% |
| LOCATION | 8 | 100% |
| MEDICAL_RECORD_NUMBER | 8 | 100% |
| PERSON | 16 | 100% |

_Config:_ backend=presidio, model=en_core_web_sm, clinical_recognizers=False, n_phi_types=6

## With clinical + Swiss recognizers

# De-identification recall evaluation

*config `1fe696d4a192d68e` · 8 notes*

> **Upper bound, not real-note recall.** Synthetic PHI injected into de-identified notes; leakage-recall = fraction of injected values absent from the pseudonymized output, per PHI type. UPPER BOUND (synthetic-in-slot is easier than organic PHI; TCGA is already de-identified). Ground-truth real-note recall needs gold-annotated data (i2b2/n2c2, DUA-gated). 'Absent' is a leakage proxy, not span-level detection.

**Overall leakage-recall: 100%**
 · clinical-signal retention: 100% (n=15)

| PHI type | n | leakage-recall |
| --- | --- | --- |
| CH_AHV | 8 | 100% |
| DATE_TIME | 8 | 100% |
| EMAIL_ADDRESS | 8 | 100% |
| LOCATION | 8 | 100% |
| MEDICAL_RECORD_NUMBER | 8 | 100% |
| PERSON | 16 | 100% |

_Config:_ backend=presidio, model=en_core_web_sm, clinical_recognizers=True, n_phi_types=6
