# Data provenance — LiveBrowseComp

- **Upstream:** [Forival/LiveBrowseComp](https://huggingface.co/datasets/Forival/LiveBrowseComp)
  (Hugging Face dataset; 335 questions, idx 0–334), the eval set of
  *"LiveBrowseComp: Are Search Agents Searching, or Just Verifying What They
  Already Know?"* (Fan et al., 2026, [arXiv:2605.28721](https://arxiv.org/abs/2605.28721)).
- **License:** MIT (per the dataset card).
- **Snapshot:** `data/LiveBrowseComp.jsonl` was fetched on **2026-08-13** from
  revision `ee6b1bb971eba285823394a4162bdc104cefd73b` (dataset card
  `lastModified` 2026-05-28).
- **Encryption:** upstream encrypts `problem`/`answer` with the BrowseComp XOR
  scheme (SHA-256 of a canary string as key material, base64) to keep benchmark
  plaintext out of LLM training corpora. **This repo preserves that property:**
  only the encrypted JSONL is committed; `scripts/lbc_crypto.py` decrypts in
  memory at run time, decrypted artifacts are gitignored, and published files
  (`TASKS.md`, results) reference tasks by idx and SHA-256 content hashes only.
- Agent transcripts under `results/` may quote question text verbatim (the
  agents see decrypted questions). Raw transcripts are therefore kept out of
  the public repo or scrubbed before publication; published result files carry
  only final answers, verdicts, and metadata.
