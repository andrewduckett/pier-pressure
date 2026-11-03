## ADDED Requirements

### Requirement: The snapshot keeps alternates beside the filled series

For each variable, the snapshot SHALL keep as alternates the series of every provider after the filling one, in configured order, that returned the variable: at least one hour of its forecast carries a value for it, or for another variable in the same bundle. An alternate SHALL carry that provider's hourly values, its key and the issue time of its data, exactly as a filled series does. A provider that returned nothing for the variable, or whose fetch failed, SHALL leave no alternate. The filled series, the hours it covers and the value it gives for each hour SHALL be the same as they would be with no alternates.

#### Scenario: A later provider's cloud becomes an alternate

- **WHEN** the order is `open_meteo` then `open_meteo_hrrr`, both return `cloud_cover` for the dark window, and the first gives `40` for 21:00 where the second gives `70`
- **THEN** the `cloud_cover` series carries `open_meteo` and `40` at 21:00
- **AND** `cloud_cover` has one alternate, carrying `open_meteo_hrrr`, its issue time and `70` at 21:00

#### Scenario: Alternates keep the configured order

- **WHEN** three providers in order each return `cloud_cover`
- **THEN** `cloud_cover` has two alternates, the second provider's first and the third provider's second

#### Scenario: An alternate never fills an hour the filled series lacks

- **WHEN** the first provider in order returns `cloud_cover` for 20:00 to 23:00 only, and the second returns `cloud_cover` for 20:00 to 03:00
- **THEN** the `cloud_cover` value for 01:00 is unavailable
- **AND** the alternate carries the second provider's values for 20:00 to 03:00

#### Scenario: A provider that returned nothing leaves no alternate

- **WHEN** the second provider in order returns rows whose `cloud_cover` is blank in every hour
- **THEN** `cloud_cover` has no alternate from that provider

#### Scenario: A failed provider leaves no alternate

- **WHEN** the second provider in order fails to fetch
- **THEN** no variable has an alternate from that provider
- **AND** the snapshot is otherwise the same as if that provider were not listed

#### Scenario: A losing bundle becomes alternates member by member

- **WHEN** the first provider in order returns `cloud_cover` but no layer, and the second returns `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`
- **THEN** each of the four variables has one alternate carrying the second provider's key
- **AND** the filled `cloud_low`, `cloud_mid` and `cloud_high` series still carry the first provider's key with no values

#### Scenario: Alternates do not change the verdict's cloud reading

- **WHEN** two verdicts are produced for the same pier and instant from snapshots that differ only in whether a `cloud_cover` alternate is present
- **THEN** the two documents have the same `verdict`, `score`, `scored_window` and `timeline` cloud-cover values
