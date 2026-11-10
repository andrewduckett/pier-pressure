## Why

Six `night-verdict` requirements about the hard gates, the banded score, degrading without conditions, high cloud, pier tuning and the ranked target list run to between 800 and 2,871 characters, and each one bundles several behaviors (D1). A later change to one of those behaviors has to MODIFY the whole bundle, so a review cannot see which behavior moved, and `openspec validate --strict` fails. This story is part 2 of 3 for `night-verdict` in epic #230.

## What Changes

- Split "Hard gates decide a NO-GO" into five requirements (D3), "A banded score decides GO versus MAYBE" into nine (D4), "The verdict degrades honestly when conditions are unavailable" into six (D5), "High, thin cloud is a distinct score penalty" into six (D7), "Optional pier tuning configuration" into five (D8) and "Targets list is an ordered ranked list" into five (D9). That makes 36 ADDED requirements.
- The banded score's rule for missing seeing and transparency joins the degrading rule that states the same behavior (D6).
- Each original is REMOVED and its parts ADDED under new headings, as epic #230 decision 5 requires (D15).
- Every existing scenario moves word for word. Ten scenarios are added, one for each new requirement that no original scenario fits. Each rests on an existing test (D10).
- Every SHALL, SHALL NOT and MAY keeps its meaning. Six SHALL are added without adding an obligation (D14).
- No behavior, code or test changes. Nothing is **BREAKING**.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `night-verdict`: six long requirements become 36 requirements with the same meaning.

## Impact

- Spec text only: `openspec/specs/night-verdict/spec.md` after archive.
- No spec quotes a heading this change removes (D11).
- No code, test, card, doc or README text quotes a removed heading. Some comments and docs use the terms "hard gates", "banded score" and "ranked list". They stay as they are, and the pull request lists them (D12).
- No drift between the 6 requirements and the code was found (D13).
- After archive, `night-verdict` still has 8 long-requirement warnings. #244 splits those (D16).
