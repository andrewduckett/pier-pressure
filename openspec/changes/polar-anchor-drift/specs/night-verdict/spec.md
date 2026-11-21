## ADDED Requirements

### Requirement: At the exact geographic poles, the continuous-night anchor is the UTC calendar day

At a pier whose latitude is exactly 90 or −90 degrees, the sun has no local
solar noon. There, the day that anchors continuous polar night SHALL be the
UTC calendar day that holds the evaluation instant, from 00:00 UTC to 00:00
UTC the next day. It SHALL take the place of the local solar day wherever this
spec names that day.

#### Scenario: At the north pole in December, the dark window is the UTC day

- **WHEN** a verdict is produced for a pier at latitude 90 and longitude 0, at the evaluation instant 2026-12-21T12:00:00Z, in continuous polar night
- **THEN** `dark_window.start` is 2026-12-21T00:00:00Z
- **AND** `dark_window.end` is 2026-12-22T00:00:00Z

#### Scenario: At the south pole in June, the dark window is the UTC day

- **WHEN** a verdict is produced for a pier at latitude −90 and longitude 0, at the evaluation instant 2026-06-21T12:00:00Z, in continuous polar night
- **THEN** `dark_window.start` is 2026-06-21T00:00:00Z
- **AND** `dark_window.end` is 2026-06-22T00:00:00Z
