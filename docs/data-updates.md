# Updating the pinned data

This page is for the maintainer. It explains how to update the astronomy data that
PierPressure bundles, and how to check that an update has not broken the verdict.

PierPressure promises that the same pier and the same instant always give a
byte-identical verdict document, with no network access
([ADR-0004](decisions/0004-deterministic-offline-astronomy.md)). That promise holds
only because every piece of astronomy data is pinned. An update to that data can
legitimately change the verdict. When it does, the change must be seen and
reviewed, not merged by accident.

## The pinned data at a glance

| Data | What it gives | How it is pinned | Current version | Licence | How an update arrives |
| --- | --- | --- | --- | --- | --- |
| de421 ephemeris | Sun, moon, and planet positions | The `skyfield-data` package in `uv.lock` | `skyfield-data` 7.0.0 | MIT (package); the JPL ephemeris data is public domain | A Dependabot pull request |
| Skyfield's built-in timescale | Leap seconds and Earth-rotation (delta-T) data | The `skyfield` package in `uv.lock` | `skyfield` 1.55 | MIT | A Dependabot pull request |
| OpenNGC catalogue | Deep-sky objects for target ranking | The committed files in `pierpressure/data/openngc/` | Release tag `v20260501` | CC BY-SA 4.0 | By hand; nothing updates it for you |

Where each one is loaded:

- `pierpressure/core/sky.py` loads `de421.bsp` from the `skyfield-data` package
  and calls `load.timescale(builtin=True)`. `pierpressure/core/ranking.py` reuses
  both.
- `pierpressure/core/catalog.py` loads `NGC.csv` and `addendum.csv` from
  `pierpressure/data/openngc/`.

None of these datasets is urgent to update. de421 covers dates up to October
2053, and OpenNGC changes rarely.

## What an update does to the verdict

An update can change a number in the verdict document. For example, a new
timescale can move a twilight time by a second, and a new catalogue can change a
target's coordinates or which ten targets make the list.

Three tests catch that:

- **`tests/test_golden_verdict.py`** compares seven whole verdict documents with
  committed copies in `tests/fixtures/golden/expected/`. Each of them carries a
  dark window, the moon, and ten ranked targets. A change to any of the three
  datasets that moves a published number fails this test.
- **`tests/test_determinism.py`** checks that two runs at the same instant are
  byte-identical and touch no network.
- **`tests/test_catalog.py`** checks that the catalogue parses, loads offline,
  filters as designed, still contains a known object (M31), and loads in a stable
  order.

The ranking and sky tests (`tests/test_ranking_geometry.py`,
`tests/test_sky_dark_window.py`, `tests/test_sky_moon.py`) also load the
ephemeris. They compare against an independent Skyfield calculation, so they
usually still pass after an update.

If the golden test fails after an update, regenerate the golden documents and
review the difference (see [Review a golden difference](#review-a-golden-difference)):

```sh
PP_WRITE_GOLDENS=1 uv run pytest tests/test_golden_verdict.py
```

Only regenerate them when you have decided the change is expected. The new golden
documents are committed with the update, so the reviewed difference stays in the
history.

## Update the ephemeris or the timescale

Dependabot proposes new versions of `skyfield` and `skyfield-data` every week.
Minor and patch versions come grouped with other Python packages in one pull
request; a major version comes on its own.

1. Check whether the pull request changes `skyfield` or `skyfield-data` in
   `uv.lock`. If it does not, this section does not apply.
2. Wait for CI. If `just check` passes, no published number moved, and you can
   merge as usual.
3. If `tests/test_golden_verdict.py` fails, check out the pull request branch and
   run the regeneration command above.
4. Review the golden difference. If it is expected, commit the new golden
   documents to the same branch with a message that says which package moved them.
5. Run `just check` again and merge once it passes.

If a grouped pull request mixes a data change with unrelated updates and the
difference is hard to read, close it and update `skyfield` or `skyfield-data` on
its own branch with `uv lock --upgrade-package <name>`.

## Update the OpenNGC catalogue

The committed files are the version pin
([ADR-0008](decisions/0008-vendored-openngc-catalog.md)). An update is a
deliberate commit of new files, made on its own branch.

1. Choose an OpenNGC release tag from https://github.com/mattiaverga/OpenNGC/releases.
2. Download the two files from that tag, unchanged:

   ```sh
   TAG=v20260501  # replace with the new tag
   for f in NGC.csv addendum.csv; do
     curl -fsSL -o "pierpressure/data/openngc/$f" \
       "https://raw.githubusercontent.com/mattiaverga/OpenNGC/$TAG/database_files/$f"
   done
   ```

3. Record the new pin in `NOTICE`: the release tag, its commit, and the SHA-256 of
   each file (`sha256sum pierpressure/data/openngc/*.csv`).
4. Check the licence. If the release still uses CC BY-SA 4.0, keep
   `pierpressure/data/openngc/LICENSE-CC-BY-SA-4.0.txt` as it is. If the licence or
   the author list changed, update the licence file and `NOTICE` to match.
5. Run `just check`. If OpenNGC changed a column or a type code, `test_catalog.py`
   or the parser fails; fix the parser before going further.
6. Regenerate the golden documents and review the difference.
7. Commit the data, `NOTICE`, and the golden documents in one commit, with a
   message that names the old and new tags.

### What the licence asks of us

OpenNGC is licensed CC BY-SA 4.0. In practice:

- **Attribution:** keep the source, author, licence, and pinned version in
  `NOTICE`, and keep the licence text next to the data.
- **Share-alike:** if we change the data files themselves, our changed version
  must also be shared under CC BY-SA 4.0. Committing the files unchanged avoids
  this, which is one reason to download them as released.
- PierPressure's own code is MIT-licensed. It only reads the data, so share-alike
  does not apply to the code.

## Review a golden difference

Read the difference with `git diff tests/fixtures/golden/expected/`. Ask whether
each change matches what the update says it changed.

Expected after a timescale or ephemeris update:

- a time in `dark_window`, `moon`, or a target's `window` or `transit_time` moves
  by a few seconds at most
- an angle such as `max_altitude` or `moon_separation` moves in its last decimal
  place
- a score, or a percentage inside a `reasons` line, moves by a point because one
  of those inputs moved

Expected after a catalogue update:

- a target's coordinates, magnitude, name, or size changes, matching the upstream
  release notes
- a target enters or leaves the top ten because of that change

Suspicious, at any time — stop and investigate:

- a time moves by minutes or hours, or a window appears or disappears
- the verdict changes, a gate passes or fails differently, or a reason is added,
  removed, or reworded
- a field is added, removed, renamed, or changes type (the document is a frozen
  contract, so this is never a data update)
- the difference covers more than the update could explain

## Known warning: expired `finals2000A.all`

`skyfield-data` 7.0.0 ships an Earth-orientation file, `finals2000A.all`, that
expires on 18 October 2026. From that date, loading the ephemeris logs this
warning:

```text
RuntimeWarning: The file finals2000A.all has expired. Please upgrade your version of `skyfield-data` or expect computation errors
```

PierPressure never reads that file: it uses Skyfield's built-in timescale
instead. The warning does not affect the verdict, and the tests do not fail on
it. It goes away when a newer `skyfield-data` is released and Dependabot proposes
it.

## Related decisions

- [ADR-0004](decisions/0004-deterministic-offline-astronomy.md): deterministic,
  offline astronomy with pinned data
- [ADR-0008](decisions/0008-vendored-openngc-catalog.md): the OpenNGC catalogue
  vendored as pinned data
