# Night dashboard

A Home Assistant dashboard that shows tonight's verdict for one pier.

## The dashboard YAML

```yaml
title: PierPressure
views:
  - title: Tonight
    type: sections
    sections:
      - type: grid
        cards:
          - type: markdown
            content: "{{ states('sensor.pierpressure_backyard_verdict') }}"
```
