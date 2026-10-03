## 1. Version comes from the git tag (design D1, D5)

- [x] 1.1 Make the package version dynamic. In `pyproject.toml`, declare `dynamic = ["version"]`, add `hatch-vcs` to the build requirements, and set `[tool.hatch.version]` to `source = "vcs"` with `fallback-version = "0.0.0+unreleased"`. Run `uv lock`. Verify that `uv run python -c "import importlib.metadata as m; print(m.version('pierpressure'))"` prints a development version, and that `just check` passes.
- [x] 1.2 Write a failing test that `pierpressure.__version__` equals `importlib.metadata.version("pierpressure")`. Then set `__version__` from package metadata in `pierpressure/__init__.py`, and verify that the test passes.
- [x] 1.3 Add `[tool.uv]` to `pyproject.toml` with `required-version = ">=0.12.17,<0.13"` and `cache-keys` covering `pyproject.toml` and the git commit and tags. Verify that `uv sync` succeeds. Then create a throwaway local tag, run `uv sync`, check that the reported version follows the tag, and delete the tag.

## 2. The service logs its version first (design D6)

- [x] 2.1 Write a failing test that `main()` logs `PierPressure <version>` as its first record, before it reports a configuration error for a missing config file. Then add the log line to `pierpressure/__main__.py`, and verify that the test passes.

## 3. Next-version script (design D2)

- [x] 3.1 Write failing unit tests for `next_version(tags, today)`, one per CalVer scenario in the spec: first release of a month, later release in the same month, monthly reset, numeric comparison of `2026.10.10` against `2026.10.9`, and non-matching tags (such as `v1.0` or `2026.10.x`) being ignored.
- [x] 3.2 Implement `scripts/next_version.py` with the pure `next_version` function, using only the standard library. Verify that the tests from 3.1 pass.
- [x] 3.3 Add the command line to the script. It reads the tags from git, prints the next version, and exits non-zero with a message naming the existing version when `HEAD` already has a release tag. Write a test for the "commit already released" case first. Verify it by running the script in a scratch repository with and without a tag on `HEAD`.
- [x] 3.4 Extend mypy's scope to `scripts/` so that `just check` type-checks the script. Verify this by adding a deliberate type error, seeing `just check` fail, and then removing the error.

## 4. Dockerfile (design D1, D5)

- [x] 4.1 In the `Dockerfile`, pin uv to `ghcr.io/astral-sh/uv:0.12.17`. After the dependency-only `uv sync`, declare an optional `PIERPRESSURE_VERSION` build argument and pass it to the project install as `SETUPTOOLS_SCM_PRETEND_VERSION`. Verify the result with `docker build .`: the container's first log line shows `0.0.0+unreleased`.
- [x] 4.2 Build the image with `--build-arg PIERPRESSURE_VERSION=2026.10.0`. Verify that its first log line shows `2026.10.0`, and that a second build with a different version reuses the cached dependency layer.

## 5. Release workflow (design D3, D4)

- [x] 5.1 Create `.github/workflows/release.yml`, triggered only by `workflow_dispatch`. Give it the `release` concurrency group with `cancel-in-progress: false`, and a `check` job that reuses `ci.yml`'s setup and runs `just check` with `contents: read`. Verify the file with `actionlint`.
- [x] 5.2 Add the `release` job, with `needs: check` and `contents: write` and `packages: write`. It first fails unless the ref is `refs/heads/main`, then fetches the tags and runs `scripts/next_version.py`. Verify it with `actionlint`, and check that the job's permissions list nothing beyond those two scopes.
- [x] 5.3 Add the image steps to the `release` job: QEMU, buildx, a GHCR login with `GITHUB_TOKEN`, and `docker/metadata-action` (tags `VERSION` and `latest`, with `DOCKER_METADATA_ANNOTATIONS_LEVELS=manifest,index`). Then add `docker/build-push-action` for `linux/amd64,linux/arm64`, passing tags, labels, annotations and the version build argument. Verify with `actionlint`.
- [x] 5.4 Add a final step that runs `gh release create VERSION --target <sha> --generate-notes`, and runs only after the push step succeeds. Verify with `actionlint`, and check in the file that no step creates a tag or release before the push.

## 6. Documentation

- [x] 6.1 Rewrite the README quick start to pull `ghcr.io/andrewduckett/pier-pressure:<version>`. Show pinning a version, and mention `latest`. Remove the "No image is published yet" sentence. Keep building from source as a secondary path. Verify that every command in the quick start runs as written.
- [x] 6.2 Add a short "Releasing" section for the maintainer: how to trigger the release, the CalVer scheme, and the one-time step to make the GHCR package public. Verify that it matches design.md's Migration Plan.

## 7. Pre-merge verification

- [ ] 7.1 Build both platforms locally with `docker buildx build --platform linux/amd64,linux/arm64 --build-arg PIERPRESSURE_VERSION=2026.10.0 .` and check that both builds succeed.
- [ ] 7.2 Run `just check` and `openspec validate release-image --strict`, and check that both pass.
- [ ] 7.3 Add an "After merge" checklist to the PR description. It covers the steps that need the workflow on `main`: the first release run, making the package public, an anonymous pull on amd64 and arm64, inspecting the labels and index annotations, and checking the startup log line.
