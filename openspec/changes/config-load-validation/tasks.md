## 1. One reader for settings YAML

- [x] 1.1 [medium] A zero-padded integer in `config.yaml` is read as a decimal number by a number setting: `go_threshold: 070` gives 70, `longitude: -045` gives -45, and `go_threshold: 080` gives 80 (design DD1) (verify: uv run pytest tests/test_config.py -k padded) (✓ uv run pytest tests/test_config.py -k padded passed)
- [x] 1.2 [easy] Other number forms in `config.yaml` keep their meaning: `elevation_m: 0x1A` gives 26 and `elevation_m: 1_000` gives 1000, and `yaml.safe_load("045")` is still 37 after the reader is defined (verify: uv run pytest tests/test_config.py -k number_forms) (✓ uv run pytest tests/test_config.py -k number_forms passed)
- [x] 1.3 [easy] A base-60 value in `config.yaml` is text: `go_threshold: 1:05` skips its pier while another valid pier still loads, and `id: 1:30` loads as the text `1:30` (verify: uv run pytest tests/test_config.py -k base_60) (✓ uv run pytest tests/test_config.py -k base_60 passed)
- [x] 1.4 [easy] Horizon points written as text use the same reader: `"[[045, 10], [180, 5]]"` gives the samples `(45, 10)` and `(180, 5)`, and `"[[1:30, 20], [180, 5]]"` makes the pier invalid with an error that names `horizon.points` (verify: uv run pytest tests/test_horizon_config.py -k "padded or base_60") (✓ uv run pytest tests/test_horizon_config.py -k "padded or base_60" passed)
- [x] 1.5 [easy] Horizon points given as a list in a `config.yaml` file follow the same rules: `[[045, 10], [180, 5]]` gives `(45, 10)` and `(180, 5)`, and `[[1:30, 20], [180, 5]]` skips the pier with a logged error that names it and `horizon.points` (verify: uv run pytest tests/test_horizon_config.py -k config_file) (✓ uv run pytest tests/test_horizon_config.py -k config_file passed)

## 2. Repeated pier ids [depends-on: 1]

- [x] 2.1 [medium] Loading a `config.yaml` whose piers list holds two entries with the id `backyard` raises a `ConfigError` that names `backyard`, also when one of the two entries is otherwise invalid (design DD3) (verify: uv run pytest tests/test_config.py -k repeated_id) (✓ uv run pytest tests/test_config.py -k repeated_id passed)
- [x] 2.2 [easy] Ids that differ only in letter case, `backyard` and `Backyard`, both load, and an entry whose id is not text is left to its own per-pier check (verify: uv run pytest tests/test_config.py -k repeated_id) (✓ uv run pytest tests/test_config.py -k repeated_id passed)
- [x] 2.3 [easy] The repeated-id error is one line: an id with a line break is shown escaped, several repeated ids are listed in the order they first repeat, and no other value from the entries appears (verify: uv run pytest tests/test_config.py -k repeated_id_error) (✓ uv run pytest tests/test_config.py -k repeated_id_error passed)

## 3. Add-on and docs [depends-on: 2]

- [x] 3.1 [medium] Through `load_app_config` inside the add-on, a form that lists `backyard` twice raises a `ConfigError` that names `backyard`, with no `config.yaml` and with a `config.yaml` that adds `metar_station` to `backyard` (design DD4) (verify: uv run pytest tests/test_main.py -k repeated_id) (✓ uv run pytest tests/test_main.py -k repeated_id passed)
- [x] 3.2 [easy] Through `load_app_config` inside the add-on, a form pier's `horizon_points` of `[[045, 10], [180, 5]]` gives the samples `(45, 10)` and `(180, 5)`, and `[[1:30, 20], [180, 5]]` skips that pier with a logged error that names it and `horizon.points` while the other form pier loads (verify: uv run pytest tests/test_main.py -k horizon_points) (✓ uv run pytest tests/test_main.py -k horizon_points passed)
- [ ] 3.3 [easy] The README's configuration table says each pier needs its own id, that an id that looks like a number must be quoted, that a zero-padded number such as `045` reads as 45, and that `1:30` is not a number (design DD5) (verify: grep -q "045" README.md)
- [ ] 3.4 [easy] The whole change passes the CI gate (verify: mise run check)

## Deviations Ledger

<!-- Dated notes on small departures from the plan, written during apply. Stop and ask the user about a large one. -->
