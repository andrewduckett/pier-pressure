## 1. Lock the patched runtime packages

- [ ] 1.1 [easy] The lock holds certifi 2026.10.23, which drops the compromised emSign roots (verify: uv export --frozen --no-hashes | grep -q '^certifi==2026.10.23')
- [ ] 1.2 [easy] The lock holds pyasn1 0.6.5, which fixes the quadratic BER/DER decoding (verify: uv export --frozen --no-hashes | grep -q '^pyasn1==0.6.5')
- [ ] 1.3 [easy] The lock holds opentelemetry-api 1.45.2, which bounds tracestate parsing (verify: uv export --frozen --no-hashes | grep -q '^opentelemetry-api==1.45.2')
- [ ] 1.4 [easy] No other package moves, and the lock still matches pyproject.toml (verify: uv lock --check)
- [ ] 1.5 [easy] The project's checks pass on the new lock (verify: mise run check)
