# The LLM explainer (M7)

The explainer turns a finished verdict into a short plain-language paragraph — "is
tonight worth setting up for, and what should I point at?" answered in sentences. It
reads the already-computed verdict and never feeds the astronomy or scoring math, so
the numbers are unchanged whether or not it runs.

It is **model-agnostic**: the prose is produced through
[Pydantic AI](https://ai.pydantic.dev), and the `model` you configure selects the LLM
provider (Anthropic, OpenAI, Google, or any other Pydantic AI model). No provider is
hard-coded.

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
  model: anthropic:claude-opus-5       # provider:model — e.g. openai:gpt-4o
  api_key: ${ANTHROPIC_API_KEY}        # optional; env override, avoids plaintext
```

Then provide the key in the environment and run as usual:

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
uv run python -m pierpressure /path/to/config.yaml
```

In the Home Assistant add-on, the add-on cannot read a variable you set. Put the
key in the **API key** field of the add-on's Configuration tab instead, and
leave `api_key` out of `config.yaml`. See
[Turn on the explainer](../ha-addon/DOCS.md#turn-on-the-explainer).

- `enabled` — the single switch. It wires both the LLM provider and the narrative
  entity; leave it out or set it `false` to keep the explainer off.
- `model` — a Pydantic AI model spec, `provider:model-name`. Examples:
  `anthropic:claude-opus-5`, `openai:gpt-4o`, `google-gla:gemini-1.5-flash`. Defaults
  to `anthropic:claude-opus-5`. The provider prefix picks which LLM writes the prose.
  Anthropic, OpenAI, and Google are bundled; other Pydantic AI providers need their
  extra installed.
- `api_key` — **optional.** When set, it is exported to the selected provider's
  standard key variable (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`). Use
  the `${VAR}` form so the secret lives in the environment, not the file. The key is
  never logged; an unset `${VAR}` stays a visible placeholder (a "missing secret"
  rather than a blank), and the explainer degrades to no narrative rather than
  erroring. **Omit it** to let the provider read its key straight from that
  environment variable — the simplest path for non-Anthropic providers.

The explainer is bounded and fault-tolerant: each call carries a short timeout, the
result is cached on the exact verdict terms so an unchanged sky reuses one call, and
any failure (a timeout, an error, or empty text) simply produces no narrative for
that recompute. **A failing explainer never blocks or delays the verdict** — the
verdict is always published on time, and the narrative entity resolves to
`unavailable`.

## Use Home Assistant's AI Task

In the Home Assistant add-on, Home Assistant itself can write the paragraph. Set
`explainer.ai_task_entity` to an AI Task entity, such as `ai_task.openai`, and the
explainer calls Home Assistant's `ai_task.generate_data` action for that entity. The
AI integration behind it, such as OpenAI, Google Gemini or Ollama, picks the model
and holds the key. With an entity set, the explainer does not use `model` or
`api_key`.

```yaml
explainer:
  enabled: true
  ai_task_entity: ai_task.openai
```

You can set both fields on the add-on's Configuration tab instead, as **Enabled** and
**AI Task entity**. See
[Turn on the explainer](../ha-addon/DOCS.md#turn-on-the-explainer).

- `ai_task_entity` — **optional.** An entity ID of the form `ai_task.<object_id>`,
  in lowercase letters, digits and underscores. Any other value stops the service
  with a configuration error that names `explainer.ai_task_entity`.

This works **only in the Home Assistant add-on**. The request goes through the
Supervisor, with the token the Supervisor gives the add-on. Outside the add-on, such
as in a plain Docker container, there is no token. The service then logs one warning
at startup that names `explainer.ai_task_entity`, publishes every verdict as usual,
and the narrative entity reads `unavailable`.

The call has the same bounds as any other provider:

- It waits about 5 seconds. A model that takes longer, such as a local model on small
  hardware, gives no narrative for that recompute.
- Home Assistant keeps running a call the explainer gave up on, so your AI provider
  may still bill for it. The cache means this happens at most once for each changed
  verdict of a pier.
- A failed call is logged by its kind and HTTP status only, never by what Home
  Assistant said.

To make this call, the add-on asks for Home Assistant's API, which makes it an
administrator of Home Assistant. PierPressure uses that access only for this one
action ([ADR-0042](decisions/0042-addon-narrative-may-come-from-home-assistant-ai-task.md)).

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

To check the AI Task path, run the add-on with **Enabled** and **AI Task entity** set
on its Configuration tab:

1. Restart the add-on and confirm the log names the entity, for example
   `Narrative from the AI Task entity ai_task.openai`.
2. Wait for a recompute, or press the pier's refresh button.
3. Repeat the three steps above on the narrative it publishes.
