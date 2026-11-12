**Why:** The moon and high-cloud factors cut the whole window by a ratio over the usably clear hours, so clouding out the one hour that carries the cirrus can raise the score; with #97 now per hour for atmosphere, these are the last two factors that break "more cloud never raises the score".

## Story

#112 per-hour-sky-penalties — more cloud in any hour never raises the score, https://github.com/andrewduckett/pier-pressure/issues/112

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Does the packet's first example reproduce? | Yes: ten clear hours, one with 100% high cloud and the rest with no reading, score 70; cloud out that hour and it is 90. The per-hour rule gives 97 then 90. | Evidence: a run of `score_terms` in `pierpressure/core/scoring.py` |
| D2 | Does the packet's second example reproduce? | No: today it scores 92 and falls to 90 when that hour clouds out. It is left out; Scope already names only the first example as a scenario. | Evidence: a run of `score_terms` in `pierpressure/core/scoring.py` |
| D3 | Which factors go per hour? | Both the moon factor and the high-cloud factor, so the whole score is one per-hour sum: `Σ w·q·(0.7 + 0.3a)·(1 − 0.5·illumination·up)·(1 − 0.3·high/100) / Σ w`. | User |
| D4 | What does an hour with no high-cloud reading count as? | A high-cloud factor of 1. With partial cirrus data, only the hours with a reading are cut, not the whole window. | User |
| D5 | What number does the high-cloud reason line state? | Today's number, the clarity-weighted mean over the clear hours with a reading, plus `; covers N% of the usable sky` inside its brackets when that share is below 100%, like the seeing and transparency lines. | User |
| D6 | Does the moon reason line change? | No. Its number, illumination times the clarity-weighted share of clear hours with the moon up, already spans every clear hour. | Evidence: `moon_penalty` in `pierpressure/core/scoring.py` |
| D7 | Does the verdict document or any reader outside the score change? | No. `ScoreTerms` and the penalty terms are read only inside `scoring.py`; the document carries only the score and the reasons. | Evidence: grep of `pierpressure/` |
| D8 | Which main-spec requirements change? | In `night-verdict`: "The score is the product of four factors" becomes a per-hour sum. "More cloud never raises the usable-sky term times the atmosphere factor" becomes "More cloud never raises the score", gains the first example as a scenario, and loses its #112 note. "The high-cloud penalty has its own reason line" gains the coverage note. | Evidence: `openspec/specs/night-verdict/spec.md` |
| D9 | How are moved exact scores handled? | Recompute each spec scenario and unit test the new rule moves, and regenerate the golden verdicts with `PP_WRITE_GOLDENS`, reviewing each diff. | Evidence: `tests/test_golden_verdict.py` |
| D10 | What is the per-hour high-cloud factor called? | The high-cloud factor, the spec's existing name; the packet's "cirrus factor" means the same thing. | Evidence: `openspec/specs/night-verdict/spec.md` |

## Changes from the story

- Cut: the second reproduction case (moon and cirrus in one hour). It does not reproduce, as D2 says. The fix covers it anyway.
- Added: the coverage note on the high-cloud reason line (D5), so the line reads as a mean over part of the usable sky. The packet asked only that the reasons match the new math.

Confirmed by user: yes
