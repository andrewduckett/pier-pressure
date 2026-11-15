## ADDED Requirements

### Requirement: A failed explainer call is logged without the provider's reply

When the explainer is enabled and the LLM provider call fails, the log line that
reports the failure SHALL name only the kind of error and, when the LLM provider
answered with one, its HTTP status code. The log SHALL NOT contain the error's
text or the LLM provider's reply, because a reply to a rejected key can quote
part of that key.

#### Scenario: A rejected key's reply that quotes part of the key is not logged

- **WHEN** the explainer API key is `sk-proj-ab12marker90wxyz`
- **AND** the LLM provider rejects it with HTTP status 401 and the reply
  `Incorrect API key provided: sk-proj-ab12...wxyz`
- **THEN** one log line reports that the explainer call failed with an
  authentication error and HTTP status 401
- **AND** no log line contains `sk-proj-ab12`, `wxyz` or
  `Incorrect API key provided`

#### Scenario: A failure with no HTTP status names only the kind of error

- **WHEN** the explainer is enabled and the LLM provider call raises an error
  with no HTTP status code, whose text is `connection refused for key sk-marker`
- **THEN** one log line reports that the explainer call failed, and names the
  kind of error
- **AND** no log line contains `sk-marker` or `connection refused`
