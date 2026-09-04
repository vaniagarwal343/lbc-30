# Held-out task slice (LBC-30 extension, Amendment L)

15 tasks drawn from the 302 LiveBrowseComp questions NOT in the frozen 30
or the 3-task pilot, by the mechanical rule in `scripts/select_heldout.py`:
**same strata as the main selection (regex `\b202[56]\b` on the decrypted
problem: DATED/`recent` = 69 in pool, UNDATED/`older` = 233); within each
stratum sort by idx and take evenly strided picks — 8 DATED + 7 UNDATED
(step = floor(len/n), positions 0, step, ..., (n-1)*step).** Frozen and
committed before any held-out run.

Purpose: a slice no arm had seen when the Keenable extension was designed,
run for claude-exa, claude-builtin and claude-keenable (all model calls
via OpenRouter — CONFIG.md Amendment I/L). Codex arms optional.

Per upstream canary policy, no decrypted text is committed; the SHA-256
hashes commit to the exact decrypted content of each task.

| # | idx | stratum | problem sha256 (12) | answer sha256 (12) |
|---|-----|---------|---------------------|--------------------|
| 1 | 4 | older | `1b62545190d9` | `35100c96ac0a` |
| 2 | 12 | recent | `7c6d32444cbc` | `2dab5be80d16` |
| 3 | 39 | recent | `ba0cbc747ea7` | `4df91306cd1a` |
| 4 | 55 | older | `77dfeb6fbe91` | `f477aa39a7df` |
| 5 | 82 | recent | `d39e8830d36c` | `4f4f8f139378` |
| 6 | 102 | older | `3a6bd6f08334` | `0b32143c4660` |
| 7 | 116 | recent | `c96d8e6a70ca` | `e312f89515b6` |
| 8 | 146 | older | `2ef19db41fdf` | `ae81deb7013a` |
| 9 | 154 | recent | `19d992bd9275` | `fcfec56b61a1` |
| 10 | 193 | recent | `33ee861ba600` | `1cc4f2a4883e` |
| 11 | 197 | older | `00936d695385` | `ddad7cef2477` |
| 12 | 219 | recent | `e6a429a6c954` | `b3e2ac496feb` |
| 13 | 248 | older | `09976ebfabe6` | `fcc4d8d0a6c8` |
| 14 | 279 | recent | `0fe65007d5b3` | `92106ddedf99` |
| 15 | 292 | older | `6f02f248b493` | `a4010ec3476c` |

**Frozen held-out idx list (15):** 4, 12, 39, 55, 82, 102, 116, 146, 154, 193, 197, 219, 248, 279, 292

- DATED/recent (8): 12, 39, 82, 116, 154, 193, 219, 279
- UNDATED/older (7): 4, 55, 102, 146, 197, 248, 292
