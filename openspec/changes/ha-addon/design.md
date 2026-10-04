## Context

See proposal.md for why. This design covers how the add-on wraps the release
image, and how the release keeps the add-on's version current.

Facts that shape the approach:

- The release workflow (`.github/workflows/release.yml`) builds one multi-platform
  image for `linux/amd64` and `linux/arm64`. It pushes the image, then creates the
  tag and GitHub release. Release `2026.10.0` exists and anyone can pull it
  without logging in.
- The service reads its config path from `PIERPRESSURE_CONFIG`
  (`pierpressure/__main__.py:46`). A missing file logs
  `Configuration error: ... No such file or directory: '<path>'` and exits with
  status 1.
- Home Assistant pulls a pre-built add-on image as `<image>:<version>`. It offers
  an update only when the add-on's `version` changes.
- The Supervisor is the Home Assistant OS component that installs and runs
  add-ons. It checks an image's platform from Docker's own image fields, not from
  labels (`supervisor/docker/interface.py`, `check_image`).
- The repository does not allow GitHub Actions to create pull requests yet.
- GitHub does not start other workflows for a pull request that a workflow opens
  with its built-in token.

## Goals / Non-Goals

**Goals:**

- The add-on runs the exact image that Docker users run, with no add-on-specific
  code.
- The add-on version never names an image tag that does not exist.
- A test catches drift between the add-on files and the release workflow.

**Non-Goals:**

- 32-bit ARM (`armv7`) support. The image is not built for it.
- An add-on icon or logo. Home Assistant shows a default.

## Decisions

### D1. Home Assistant pulls the released image; it never builds one

`ha-addon/config.yaml` sets `image: ghcr.io/andrewduckett/pier-pressure` and
`version` to a release version. The add-on folder holds no `Dockerfile`.

- *Why:* Docker users and add-on users then run byte-identical images. A Raspberry
  Pi does not spend many minutes building Python dependencies.
- *Alternative:* a `Dockerfile` in the add-on folder that Home Assistant builds
  locally. Rejected: it is slow on small hardware, and it can drift from the
  release image.
- `image` has no `{arch}` placeholder. Home Assistant accepts a multi-platform
  image name and pulls the right platform.

### D2. The add-on lives in `ha-addon/`, with `repository.yaml` at the root

Home Assistant needs `repository.yaml` at the repository root, and one folder per
add-on. The folder cannot be `pierpressure/`, because that is the Python package.
The folder is `ha-addon/` and the slug is `pierpressure`.

- *Why:* users add the plain repository URL. No second repository needs keeping
  in step.
- *Alternative:* a separate `pier-pressure-addon` repository. Rejected: it splits
  the release from the add-on, and the version pull request would cross
  repositories.

### D3. Config lives in the add-on's own config folder

`config.yaml` maps `addon_config`, which Home Assistant mounts at `/config`.
`environment` sets `PIERPRESSURE_CONFIG=/config/config.yaml`. The add-on declares
no `options` or `schema`.

- *Why:* the folder belongs to this add-on, survives updates, and is included in
  Home Assistant backups. Users edit it with the File editor or Samba add-ons. The
  service needs no change.
- *Alternative:* map `homeassistant_config` and read a file from Home Assistant's
  own config folder. Rejected: it gives the add-on Home Assistant's whole config,
  including its secrets.
- *Alternative:* an options form. Out of scope (proposal).
- *Consequence:* add-on users cannot set environment variables, so `${VAR}` in
  `config.yaml` stays unexpanded. The README tells them to write the broker
  password straight into the file. #28 removes this step for Mosquitto users.

### D4. Docker's default init stays on

The add-on leaves `init` at its default (`true`). Docker then runs a small init
process as process 1, which passes the stop signal to Python.

- *Why:* the image has no init system of its own. Without one, Python runs as
  process 1 and ignores the stop signal, so each stop waits for Docker's timeout.

### D5. The release opens one version pull request, on a fixed branch

A new last step in the `release` job runs after `gh release create`:

1. Create or reset the branch `release/ha-addon-version` at the released commit.
2. Replace the `version:` line in `ha-addon/config.yaml` with the new version, and
   commit only that file.
3. Force-push the branch.
4. If no pull request is open from that branch, open one against `main`.
   Otherwise, rewrite the open pull request's title and description for the new
   version, so neither names an older release.

The job gains `pull-requests: write`. It uses the built-in `GITHUB_TOKEN`.

- *Why after the tag:* the pull request can only name an image that is already
  pushed.
- *Why a fixed branch:* a force-push replaces an older, unmerged version, so at
  most one version pull request is ever open.
- *Why not commit to `main`:* the maintainer owns merges to `main`, and the
  release spec says a release does not change `main`.
- *Alternative:* a personal access token or a GitHub App, so CI runs on the pull
  request. Rejected for now: it adds a secret to rotate. The `main` ruleset
  requires the `check` status before a merge, so the maintainer closes and
  reopens the pull request to run CI on it before merging.
- *Failure:* if the step fails, the run fails after the image, tag and release
  exist. The maintainer then opens the pull request by hand. The release itself
  stands.

### D6. The release adds `io.hass.version` and `io.hass.type` labels

The release workflow adds both labels through the existing `docker/metadata-action`
`labels` input, next to the OCI labels.

- *Why in the workflow:* only the workflow knows the release version. The
  `Dockerfile` stays free of Home Assistant details.
- *Why not `io.hass.arch`:* the Supervisor reads the platform from Docker's own
  image fields. One label value cannot be right for both platforms in a single
  multi-platform build. Docker also says `arm64` where Home Assistant says
  `aarch64`.
- *Note:* `2026.10.0` has neither label. The Supervisor runs it anyway. Without
  `io.hass.version`, a restore from backup re-pulls the image, which is slower but
  correct.

### D7. A test pins the add-on to the release workflow

`tests/test_ha_addon.py` reads `repository.yaml`, `ha-addon/config.yaml` and
`.github/workflows/release.yml` with PyYAML. It checks the fields the
`ha-addon` spec lists, and that each release platform maps to exactly one add-on
architecture (`linux/amd64` → `amd64`, `linux/arm64` → `aarch64`).

- *Why:* a later change to the release platforms or image name fails `just check`
  until the add-on follows.

## Risks / Trade-offs

- [GitHub Actions cannot create pull requests until the maintainer turns this on]
  → The tasks include turning it on before the next release. If it is off, the run
  fails loudly (D5).
- [CI does not run on the version pull request, and `main` requires it before a
  merge] → The maintainer closes and reopens the pull request, which runs CI.
- [Broker password sits in plain text in the add-on folder] → Only people who
  can open the add-on's config folder, through add-ons such as File editor or
  Samba, can read it. #28 removes it for Mosquitto users.
- [Add-on users wait for the maintainer to merge each version pull request] → This
  is deliberate: the maintainer decides when an update reaches Home Assistant.
- [32-bit ARM Home Assistant installs cannot run the add-on] → Home Assistant
  hides an add-on that does not support the host's architecture. The README names
  the supported architectures.

## Migration Plan

- No migration for existing Docker users. The image changes only by two labels.
- Before the next release, the maintainer turns on *Allow GitHub Actions to create
  and approve pull requests* in the repository settings.
- Rollback: delete `repository.yaml` and `ha-addon/`, and remove the release step.
  Installed add-ons keep running their current version.
