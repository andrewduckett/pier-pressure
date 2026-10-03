## Context

See proposal.md for why. The requirements are in `specs/release-image/spec.md`.
The design has to work within these facts about the repository:

- **The version is written in three places.** `pyproject.toml` and
  `pierpressure/__init__.py` both say `0.1.0`, and `uv.lock` records it too.
  Nothing reads the version at runtime. `tests/test_core_boundary.py` only asserts
  that `pierpressure.__version__` is set.
- **`main` is protected.** A ruleset requires pull requests and status checks.
  Only the admin role can bypass it. A workflow that uses `GITHUB_TOKEN` therefore
  cannot push a "bump the version" commit to `main`. The ruleset covers the
  default branch only, so a workflow can still push tags.
- **The Docker build has no git history.** The `Dockerfile` copies only
  `pyproject.toml`, `uv.lock`, `README.md` and `pierpressure/`. The build cannot
  read the version from git.
- **Tool versions drift between environments.** The Nix dev shell pins uv
  (0.12.17) through `flake.lock`. CI (`astral-sh/setup-uv@v5`) and the
  `Dockerfile` (`ghcr.io/astral-sh/uv:latest`) both use the newest uv. All three
  install dependencies from `uv.lock` with `--frozen`, so the installed packages
  already match.

## Goals / Non-Goals

**Goals:**

- Store each release version in exactly one place: its git tag.
- Make one manual run take a commit from "checks pass" to "image pulled by
  adopters", with no step done by hand except triggering the run. (Making the
  GHCR package public is a one-time step, described under Migration Plan.)
- Keep the published image reproducible enough that the same commit gives the
  same tooling.

**Non-Goals:**

- Signing images, attaching provenance attestations or generating an SBOM
  (software bill of materials). These can be added to the same workflow later.
- Publishing to any registry other than GHCR.
- Pinning the Python base image. `python:3.12-slim` keeps floating within 3.12,
  so it picks up security patches. #26 handles base image updates.

## Decisions

### D1: The git tag is the only source of the version

`pyproject.toml` declares `dynamic = ["version"]`. The `hatch-vcs` plugin for the
existing `hatchling` build backend reads the version from git when the package is
built. `pierpressure/__init__.py` sets `__version__` from
`importlib.metadata.version("pierpressure")`. The hard-coded `0.1.0` goes away in
both files.

How each kind of build gets its version:

| Build | Version source | Example |
|---|---|---|
| Release image | The workflow passes the computed version as a Docker build argument. The `Dockerfile` exports it as `SETUPTOOLS_SCM_PRETEND_VERSION` for the project install step. | `2026.10.0` |
| Dev checkout or CI | `hatch-vcs` reads the nearest tag and the distance from it. | `2026.10.1.dev3+g1a2b3c4` |
| Local `docker build .` | No git history and no build argument, so `hatch-vcs` uses `fallback-version`. | `0.0.0+unreleased` |

The `Dockerfile` declares the build argument *after* the dependency-only
`uv sync`. Changing the version then rebuilds only the project layer, not the
dependency layer.

uv caches the editable install of the project. Without help, a local `uv sync`
would keep reporting a stale version after a new tag. `[tool.uv] cache-keys`
therefore includes the git commit and tags, so uv rebuilds the project when
either changes.

`uv.lock` stops recording the project's own version, which is how uv handles a
dynamic version. `uv sync --frozen` keeps working.

Alternatives considered:

- **Inject the version only into the image.** This is simplest, but the package
  metadata would say one thing and the image another. `pierpressure.__version__`
  would be wrong everywhere except in a released image.
- **Commit a version bump, then tag.** The `main` ruleset blocks a direct push.
  Opening a pull request for each release breaks the "one manual action" goal.

### D2: Version computation is a small, tested Python script

`scripts/next_version.py` computes the next version. It takes the existing tags
and today's UTC date as input, and it uses only the standard library. A pure
function, `next_version(tags, today)`, holds the logic, and the script's command
line is a thin wrapper around it. The tests in `tests/` call the function
directly, so every CalVer scenario in the spec is a unit test. That includes the
monthly reset and the numeric comparison of `2026.10.10` against `2026.10.9`.

The script ignores tags that do not match `YYYY.M.N` exactly. The same script
also reports whether the commit being released already has a release tag, so the
workflow can refuse to release it twice.

The alternative was a shell one-liner in the workflow using `git tag --sort`.
Text sorting gets `2026.10.10` against `2026.10.9` wrong unless the shell is
written carefully, and a one-liner cannot be unit tested.

### D3: One release workflow with two jobs

`.github/workflows/release.yml` runs on `workflow_dispatch` only:

```
  workflow_dispatch (main only)
          |
          v
  +-------------------+        +----------------------------------------------+
  | job: check        |  pass  | job: release   (needs: check)                |
  | uv sync --frozen  | -----> | 1. refuse if ref != refs/heads/main          |
  | just check        |        | 2. fetch tags; next_version.py -> VERSION    |
  +-------------------+        |    (fail if HEAD already has a release tag)  |
                               | 3. QEMU + buildx; log in to GHCR             |
                               | 4. build + push linux/amd64,linux/arm64      |
                               |    tags: VERSION, latest; OCI labels         |
                               | 5. gh release create VERSION --target SHA    |
                               |    --generate-notes   (creates the tag)     |
                               +----------------------------------------------+
```

- **Checks gate the release.** The `check` job repeats the setup steps from
  `ci.yml`. The `release` job declares `needs: check`. Re-running the checks costs
  about a minute, and it does not depend on looking up CI results through the API.
  The integration tests are not part of the gate. `just check` is the gate the
  project defines, and the integration tests need a broker service.
- **Only `main` releases.** The first step fails unless `github.ref` is
  `refs/heads/main`.
- **Image first, then tag.** The workflow creates the tag and GitHub release only
  after the push succeeds, so a release can never exist without its image. If the release
  step fails after the push, re-running the workflow computes the same version,
  because no tag exists yet. It then pushes the same commit again under that
  version and completes the release.
- **One release at a time.** A `concurrency` group named `release`, with
  `cancel-in-progress: false`, queues a second run behind the first. Two runs
  can therefore never read the same tag list and pick the same `N`. GitHub keeps
  at most one waiting run per group. A third trigger cancels the waiting run
  before it starts, so the cancelled run pushes and tags nothing. The maintainer
  starts releases by hand, so a cancelled duplicate loses nothing.
- **Least privilege.** The `release` job alone gets `contents: write` (to create
  the tag and release) and `packages: write` (to push to GHCR). The `check` job
  gets `contents: read`.
- **Standard actions.** `docker/metadata-action` produces the tags, the OCI labels
  and the matching OCI annotations (`version`, `revision`, `source`, `created`).
  `docker/build-push-action` builds and pushes the image, and receives both
  outputs.
- **Labels and annotations.** A multi-platform image has two layers of metadata.
  Each platform's image config carries labels, which `docker inspect` shows after
  a pull. The image index that ties the platforms together carries annotations.
  GHCR reads `source` from the index annotations to link the package to the
  repository. The workflow therefore sets
  `DOCKER_METADATA_ANNOTATIONS_LEVELS=manifest,index`, so the annotations land on
  both layers.

### D4: Build arm64 under QEMU emulation

One `build-push-action` step builds both platforms, using QEMU to emulate arm64
on the amd64 runner. The `Dockerfile` compiles nothing. `uv sync` installs only
prebuilt wheels, and every dependency publishes arm64 wheels. The slowest
emulated step is bytecode compilation, which should take a few minutes at most.
Releases are rare and started by hand, so the slower build is acceptable.

The alternative was a native arm64 runner (`ubuntu-24.04-arm`). It is faster, but
it needs a job per platform plus a job that merges the manifests. It can replace
QEMU later without any change that adopters can see.

### D5: Pin uv once, and let uv enforce the range everywhere

- The `Dockerfile` copies uv from `ghcr.io/astral-sh/uv:0.12.17` instead of
  `:latest`.
- `pyproject.toml` declares `[tool.uv] required-version = ">=0.12.17,<0.13"`.

uv checks `required-version` itself, so the check applies everywhere:

- in the Nix shell;
- in CI, where `setup-uv` also reads the range to pick a uv version;
- in the Docker build, because the `Dockerfile` copies `pyproject.toml` in before
  `uv sync` runs.

If any environment drifts out of range, uv stops with a clear error.

The range spans one minor version. Before 1.0, a uv minor release can contain
breaking changes, but a patch release does not change what `uv.lock` installs.
An exact pin would force a coordinated edit whenever `nix flake update` moves uv
by a patch.

Building the image with Nix was considered, so that it would use exactly the
dev shell's versions. It would replace the `Dockerfile` with a second build
system, complicate multi-platform builds, and gain nothing for adopters.

### D6: Log the version before anything else

`main()` in `pierpressure/__main__.py` logs `PierPressure <version>` right after
it configures logging, before it loads the configuration. An adopter reporting a
configuration error therefore always shows which version they ran.

## Risks / Trade-offs

- [A new GHCR package is private by default, so adopters' pulls fail with
  "unauthorized" after the first release.] → The Migration Plan includes a
  one-time step to make the package public. This change also updates the README,
  and tasks.md lists the step as a checklist item.
- [`hatch-vcs` reads no tags in CI's shallow checkout, so CI builds report a
  version such as `0.1.dev1+g…`.] → This is harmless, because no test asserts a
  specific version. The release job fetches tags explicitly.
- [Re-running a failed release step re-pushes an image under the same version.]
  → The re-run builds the same commit. No tag or release existed yet, so no
  adopter could have found that version through a published release.
- [A future Dependabot update (#26) moves uv to 0.13 in the `Dockerfile` while
  `required-version` still says `<0.13`.] → The image build fails loudly, which is
  the intended drift signal. The fix is one edit to the range.
- [QEMU builds are slow.] → This is acceptable for manual releases. D4 describes
  the way out if it stops being acceptable.

## Migration Plan

1. Merge this change. Nothing is published yet.
2. The maintainer triggers the release workflow on `main`. It publishes
   `2026.10.0`, or whatever version the month and existing tags give.
3. The maintainer makes the package public once, in the GHCR package settings
   (Package settings → Change visibility → Public).
4. From a machine that is not logged in to GHCR, pull the version tag. The pull
   proves the image is public. Run it, and check that the first log line shows
   the version.

Rollback: delete the GitHub release, the git tag and the GHCR package version.
Adopters who pinned that version keep the copy they already pulled. No code
rollback is needed, because nothing in the running service depends on the
workflow.
