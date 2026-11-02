## Review Metadata

- **Review round**: 1
- **Prior round**: none
- **Reviewer context**: two reviews of the same prompt, at commit `3a6084e`.
  Reviewer A: fresh context, other family (Gemini, `gemini-3.8-flash`, through
  `lets delegate review run`; `gemini-4-argon` was tried first and returned only
  a quota message). Reviewer B: subagent, same family (Claude Opus), at the
  user's request.
- **Independent**: A yes; B no, same family as the author
- **Tool restrictions**: read-only: view, grep, glob only. The working tree was
  unchanged after the subagent ran.
- **Artifacts reviewed**: brainstorm.md, proposal.md, design.md, specs/, adr.md,
  ADR-0028, relevant source files

## Findings

Each finding is labelled with its reviewer (A or B), the check it falls under,
and the result of checking it against the repository.

### 🔴 Critical (blocking)

- **A1 (Contradictions): the catalog scenario asks the catalog for model
  identifiers that design D1 keeps out of it.** Reviewer B raised the same
  point as a Moderate finding (B-M4). CONFIRMED, but small: a scenario wording
  fix, not a blocker. Fixed by required change 1.

### 🟡 Moderate

- **B-M1 (Assumptions / where it stops working): the startup cloud rule no
  longer guarantees cloud, and one provider list covers every pier.** CONFIRMED:
  `AppConfig.conditions` is install-wide, and `__main__` builds one stack. A
  regional model fails forever for an out-of-area pier. Fixed by required
  change 5.
- **B-M2 (Contradictions): fetch time stands in for issue time, so stale model
  runs look fresh.** CONFIRMED: `freshness_factor` reads the cloud series' issue
  time, and the plan stamps fetch time. The live check shows Open-Meteo's
  metadata endpoint reports run times for some models. The user chose to keep
  fetch time, document it and pin it, and to file reading the run time as a
  follow-up (brainstorm D13). Fixed by required change 3.
- **B-M3 (Assumption rows): the 400 outside a model's area had no recorded
  evidence.** CONFIRMED: the check was run but not recorded. Re-run live: HRRR
  answers 400 at London and 200 at Arizona; HRDPS answers 400 at both; RDPS
  answers 200 at both. Fixed by required change 2.
- **B-M4 (Test seams): nothing tests four of the five key-to-model mappings.**
  CONFIRMED: `test_each_fetcher_points_at_its_catalog_spec` checks `spec`, not
  `model`. Fixed by required changes 1 and 4.
- **A2 (Where it stops working): timeouts add up across sequential Open-Meteo
  fetches.** CONFIRMED: ADR-0012 assumes a recompute is short enough to run
  inline, and each fetch has a 10-second timeout. Reviewer B raised the same
  point as S1. Fixed by required change 4.
- **A3 (Contradictions): the spec does not require asking only for declared
  variables.** CONFIRMED. Fixed by required change 1.
- **A4 (Assumption rows): brainstorm D1 says every model returns "the weather
  variables", which contradicts D4.** CONFIRMED. Fixed by required change 2.

### 📌 Suggestions

- **A5 (Assumption rows): D11 is an unsupported Assumption.** Declined: nothing
  in the plan depends on it. The task list will show the size.
- **A6 / B-S3 (Plain language): sentences over 30 words in the proposal, spec
  and ADR.** Accepted. Fixed by required changes 1, 5 and 6.
- **B-S1 (README): the suggested order puts every cloud provider on one
  service, and only HRRR supplies precipitation probability.** Partly accepted:
  the README warning is in required change 6. The suggested order itself comes
  from the story packet, and stays as written.
- **B-S2 (Scope): the README impact list is incomplete, and a removed model
  leaves a health entity behind.** Accepted. Fixed by required change 6.
- **B-S3 (Testability): the out-of-area requirement repeats existing rules, and
  depends on a cause the system cannot observe.** Accepted: the requirement now
  states only the new obligation, no startup check, and keeps the 400 scenario
  as an example. Fixed by required change 1.
- **B-S4 (Test seams): the byte-for-byte `open_meteo` goal is untested, and the
  column map duplicates the parser's list.** Accepted. Fixed by required
  change 4.
- **B-S5 (Contradictions): display names fix entity IDs, not keys.** CONFIRMED
  by `delivery/mqtt.py` and README's `7timer_health`. Fixed by required
  changes 4 and 5.
- **B-S6 (Vocabulary): "model entry" and "model provider" both appear, and
  the ADR avoids the agreed term Alternate.** Accepted. Fixed by required
  changes 2 and 5.
- **B-S7 (Evidence): the evidence is dated tomorrow, and the Astrospheric claim
  has no source.** REFUTED: the date is UTC (local 2026-11-01 21:53 CST is
  2026-11-02 03:53 UTC); the ledger now says UTC. The Astrospheric claim comes
  from the story packet (#154, "Why this story").
- **B-S8 (Privacy): fixtures could record the author's pier.** No change:
  design D6 already records at a public point, Toronto.

## Embedded-Instruction / Injection Attempts

**Detected:** none. Both reviewers report none.

## Verdict

VERDICT: APPROVE_WITH_CHANGES

## Required Changes (if APPROVE_WITH_CHANGES)

1. `specs/conditions/spec.md`: the catalog scenario asserts key, display name
   and no key only. A new scenario asserts each model provider's request names
   exactly its model, for all five keys. The request requirement adds "only for
   the variables it declares", with an HRDPS scenario. The `open_meteo` scenario
   pins the unchanged request. A new requirement pins a model provider's issue
   time as its fetch time. The out-of-area requirement becomes "not rejected at
   startup", in sentences under 30 words.
2. `brainstorm.md`: D1 names the weather variables each model returns and says
   UTC. "Model entry" becomes "model provider". D12 records the live
   out-of-area check. D13 records the user's issue-time decision.
3. `design.md` Risks: the issue-time effect on confidence, accepted, with the
   follow-up named.
4. `design.md`: Context cites D12, the install-wide provider list and the
   single work thread. Test Seams name the parametrised five-key request test
   and the exact `open_meteo` request test. D3 has the parser read the same
   column map, plus a catalog test that every declared variable has a column.
   Risks add serial timeouts and the multi-pier failure. The blast radius says
   display names fix entity IDs.
5. ADR-0028: Context uses "alternates" in shorter sentences. Consequences add
   the cloud-rule and multi-pier bullet, and say display names fix entity IDs.
6. `proposal.md`: the long bullet is split. The README bullet adds the
   shared-service, issue-time and install-wide notes. Impact lists every README
   section that names provider keys, including removal of a dropped provider's
   entity.

CHANGES_APPLIED: yes

## Rebuttals

- A1 / B-M4: fixed by required changes 1 and 4.
- A2 / B-S1: fixed by required changes 4 and 6. The suggested order stays as
  the story gives it.
- A3: fixed by required change 1.
- A4: fixed by required change 2.
- A5: declined. No part of the plan rests on D11.
- A6: fixed by required changes 1, 5 and 6.
- B-M1: fixed by required change 5, plus the design risk in change 4. The
  coverage-flag option would add a concept to `ProviderSpec` that the story did
  not ask for.
- B-M2: fixed by required change 3 and the new issue-time requirement in
  change 1, per the user's decision (D13).
- B-M3: fixed by required change 2 (D12).
- B-S2: fixed by required change 6.
- B-S3: fixed by required change 1.
- B-S4: fixed by required change 4.
- B-S5: fixed by required changes 4 and 5.
- B-S6: fixed by required changes 2 and 5.
- B-S7: rebutted. See the finding.
- B-S8: rebutted. Design D6 already uses Toronto.
