## Why

Ranking today answers "what is best *placed* tonight" — altitude, window length,
moon separation, transit timing. It ignores two things an imager cares about just
as much: whether a target *fits the gear* pointed at it, and whether it is *bright
enough* to be worth the night. So a faint smudge that frames badly can outrank a
well-suited target that sits slightly lower. M5 deferred exactly this science to
"the equipment milestone," and the pinned catalog already carries the angular size
and surface brightness the terms need — so the data is in hand and the milestone
is unblocked.

## What Changes

- **Add an optional per-pier equipment description.** One rig per pier —
  telescope focal length plus camera sensor dimensions, with an optional
  reducer/barlow factor. The pure core derives the rig's field of view offline.
  Equipment is optional: a pier with no rig still ranks, on placement and
  brightness. (Config growth only — no existing field changes. Not breaking.)
- **Add a field-of-view fit ranking term.** A target's angular size is scored on
  how well it frames in the rig: an object too large to fit and one too small to
  see are both penalised, with a comfortable fraction of the frame scoring best.
- **Add a brightness ranking term.** Brighter targets score higher, using surface
  brightness where the catalog records it and integrated magnitude otherwise.
  Magnitude stays the candidate filter it is today; brightness now also *ranks
  within* the survivors, so a fainter but better-placed object no longer
  automatically outranks a brighter one.
- **Renormalise the score over known terms.** The four fixed-weight terms become
  six, and the weights renormalise over the terms whose inputs are known for each
  (pier, target). A missing rig, an unknown size, or an unknown magnitude drops
  only that term rather than substituting a guessed value. The score stays a
  banded 0–100.
- **Grow the document additively.** Each target object additionally carries its
  angular size and brightness, and `reasons[]` gains equipment-aware entries. No
  existing field changes meaning. The catalog parser additionally reads surface
  brightness.
- **Key the ranking cache on the rig.** Rankings now depend on the configured
  rig, so the rig identity joins the per-night ranking cache key.

## Capabilities

### New Capabilities

- `pier-equipment`: an optional per-pier optical description (telescope + camera)
  and the field of view derived from it — computed offline and deterministically,
  with no rig meaning no field-of-view term rather than an error.

### Modified Capabilities

- `target-ranking`: scoring gains a field-of-view-fit term and a brightness term;
  the six terms' weights renormalise per target over those with known inputs; the
  catalog additionally carries surface brightness; each ranked target additionally
  carries its size and brightness.
- `night-verdict`: each target object in the verdict document additively carries
  angular size and brightness fields. No existing field changes.

## Impact

- **Config:** a new optional `rig` on the pier configuration
  (`pierpressure/core/config.py`).
- **Core:** `catalog.py` (parse surface brightness; expose size), `ranking.py`
  (two new sub-scores, per-target weight renormalisation, rig in the cache key),
  `model.py` (additive `Target` fields).
- **Contract:** additive only — new document fields and new `reasons[]` entries;
  the delivery surface (topics, entities, entity mapping) and every existing
  field are unchanged.
- **Tests:** golden target-list outputs shift as the new terms enter the score
  and must be re-baselined against a validation night (as M5 did); the
  determinism and pure-core boundary tests are unaffected.
- **Dependencies:** none added; the astronomy stack is unchanged and the core
  stays fully offline.
- **Docs:** `docs/roadmap.md` M6 is updated; the scoring-model change (weight
  renormalisation and the surface-brightness choice) is a likely ADR.
