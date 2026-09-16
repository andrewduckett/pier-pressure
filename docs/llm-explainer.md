# The LLM explainer (M7)

The explainer turns a finished verdict into a short plain-language paragraph — "is
tonight worth setting up for, and what should I point at?" answered in sentences. It
reads the already-computed verdict and never feeds the astronomy or scoring math, so
the numbers are unchanged whether or not it runs.

The narrative is delivered as a **separate Home Assistant sensor entity**, beside the
existing verdict, score, top-target, and refresh entities. It is **never** a field of
the verdict document (ADR-0011), so the document stays byte-identical with the
explainer on or off.

## Disabled by default

With no `explainer` block — or with `enabled: false` — the explainer is off. No
provider is constructed, no LLM call is ever made, and no narrative entity is
published. A default deployment behaves exactly as it did before M7.

## Enabling it

Add an `explainer` block to your `config.yaml`:

```yaml
explainer:
  enabled: true
  model: claude-opus-5                 # any current Claude model id
  api_key: ${ANTHROPIC_API_KEY}        # env override; avoids plaintext
```

Then provide the key in the environment and run as usual:

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
uv run python -m pierpressure /path/to/config.yaml
```

- `enabled` — the single switch. It wires both the LLM provider and the narrative
  entity; leave it out or set it `false` to keep the explainer off.
- `model` — the Claude model that writes the prose. Defaults to `claude-opus-5`.
- `api_key` — your Anthropic API key. Use the `${VAR}` form so the secret lives in the
  environment, not the file. The key is never logged. If the variable is unset, the
  literal `${VAR}` placeholder is left in place (a visible "missing secret" rather
  than a blank), and the explainer degrades to no narrative rather than erroring.

The explainer is bounded and fault-tolerant: each call carries a short timeout, the
result is cached on the exact verdict terms so an unchanged sky reuses one call, and
any failure (a timeout, an error, or empty text) simply produces no narrative for
that recompute. **A failing explainer never blocks or delays the verdict** — the
verdict is always published on time, and the narrative entity resolves to
`unavailable`.

## The narrative entity

When enabled, Home Assistant auto-discovers one extra sensor per pier:

| Purpose | Topic | Retain |
| --- | --- | --- |
| Narrative sensor (discovery) | `homeassistant/sensor/pierpressure_<pier>/narrative/config` | yes |
| Narrative state | `pierpressure/<pier>/narrative/state` | yes |
| Narrative attributes (JSON) | `pierpressure/<pier>/narrative/attributes` | yes |

Entity state values are length-limited, so the state topic carries a short marker
(`ready` / `unavailable`) and the full prose rides in the `narrative` attribute. Point
a Markdown or entities card at that attribute to show the paragraph. When no narrative
is available, the entity resolves to `unavailable` — it is never left showing an
earlier night's prose.

## Removing the entity after disabling

The service is stateless across restarts, so it cannot know it once published a
narrative entity and does not auto-remove one. If you enable the explainer, let it
publish, then disable it, Home Assistant keeps showing the orphaned (now stale)
narrative entity from its retained discovery topic.

To remove it, clear that retained discovery topic **once** — the standard Home
Assistant discovery removal (publish an empty retained payload to the config topic):

```bash
mosquitto_pub -h <broker> -r -t 'homeassistant/sensor/pierpressure_<pier>/narrative/config' -n
```

This is a one-time operator step, not something the publish path does on its own.

## Manual acceptance check

Whether the prose reads as a *faithful, plain-language summary* of the verdict depends
on generated language, which PierPressure does not assert mechanically (spec
`verdict-narrative`). Confirm it by hand after enabling:

1. Note the verdict entity's value, the score, the confidence, and the top target.
2. Read the narrative attribute.
3. Confirm the paragraph agrees with those terms — same go/no-go sense, no invented
   numbers, objects, or claims beyond what the verdict states — and reads clearly to a
   stargazer. If it drifts from the numbers, that is a prompt or model issue to
   address; the numbers document remains the source of truth regardless.
