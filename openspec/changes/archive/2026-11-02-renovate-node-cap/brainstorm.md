**Why:** The update bot offers to run itself on Node 26, which Renovate does not support (its `engines` allow only `^24.11.0`), and CI cannot catch it, so the same pull request (#168) would return every week.

## Story

#169 renovate-node-cap — Renovate proposes no runner Node outside the engines range Renovate supports.
https://github.com/andrewduckett/pier-pressure/issues/169

## Decisions

| # | Question | Answer | Source |
|---|---|---|---|
| D1 | Which Node majors may the update bot offer for its own runner? | Below 25: `allowedVersions: "<25"`. Node 24 is the only major Renovate 44.201.1 supports. | Evidence: `engines.node` in renovate@44.201.1 on npm is `^24.11.0` |
| D2 | Which Node pin does the cap cover? | Only `RENOVATE_NODE_VERSION` in `.github/workflows/renovate.yml`, matched by file name and dependency name. The `mise.toml` Node pin stays at 26 for `lets` and keeps updating. | Evidence: `mise.toml` pins `node = "26"`; the workflow says `lets` needs Node 26 |
| D3 | Should the cap follow Renovate's `engines` automatically? | No. Renovate cannot read another package's `engines` to choose a Node version, so the cap is a fixed number raised by hand, like the uv rule. | User |
| D4 | Does CI already catch an unsupported Node? | No. The `validate` job passed on #168 with Node 26, because the config validator does not enforce `engines`. The cap is the only guard. | Evidence: #168 checks |
| D5 | What happens to #168? | Nothing by hand. Once the rule is on main, Renovate closes it as no longer needed and does not reopen it. | Assumption |
| D6 | Where does the reader learn the cap exists? | A comment on the new package rule says why and when to raise it. The workflow's comment on the Node pin points to the rule. | Assumption |

## Changes from the story

None

Confirmed by user: yes
