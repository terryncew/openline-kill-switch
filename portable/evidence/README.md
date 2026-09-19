# Portability evidence — provenance

Byte-for-byte copies of the frozen KILL-SWITCH-PORTABILITY-001 records
(study directory: `~/workspace/kill-switch-portability-001/` on the
author's machine; the study is sealed and unchanged since 2026-09-19).

| File | Source | sha256 |
|---|---|---|
| `CONTRACT.md` | frozen minimum gate contract (sealed before Implementation B existed) | `d0832fa6b8abcfbf25b81d433b5d9626482e58a539aaa4122b425641fa097863` |
| `PREREGISTRATION.md` | frozen acceptance criteria | `799c96192f0ab024758d350da02f383bdad2c0e8aed5b686b46b4c18a0cd3a83` |
| `PRECONTACT_SEAL.md` | seal record | `8b3fb6557efbbd44331808b54226127225288ff3b04765d86d36bc1f7cef480e` |
| `RESULTS.md` | full portability results | `0b379907a59b421b32ffdd9597f9e57ac99ccf1ce1db314d53a55dc9a029da2f` |
| `impl-b-evidence.jsonl` | Implementation B deterministic evidence bundle (73 records) | `bace02a6f08f4f15b780096ead4b5e76e3281873492e57924dbfe75ac5622be4` |
| `impl-b-race-evidence.jsonl` | Implementation B race evidence (60 records; winners nondeterministic by design) | `f461a2bd7fb8a8c962daf677fcda5b7b8003db5e334dc8b087ac2b1f33c6e526` |
| `impl-b-auditor-appraisal.txt` | output of the study's separate auditor run against these exact copies | — |

Verify with `sha256sum -c SHA256SUMS.txt` from this directory.

`impl-b-auditor-appraisal.txt` was produced by running the study's
`auditor.py` (also published in `../impl-b/`) against the copies in this
directory — the same verification the study performed, re-derived here so
the claim in this repository points at inspectable bytes, not at the
author's word.
