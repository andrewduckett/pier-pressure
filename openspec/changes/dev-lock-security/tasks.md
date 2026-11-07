## 1. Lock the patched dev-toolchain packages

- [ ] 1.1 [easy] The lock holds virtualenv 21.15.6, which fixes the activation-script and seeding advisories (verify: uv export --frozen --no-hashes | grep -q '^virtualenv==21.15.6')
- [ ] 1.2 [easy] The lock holds filelock 4.2.9, which fixes the lock-file symlink and stale-lock advisories (verify: uv export --frozen --no-hashes | grep -q '^filelock==4.2.9')
- [ ] 1.3 [easy] No package moves beyond virtualenv, python-discovery and filelock, and the lock still matches pyproject.toml (verify: uv lock --check)
- [ ] 1.4 [easy] Every pre-commit hook runs on the new virtualenv and filelock (verify: uv run pre-commit run --all-files)
- [ ] 1.5 [easy] The project's checks pass on the new lock (verify: mise run check)
