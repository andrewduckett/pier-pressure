## Why

An adopter who wants to run PierPressure today must clone the repository and build
the image. No published image exists, so nobody can pin a known-good image. The
maintainer also has no release process: *Release and deploy* is the only `gap` in
the discovery journey map. This story is the walking skeleton for the
"adoptable, maintainable release" epic (#19), because every later install path,
including the Home Assistant add-on (#23), pulls this image.

Story: #21 `release-image`.

## What Changes

- Add a **release workflow** that the maintainer starts by hand in GitHub Actions
  (`workflow_dispatch`). One run does the whole release:
  1. It re-runs the project's checks (`just check`) and stops if they fail.
  2. It computes the next CalVer (calendar versioning) version, `YYYY.M.N`. The
     counter `N` starts at 0 each month, so this month's first release is
     `2026.10.0`.
  3. It builds the existing `Dockerfile` for `linux/amd64` and `linux/arm64`.
  4. It pushes the image to `ghcr.io/andrewduckett/pier-pressure`, tagged with
     the version and `latest`.
  5. It tags the commit with the version and creates a GitHub release with
     generated notes.
- Make the **git tag the only source of the version.** The package reads its
  version from the tag at build time, so `pyproject.toml` and
  `pierpressure/__init__.py` no longer hard-code `0.1.0`.
- **Stamp the version into the image.** The image carries it in standard OCI
  (Open Container Initiative) labels, and the service logs it on startup.
- **Pin the uv build tool** in the `Dockerfile`, and declare the accepted uv range
  in `pyproject.toml`, so the dev shell, CI and the image agree on uv.
- **Point the README quick start at the published image** instead of a local
  build.

Out of scope:

- The Home Assistant add-on. It is its own story (#23).
- Automatic releases on every merge.
- Making CI read `.python-version`, and checking that the `Dockerfile` matches it.
  This tooling-consistency work belongs with #26 `dependency-updates`.
- Reporting the version through MQTT, for example as the device's software
  version. The delivery surface stays as it is.

## Capabilities

### New Capabilities

- `release-image`: how the maintainer cuts a versioned release, and what an
  adopter can rely on in the published image (registry, tags, platforms, version
  scheme and startup version log).

### Modified Capabilities

None. The verdict document, the MQTT topics and the entities do not change.

## Impact

- **New file:** `.github/workflows/release.yml`.
- **Changed files:**
  - `pyproject.toml`: the version becomes dynamic, it gains the `hatch-vcs` build
    dependency, and it gets a `[tool.uv]` section.
  - `uv.lock`: no longer records the project's own version.
  - `pierpressure/__init__.py`: reads the version from package metadata.
  - `pierpressure/__main__.py`: logs the version at startup.
  - `Dockerfile`: pins uv and accepts the version as a build argument.
  - `README.md`: the quick start pulls the image.
- **New dependency:** `hatch-vcs`, used only at build time.
- **GitHub:** the workflow needs permission to write packages and repository
  contents. After the first release, the maintainer must make the GHCR (GitHub
  Container Registry) package public once, by hand.
- **No change** to the core, the verdict document or the MQTT delivery surface.
