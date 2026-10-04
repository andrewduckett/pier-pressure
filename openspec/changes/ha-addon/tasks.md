## 1. Add-on files (design D1-D4, D7)

- [x] 1.1 Write failing tests in `tests/test_ha_addon.py` for the `ha-addon` spec's file scenarios. `repository.yaml` and `ha-addon/config.yaml` parse as YAML. The add-on config sets `name`, `version`, `slug`, `description`, `arch` and `image`, and `slug` is `pierpressure`. `version` matches `YYYY.M.N`. `image` is `ghcr.io/andrewduckett/pier-pressure`, with no tag and no `{arch}`. `map` includes `addon_config`, and `environment` sets `PIERPRESSURE_CONFIG` to `/config/config.yaml`. Verify that the tests fail because the files are missing.
- [x] 1.2 Write a failing test that maps each platform in `release.yml`'s build step to an add-on architecture (`linux/amd64` to `amd64`, `linux/arm64` to `aarch64`). The test checks that the add-on's `arch` list is exactly those architectures, and that the release's image name matches the add-on's `image`. Verify that it fails.
- [x] 1.3 Create `repository.yaml` with the repository's name, URL and maintainer. Verify that its test from 1.1 passes.
- [x] 1.4 Create `ha-addon/config.yaml` with `version: "2026.10.0"`, slug `pierpressure`, `arch` `[amd64, aarch64]`, the GHCR `image`, `map: [addon_config]` and the `PIERPRESSURE_CONFIG` environment variable. Leave `init` at its default and add no `options`. Verify that every test from 1.1 and 1.2 passes.
- [x] 1.5 Write `ha-addon/DOCS.md` for the add-on's Documentation tab. It covers where to put `config.yaml`, the `core-mosquitto` broker host, writing the password straight into the file, and a link to the README for the config format. Verify that each step names a real path or setting from 1.4.

## 2. Release labels and version pull request (design D5, D6)

- [x] 2.1 Write failing tests for a small script, `scripts/set_addon_version.py`. Given a version, it replaces only the `version:` line in `ha-addon/config.yaml` and leaves every other byte unchanged. It exits non-zero with a message for a version that does not match `YYYY.M.N`, or for a file with no `version:` line. Then implement the script, and verify that the tests pass.
- [x] 2.2 In `release.yml`, add `io.hass.version=<version>` and `io.hass.type=addon` to the `docker/metadata-action` `labels` input. Verify with `actionlint`.
- [x] 2.3 In `release.yml`, add `pull-requests: write` to the `release` job. Add a last step, after `gh release create`, that resets the branch `release/ha-addon-version` to the released commit and runs `scripts/set_addon_version.py`. The step commits only `ha-addon/config.yaml` and force-pushes the branch. It opens a pull request against `main` when none is open from that branch, and otherwise rewrites the open pull request's title and description for the new version. Verify with `actionlint`. Then check in the file that the step runs only after `gh release create`, and that it never pushes to `main`.
- [x] 2.4 Dry-run the step's shell commands in a scratch clone with a fake version, without pushing. Verify that the resulting commit changes only the `version:` line of `ha-addon/config.yaml`.

## 3. Documentation

- [x] 3.1 Add an "Install as a Home Assistant add-on (app)" section to the README. It covers adding the repository URL, writing `config.yaml` in the add-on's config folder, starting the add-on, the supported architectures, and the plain-text password until #28. Verify that it matches `ha-addon/DOCS.md` and `ha-addon/config.yaml`.
- [x] 3.2 Update the README's "Releasing" section. Each release now opens a version pull request for the add-on, which the maintainer merges to deliver the update. Add the one-time repository setting that lets GitHub Actions create pull requests. Verify that it matches design D5 and the Migration Plan.
- [x] 3.3 Add an add-on section to `docs/acceptance/ha-acceptance.md`. It covers adding the repository by URL (with `#<branch>` before merge), installing it, a first start without `config.yaml` that stops with a configuration error, a start with `config.yaml` that shows the same device and entities as a Docker install, and a first log line with the add-on's version. Verify that each check matches a scenario in the `ha-addon` spec.

## 4. Pre-merge verification

- [ ] 4.1 Run `just check` and `openspec validate ha-addon --strict`, and check that both pass.
- [ ] 4.2 Ask the maintainer to turn on *Allow GitHub Actions to create and approve pull requests* in the repository settings. Verify with `gh api repos/andrewduckett/pier-pressure/actions/permissions/workflow`, which should show `can_approve_pull_request_reviews: true`.
- [ ] 4.3 Ask the maintainer to run the add-on section of the acceptance checklist on Home Assistant OS, using `https://github.com/andrewduckett/pier-pressure#ha-addon`. Record the result in the checklist's Result block in the pull request description.
- [ ] 4.4 Add an "After merge" checklist to the pull request description for the next release. It covers checking that the version pull request opens and changes only the add-on version, that the new image carries both `io.hass` labels, and that Home Assistant offers the add-on update after the merge.
