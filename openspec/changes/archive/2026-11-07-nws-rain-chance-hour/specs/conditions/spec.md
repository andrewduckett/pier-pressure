## MODIFIED Requirements

### Requirement: NWS periods are expanded onto the hourly grid within a 72-hour horizon

Each NWS value SHALL be held across every clock hour its period covers, so the
result is on the same hourly grid as every other provider. Precipitation
probability is the exception: because its value at an hour is the chance for
the hour that ends there, each precipitation probability value SHALL be held on
the clock hours one hour after each hour its period covers. The provider SHALL
keep only hours within 72 hours of the earliest period start in the payload.
Hours past that horizon SHALL be dropped, precipitation probability hours
included, and hours within it that no period covers SHALL stay absent.

#### Scenario: A three-hour period is held across its hours

- **WHEN** NWS reports sky cover `45` for the period starting at 21:00 lasting three hours
- **THEN** the readings for 21:00, 22:00 and 23:00 each carry a cloud cover of `45`

#### Scenario: A period spanning days is held across its hours

- **WHEN** NWS reports a wind speed for a period starting at 06:00 lasting one day and six hours
- **THEN** the readings from 06:00 to 11:00 the next day each carry that wind speed

#### Scenario: A precipitation probability period is held on the hours that end within it

- **WHEN** NWS reports a precipitation probability of `40` for the period starting at 18:00 lasting six hours
- **THEN** the readings for 19:00, 20:00, 21:00, 22:00, 23:00 and 00:00 the next day each carry a precipitation probability of `40`
- **AND** the reading for 18:00, if one exists, carries no precipitation probability

#### Scenario: Precipitation probability moves and the other variables do not

- **WHEN** NWS reports sky cover `45` and a precipitation probability of `20`, each for the period starting at 21:00 lasting one hour
- **THEN** the reading for 21:00 carries a cloud cover of `45` and no precipitation probability
- **AND** the reading for 22:00 carries a precipitation probability of `20` and no cloud cover

#### Scenario: A period that straddles the horizon is cut at it

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a sky cover period starts at 16:00 on day four lasting three hours
- **THEN** the readings for 16:00 and 17:00 on day four carry that sky cover
- **AND** no reading exists for 18:00 on day four

#### Scenario: A precipitation probability hour at the horizon is cut

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a precipitation probability period starts at 16:00 on day four lasting two hours
- **THEN** the reading for 17:00 on day four carries that precipitation probability
- **AND** no reading exists for 18:00 on day four

#### Scenario: A period that starts past the horizon is dropped

- **WHEN** the earliest period in the payload starts at 18:00 on day one, and a period starts at 19:00 on day four
- **THEN** no reading exists for 19:00 on day four

#### Scenario: Periods for different variables stay independent

- **WHEN** NWS reports sky cover for 21:00 to 23:00 and temperature for 21:00 only
- **THEN** the readings for 22:00 and 23:00 carry a cloud cover and no temperature
