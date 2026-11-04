## ADDED Requirements

### Requirement: The catalog offers Open-Meteo's air-quality forecast as a provider

The catalog SHALL offer a provider with the key `open_meteo_air_quality` and the
display name `Open-Meteo air quality`. It SHALL need no key. It SHALL declare
`aerosol_optical_depth` and `pm2_5`, and no bundle. It SHALL NOT declare cloud
cover or any other variable. It SHALL be listed, filled, fetched and reported
like any other provider.

#### Scenario: The catalog offers the air-quality provider

- **WHEN** the catalog is read
- **THEN** it holds `open_meteo_air_quality` with the display name `Open-Meteo air quality`, needing no key
- **AND** its declaration lists `aerosol_optical_depth` then `pm2_5`, and no bundle

#### Scenario: The air-quality provider is accepted in the provider list

- **WHEN** the configuration lists `providers: [open_meteo_hrrr, open_meteo_air_quality]`
- **THEN** startup succeeds and the provider order is `open_meteo_hrrr` then `open_meteo_air_quality`

#### Scenario: The air-quality provider alone does not satisfy the cloud rule

- **WHEN** the configuration lists `providers: [open_meteo_air_quality]`
- **THEN** startup fails with an error that says the list must include a provider that needs no key and supplies cloud cover

### Requirement: Air-quality variables are carried as reported

The snapshot SHALL carry `aerosol_optical_depth` as the air-quality forecast
reports it, with no unit, and `pm2_5` in micrograms per cubic metre, as
reported, with no rounding or conversion. An hour whose value is blank SHALL
leave that variable unavailable for the hour, and the other variable SHALL be
unaffected.

#### Scenario: Both values are carried for an hour the forecast reports fully

- **WHEN** the air-quality forecast reports an aerosol optical depth of `0.14` and a PM2.5 of `8.8` for an hour
- **THEN** that hour in the snapshot carries `aerosol_optical_depth` `0.14` and `pm2_5` `8.8`, each from `open_meteo_air_quality`

#### Scenario: One blank value leaves the other present

- **WHEN** the air-quality forecast reports a PM2.5 of `8.8` and a blank aerosol optical depth for an hour
- **THEN** that hour's `aerosol_optical_depth` is unavailable
- **AND** that hour's `pm2_5` is `8.8`

### Requirement: The air-quality provider's issue time is its fetch time

The air-quality provider SHALL record the time of its fetch as the issue time of
its data, as `open_meteo` does, because the air-quality response gives none.

#### Scenario: The air-quality provider stamps the fetch time

- **WHEN** `open_meteo_air_quality` is fetched at 21:05 and returns readings
- **THEN** the `aerosol_optical_depth` and `pm2_5` series carry an issue time of 21:05

## MODIFIED Requirements

### Requirement: Providers are configured as an ordered list

The configuration SHALL accept a `conditions.providers` list of provider keys,
preferred first. When the `conditions` block or the list is absent, the list
SHALL be `[open_meteo, seven_timer, open_meteo_air_quality]`.

#### Scenario: An absent block gives the default order

- **WHEN** the configuration has no `conditions` block
- **THEN** the provider order is `open_meteo`, `seven_timer`, `open_meteo_air_quality`

#### Scenario: A configured order is kept as written

- **WHEN** the configuration lists `providers: [seven_timer, open_meteo]`
- **THEN** the provider order is `seven_timer` then `open_meteo`

### Requirement: Each provider declares its variables and bundles

Each provider SHALL declare the variables it supplies, named by their variable
keys, and which of them form a bundle. A variable key need not be a timeline
key. A declaration SHALL be fixed: it SHALL NOT change with what a fetch
returned.

#### Scenario: Open-Meteo declares the cloud bundle and the weather variables

- **WHEN** the Open-Meteo provider's declaration is read
- **THEN** it lists `cloud_cover`, `cloud_low`, `cloud_mid`, `cloud_high`, `wind_gust`, `temperature`, `dew_point`, `humidity`, `wind_speed`, `wind_direction` and `precipitation_probability`
- **AND** its one bundle holds `cloud_cover`, `cloud_low`, `cloud_mid` and `cloud_high`

#### Scenario: 7Timer! declares seeing and transparency

- **WHEN** the 7Timer! provider's declaration is read
- **THEN** it lists `seeing` and `transparency` and no bundle

### Requirement: The catalog offers the National Weather Service as a provider

The catalog SHALL offer a provider with the key `nws` and the display name
`NWS`. It SHALL need no key. It SHALL declare `cloud_cover`, `wind_gust`,
`wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and
`precipitation_probability`, and no bundle. It SHALL NOT declare `cloud_low`,
`cloud_mid`, `cloud_high`, `seeing` or `transparency`. It SHALL be listed,
filled, fetched and reported like any other provider, and it SHALL NOT be in
the default provider order.

#### Scenario: The catalog offers NWS

- **WHEN** the catalog is read
- **THEN** it holds `nws` with the display name `NWS`, needing no key
- **AND** its declaration lists `cloud_cover`, `wind_gust`, `wind_speed`, `wind_direction`, `temperature`, `dew_point`, `humidity` and `precipitation_probability`, and no bundle

#### Scenario: NWS is accepted in the provider list

- **WHEN** the configuration lists `providers: [nws, open_meteo_hrrr, seven_timer]`
- **THEN** startup succeeds and the provider order is `nws`, `open_meteo_hrrr`, `seven_timer`

#### Scenario: NWS alone satisfies the cloud rule

- **WHEN** the configuration lists `providers: [nws]`
- **THEN** startup succeeds, because `nws` needs no key and supplies cloud cover

#### Scenario: The default order does not include NWS

- **WHEN** the configuration has no `conditions` block
- **THEN** the provider order is `open_meteo`, `seven_timer`, `open_meteo_air_quality`
- **AND** it does not include `nws`
