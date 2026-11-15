## MODIFIED Requirements

### Requirement: The explainer sits behind a provider interface

The explainer SHALL obtain prose through a provider interface so the provider is
swappable and can be replaced by a test double. The default provider SHALL use an
LLM service. The AI Task provider SHALL use a Home Assistant AI Task entity. The
explainer's provider SHALL be the only component permitted to make a network
call; no other part of the explainer or core reaches the network. Selecting or
omitting a provider SHALL NOT change the verdict document.

#### Scenario: A test double replaces the LLM provider

- **WHEN** the explainer is configured with a non-LLM provider double
- **THEN** it produces narratives through that double with no network call
- **AND** the verdict document is unchanged by the choice of provider

#### Scenario: The AI Task provider leaves the verdict document unchanged

- **WHEN** the same verdict is produced once with the explainer off and once
  with the explainer using an AI Task entity
- **THEN** the two verdict documents are byte-identical

## ADDED Requirements

### Requirement: An AI Task entity setting selects Home Assistant's AI Task

When the explainer is enabled inside a Home Assistant add-on and
`explainer.ai_task_entity` is set, the explainer SHALL obtain its prose from that
AI Task entity through Home Assistant's `ai_task.generate_data` action. It SHALL
NOT call an LLM service directly, and SHALL NOT use `explainer.model` or
`explainer.api_key`.

#### Scenario: An entity setting sends the request to Home Assistant

- **WHEN** the explainer is enabled inside an add-on with
  `explainer.ai_task_entity` set to `ai_task.openai`
- **AND** `explainer.api_key` is set to `sk-8c41f2`
- **THEN** the explainer's only network request for a narrative goes to Home
  Assistant's `ai_task.generate_data` action for `ai_task.openai`
- **AND** no request goes to an LLM service, and no request carries `sk-8c41f2`

### Requirement: The AI Task entity setting is an ai_task entity ID

`explainer.ai_task_entity` SHALL be text of the form `ai_task.<object_id>`, where
the object ID holds only lowercase letters, digits and underscores. Any other
value SHALL stop the process with a configuration error that names
`explainer.ai_task_entity` and does not contain the value.

#### Scenario: An entity of another domain is rejected

- **WHEN** `config.yaml` sets `explainer.ai_task_entity` to `light.kitchen`
- **THEN** the process stops with a configuration error that names
  `explainer.ai_task_entity`
- **AND** neither the error nor the log contains `light.kitchen`

#### Scenario: An AI Task entity ID is accepted

- **WHEN** `config.yaml` sets `explainer.ai_task_entity` to `ai_task.google_ai_task`
- **THEN** the configuration loads

### Requirement: The AI Task request goes through the Supervisor's Core API

The AI Task provider SHALL send `POST
http://supervisor/core/api/services/ai_task/generate_data?return_response` with
the header `Authorization: Bearer <Supervisor token>`. The JSON body SHALL hold
`task_name`, `instructions` and `entity_id`, set to the configured entity, and
nothing else.

#### Scenario: The request names the entity and asks for the response

- **WHEN** the AI Task provider asks `ai_task.openai` for a narrative, with the
  Supervisor token `tok-3e9a`
- **THEN** it sends one POST to
  `http://supervisor/core/api/services/ai_task/generate_data?return_response`
- **AND** the request carries `Authorization: Bearer tok-3e9a`
- **AND** the JSON body's keys are exactly `task_name`, `instructions` and
  `entity_id`, and `entity_id` is `ai_task.openai`

### Requirement: The AI Task instructions are the explainer's existing prompt

The `instructions` the AI Task provider sends SHALL be the explainer's system
framing followed by the prompt text built from the verdict document, the same
words the default provider sends to its LLM.

#### Scenario: The instructions hold the framing and the verdict prompt

- **WHEN** the AI Task provider asks for a narrative of a verdict
- **THEN** its `instructions` start with the explainer's system framing
- **AND** they end with the prompt text the explainer built from that verdict

### Requirement: The narrative is the text of the AI Task reply

When Home Assistant answers with HTTP status 200 and a JSON body whose
`service_response.data` is non-empty text, the narrative SHALL be that text with
leading and trailing spaces removed. Any other answer SHALL count as a failed
provider call: no narrative, and the verdict still delivered.

#### Scenario: A text reply becomes the narrative

- **WHEN** Home Assistant answers with status 200 and the body
  `{"changed_states": [], "service_response": {"conversation_id": "c1", "data": " Clear skies. "}}`
- **THEN** the narrative is `Clear skies.`

#### Scenario: A reply without text gives no narrative

- **WHEN** Home Assistant answers with status 200 and a `service_response.data`
  that is a mapping, empty text, or missing
- **THEN** the explainer produces no narrative text for that recompute
- **AND** the verdict is still delivered

#### Scenario: An error status gives no narrative

- **WHEN** Home Assistant answers with status 400, 401, 500 or 502
- **THEN** the explainer produces no narrative text for that recompute
- **AND** the verdict is still delivered

### Requirement: A Home Assistant that does not answer never delays the verdict past the explainer's bound

When Home Assistant or the Supervisor does not answer the AI Task request, or
cannot be reached, the verdict SHALL still be delivered, and the explainer SHALL
give up within the same per-call time bound as the default provider.

#### Scenario: A request that never answers gives up within the bound

- **WHEN** the AI Task request gets no answer
- **THEN** the explainer returns no narrative within its per-call time bound
- **AND** the verdict for that pier is delivered

#### Scenario: A refused connection gives no narrative

- **WHEN** the connection to the Supervisor is refused
- **THEN** the explainer produces no narrative text for that recompute
- **AND** the verdict is still delivered

### Requirement: A failed AI Task call is logged without the reply or the token

When the AI Task call fails, the log line that reports it SHALL name only the
kind of error and, when Home Assistant answered, its HTTP status code. No log
line SHALL contain the reply's text or the Supervisor token.

#### Scenario: A rejected entity's reply is not logged

- **WHEN** the Supervisor token is `tok-3e9a`
- **AND** Home Assistant answers with status 400 and the body
  `{"message": "AI Task entity ai_task.marker90 not found."}`
- **THEN** one log line reports that the explainer call failed, with HTTP
  status 400
- **AND** no log line contains `marker90`, `not found` or `tok-3e9a`

### Requirement: An AI Task entity outside an add-on gives no narrative

When the explainer is enabled and `explainer.ai_task_entity` is set, but the
process does not run inside a Home Assistant add-on, the explainer SHALL make no
network call and produce no narrative. The service SHALL log one warning at
startup that names `explainer.ai_task_entity` and says it works only in the
add-on, and SHALL still deliver every verdict.

#### Scenario: A Docker install with an entity still publishes verdicts

- **WHEN** the process runs with no Supervisor token
- **AND** `config.yaml` enables the explainer and sets `explainer.ai_task_entity`
  to `ai_task.openai`
- **THEN** the service publishes a verdict for each pier
- **AND** the narrative entity resolves to unavailable
- **AND** one startup warning names `explainer.ai_task_entity` and the add-on
- **AND** no request goes to an LLM service or to Home Assistant

### Requirement: The startup log names the AI Task entity in use

When the explainer uses an AI Task entity, the service SHALL log at startup that
the narrative comes from that entity, and name it. When `explainer.api_key` is
also set, the same log SHALL say the API key is not used, and SHALL NOT contain
the key.

#### Scenario: An unused key is reported without its value

- **WHEN** the explainer is enabled inside an add-on with
  `explainer.ai_task_entity` set to `ai_task.openai` and `explainer.api_key` set
  to `sk-8c41f2`
- **THEN** a startup log line names `ai_task.openai` and says the API key is not
  used
- **AND** no log line contains `sk-8c41f2`
