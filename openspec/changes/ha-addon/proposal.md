## Why

Home Assistant OS cannot run arbitrary containers. Its users can run extra
software only as an add-on, which Home Assistant now also calls an "app". Today
those users cannot run PierPressure at all. The release image now exists
(`2026.10.0`), so an add-on can wrap that image and add no behaviour of its own,
as the PRD (§9) requires.

Story: #23 `ha-addon`.

## What Changes

- Add an **add-on repository** to this repo. A Home Assistant OS user adds the
  repository URL in Home Assistant and installs PierPressure from it:
  - `repository.yaml` at the repo root names the repository.
  - `ha-addon/config.yaml` describes the add-on. It runs the published image
    `ghcr.io/andrewduckett/pier-pressure` at a pinned release version, on
    `amd64` and `aarch64`.
- **Read the user's config from the add-on's own config folder.** Home Assistant
  mounts that folder at `/config` in the container. The add-on sets
  `PIERPRESSURE_CONFIG=/config/config.yaml`, which the service already reads.
  Broker settings come from `config.yaml`, as they do outside Home Assistant.
- **Keep the add-on version in step with releases.** Home Assistant offers an
  update only when the add-on's `version` changes, and that version must name an
  image tag that exists. After each release pushes its image, the release
  workflow opens a pull request that sets the add-on `version` to the new
  release. The maintainer merges it.
- **Label the image for Home Assistant.** The release adds the labels
  `io.hass.version` (the release version) and `io.hass.type` (`addon`), which the
  Home Assistant add-on documentation asks for.
- **Guard against drift.** A test checks that the add-on's image name and
  architectures match the release workflow's.
- **Document the add-on.** The README gets an "Install as a Home Assistant add-on"
  section. The acceptance checklist gets an add-on section, so the add-on is
  proved on a real Home Assistant OS install.

Out of scope:

- Finding the broker through the Supervisor's MQTT service. That is #28.
- An options form in Home Assistant that replaces `config.yaml`.
- Listing the add-on in the community add-on store.
- Any change to how the service behaves. The add-on runs the same image, with the
  same config file format, as Docker users.

## Capabilities

### New Capabilities

- `ha-addon`: how a Home Assistant OS user installs and runs PierPressure as an
  add-on, where its config file lives, which image and platforms it uses, and how
  its version follows releases.

### Modified Capabilities

- `release-image`: a release also labels the image for Home Assistant and opens a
  pull request that moves the add-on to the new version.

## Impact

- **New files:** `repository.yaml`, `ha-addon/config.yaml`,
  `ha-addon/README.md` (the add-on's description in Home Assistant), and a test
  for the add-on files.
- **Changed files:**
  - `.github/workflows/release.yml`: adds the two labels and a step that opens the
    version pull request.
  - `README.md`: the add-on install section.
  - `docs/acceptance/ha-acceptance.md`: the add-on section.
- **Repository setting:** GitHub Actions must be allowed to create pull requests.
  The maintainer turns this on once.
- **No change** to the verdict document, MQTT topics, entities, or the service's
  code.
