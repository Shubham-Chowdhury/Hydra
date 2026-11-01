# Synthetic Demonstration Data Registry

This directory documents the boundary and provenance of Hydra's synthetic demonstration catalogue.

## 1. Strict Demarcation

Hydra maintains a strict architectural separation between:
1. **Synthetic Demonstration Catalogues**:
   - Explicitly labelled with `is_synthetic: True`.
   - Dataset label: `SYNTHETIC_DEMO_CATALOG_NOT_OFFICIAL`.
   - Provenance record: `SYNTHETIC_DEMO_RECORD_V1`.
   - Use fictional institutions (e.g., *Demo Institute of Technology, Bengaluru*, *Apex Institute of Science and Technology, Hyderabad*).
   - Used exclusively for testing the symbolic reasoning engine, frame inheritance, AST evaluation, and UI interactions.

2. **Official Admissions Knowledge Base**:
   - Governed by Phase 3 data provenance protocols.
   - Requires verified source documents, immutable SHA-256 checksums, and dataset snapshots.
   - Uses published official institution names, counselling rounds, quotas, seat categories, and rank bases.
   - Explicitly records whether data was directly retrieved from authoritative government portals or derived from published fixtures.

3. **Historical Cutoff Observations vs. Eligibility**:
   - Historical opening and closing ranks represent observed allocation boundaries from previous counselling cycles.
   - They **never** constitute mandatory eligibility prerequisites or guarantees of future admission.
   - They are never merged into the student eligibility AST.

