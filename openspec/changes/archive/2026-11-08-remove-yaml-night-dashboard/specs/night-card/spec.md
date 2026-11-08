## MODIFIED Requirements

### Requirement: More cloud is darker
The card SHALL shade each cell in a cloud row in one of seven blues. From lightest to darkest they are `#cde2fb`, `#9ec5f4`, `#6da7ec`, `#3987e5`, `#256abf`, `#184f95` and `#0d366b`. A value `v` in percent SHALL take shade step `min(6, floor(v / 15))`, where step 0 is the lightest.

#### Scenario: Clear and overcast
- **WHEN** the Cloud cover forecast holds 0 at one hour, 44 at another and 100 at a third
- **THEN** the cells are shaded `#cde2fb`, `#6da7ec` and `#0d366b`
