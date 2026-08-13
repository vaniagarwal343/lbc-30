# Frozen task set (LBC-30)

Selected from LiveBrowseComp (335 questions, idx 0-334) by the
mechanical rule in `scripts/select_tasks.py`: **stratify by whether the
decrypted problem text mentions 2025/2026 (regex `\b202[56]\b`) into
RECENT (85 tasks) and OLDER (250 tasks); within each stratum sort by idx
and take 15 evenly strided picks (positions 0, step, ..., 14*step,
step = floor(len/15))**. Frozen and published before any agent run.

Note: per the LiveBrowseComp paper, all 335 questions are post-cutoff
by construction; the strata separate explicitly-dated phrasing from
obfuscated/undated phrasing, not pre- vs post-cutoff knowledge
(CONFIG.md §1 caveat).

Per upstream canary policy, no decrypted problem or answer text is
committed anywhere in this repo; the SHA-256 hashes below commit to the
exact decrypted content of each selected task.

| # | idx | stratum | problem sha256 (12) | answer sha256 (12) |
|---|-----|---------|---------------------|--------------------|
| 1 | 0 | older | `b115d23ce319` | `091ad410c950` |
| 2 | 1 | recent | `12d4c20291d9` | `58380d168456` |
| 3 | 19 | older | `24fa763d2ed0` | `2f9fcea981fa` |
| 4 | 26 | recent | `9ccafa20fd47` | `23540fb2a8c1` |
| 5 | 34 | recent | `7d0e0a80ec6e` | `6dee19da7993` |
| 6 | 45 | recent | `292266bbc705` | `68d4bb40f706` |
| 7 | 49 | older | `f0b3ec3dd9ab` | `9d6652e2c569` |
| 8 | 68 | older | `9e8d0260f4fb` | `629ceb7e09ab` |
| 9 | 72 | recent | `d5bf761de4e1` | `82853e979087` |
| 10 | 88 | recent | `f5102fb8a5c8` | `a406f642553e` |
| 11 | 90 | older | `aea29c38f7bf` | `5738fe0e2b0c` |
| 12 | 110 | older | `5766d0ab773c` | `f9fbcf0d9a88` |
| 13 | 111 | recent | `2c63b3ffedce` | `84941747b2c9` |
| 14 | 130 | older | `ddab82e99d2e` | `8c0e7cf27d47` |
| 15 | 133 | recent | `74b31b6dcce9` | `ca77513d8a7e` |
| 16 | 152 | recent | `0ac756df270d` | `6c94e35ccc35` |
| 17 | 156 | older | `5598bad4d85e` | `01c6451bdcb2` |
| 18 | 158 | recent | `c30b24aceded` | `dfd661cee3dd` |
| 19 | 178 | recent | `9b1b5155b25e` | `e98ca234f4a5` |
| 20 | 180 | older | `f4f6149fc395` | `2949a22b97b1` |
| 21 | 198 | older | `d7406cda9872` | `9f165139a8c2` |
| 22 | 203 | recent | `e8a49cf5520c` | `3d88af78cf71` |
| 23 | 213 | recent | `363658a3e159` | `0ced08614a2e` |
| 24 | 225 | older | `523ced5c332e` | `a78f19952edd` |
| 25 | 232 | recent | `074d2d240dd9` | `39bbf6f3c741` |
| 26 | 244 | older | `2726bb97104f` | `bd43b822ce30` |
| 27 | 262 | older | `a599df246575` | `a2bcfc025e52` |
| 28 | 270 | recent | `d7a1386a61ba` | `07229b11229b` |
| 29 | 283 | older | `4abf26f604db` | `a74028a6f96c` |
| 30 | 307 | older | `1b6bf2d11294` | `1bd47f8f0524` |

**Frozen idx list (30):** 0, 1, 19, 26, 34, 45, 49, 68, 72, 88, 90, 110, 111, 130, 133, 152, 156, 158, 178, 180, 198, 203, 213, 225, 232, 244, 262, 270, 283, 307

- RECENT (15): 1, 26, 34, 45, 72, 88, 111, 133, 152, 158, 178, 203, 213, 232, 270
- OLDER (15): 0, 19, 49, 68, 90, 110, 130, 156, 180, 198, 225, 244, 262, 283, 307

## Pilot tasks (never in headline tables — CONFIG.md §8)

Lowest-idx not-selected task in RECENT plus the two lowest-idx
not-selected tasks in OLDER (zero overlap with the frozen 30):

- idx 2 (older) — problem sha256 `c1ac5031283a`
- idx 3 (older) — problem sha256 `08dc3c0913de`
- idx 11 (recent) — problem sha256 `ec6b9918b593`
