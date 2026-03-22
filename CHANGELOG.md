# Changelog

All notable changes to the Titan V12.0 Antidetect Device Platform.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [12.0.0] — 2025-03-21

### Added
- **`server/routers/viewer.py`** — Built-in device viewer endpoint with live screenshots and touch/key input (replaces unreliable ws-scrcpy dependency)
- **`core/device_manager.py`** — `_launch_cvd_detached()` with `start_new_session=True` so VMs survive API restarts
- **`core/device_manager.py`** — `_kill_stale_cvd_processes()` to clean orphaned modem_simulator, netsimd, etc. before launch
- **`core/device_manager.py`** — `_ensure_cvd_home_symlinks()` for etc/lib64/usr directories required by assemble_cvd
- **`core/device_manager.py`** — `_post_boot_setup()` disables screen timeout and wakes device after boot

### Fixed
- **`core/device_manager.py`** — GPU auto-detect now requires `/dev/dri/renderD*` before selecting drm_virgl (prevents launch failures)
- **`core/device_manager.py`** — cvd_config isolation: per-device etc directory with selective symlinks (prevents preset corruption)
- **Branding** — Updated all V11.3 references to V12.0 across server, desktop, and core modules

---

## [11.3.5] — 2025-03-19

### Added
- **`core/exceptions.py`** — Structured exception hierarchy (`TitanError`, `ADBConnectionError`, `PatchPhaseError`, `InjectionError`, `WalletProvisionError`, etc.)
- **`core/models.py`** — Typed Pydantic/dataclass models (`PatchPhase` enum, `PatchReport`, `InjectionResult`, `ProfileData`, `CardData`, `DeviceInfo`, API response models)
- **`core/py.typed`** — PEP 561 type marker for static analysis
- **`pyproject.toml`** — Unified project config (pytest, ruff, mypy, coverage, dependencies)
- **`.pre-commit-config.yaml`** — Ruff lint/format + pre-commit hooks
- **`.github/workflows/ci.yml`** — GitHub Actions CI: unit tests, ruff lint, mypy (Python 3.10/3.11/3.12 matrix)
- **`tests/conftest.py`** — Shared pytest fixtures (`mock_adb`, `sample_profile`, `sample_card_data`, `temp_data_dir`)
- **`tests/mocks/adb_mock.py`** — `MockADB` class for offline testing (intercepts `subprocess.run` ADB calls)
- **`tests/test_anomaly_patcher.py`** — Unit tests: IMEI/ICCID/serial generators, Luhn validation, PatchReport, mocked needs_repatch
- **`tests/test_profile_injector.py`** — Unit tests: InjectionResult, SQLite batch injection patterns, browser resolution
- **`tests/test_wallet_provisioner.py`** — Unit tests: detect_network, detect_issuer, generate_dpan (Luhn + Token BIN), WalletProvisionResult
- **`tests/test_forge.py`** — Unit tests: profile generation, contacts, call logs, SMS, browser data, age boundaries, locale variants
- **`tests/e2e/README.md`** — E2E test documentation
- **`scripts/postinstall.sh`** — Post-install automation (venv, .env, systemd service, data dirs)
- **`CHANGELOG.md`** — This file
- **`docs/adr/`** — Architecture Decision Records

### Changed
- **`core/anomaly_patcher.py`** — Added `quick_repatch()`, `needs_repatch()`, `_save_patch_config()` for fast reboot recovery (~30s vs 200-365s); `full_patch()` now saves config to `/data/local/tmp/titan_patch_config.json`
- **`core/profile_injector.py`** — Replaced O(n) ADB content-insert contact injection with SQLite batch (pull→modify→push); stops contacts provider before DB writes to prevent crash (GAP-B1, GAP-B4)
- **`core/gapps_bootstrap.py`** — Chrome install failure auto-fallback to Kiwi Browser (GAP-B6)
- **`server/routers/stealth.py`** — Converted `/patch` to background job with `/patch-status/{job_id}` polling; added `/needs-repatch` endpoint (GAP-B2, GAP-B3)
- **`server/routers/provision.py`** — Converted `age-device` to background job; added `proxy_url` field and proxy config step in full-provision pipeline (GAP-B2, GAP-B7)
- **`server/titan_api.py`** — Added `/health/live` and `/health/ready` K8s-convention aliases; bumped version to 11.3.5
- **`desktop/main.js`** — `TITAN_DATA` defaults to `/opt/titan/data` in packaged mode; added `--no-sandbox`, `--disable-gpu`, `--disable-software-rasterizer` flags; extended PYTHONPATH
- **`desktop/package.json`** — Bumped to v11.3.5
- **`docker/Dockerfile.titan-api-prod`** — Multi-stage build (builder + runtime)
- **`docker/docker-compose.yml`** — Added healthcheck for titan-api service
- **`.gitignore`** — Added `.mypy_cache/`, `.pytest_cache/`, `.coverage`, `htmlcov/`

### Fixed
- Contact injection now 50x faster (SQLite batch vs per-contact ADB insert)
- Contacts Storage no longer crashes after re-patching (provider stopped before DB writes)
- Stealth patch no longer times out on 120s HTTP deadline (runs as background job)
- Age-device endpoint no longer times out (background job with poll)
- Resetprop changes survive reboots via `quick_repatch()` auto-detection

## [11.3.4] — 2025-03-18

### Changed
- Desktop app Electron build pipeline improvements
- Console SPA tab refinements

## [11.3.3] — 2025-03-17

### Added
- Wallet verification endpoint (`/api/stealth/{id}/wallet-verify`)
- WebSocket real-time device events (`/ws/{device_id}`)

### Fixed
- AI router error handling for missing Ollama models

## [11.3.2] — 2025-03-16

### Added
- Full 62-tab console SPA with Alpine.js + Tailwind CSS
- 16 FastAPI router modules (devices, stealth, genesis, provision, agent, intel, network, cerberus, targets, kyc, admin, dashboard, settings, bundles, ai, ws, training)
- Job manager with TTL cleanup and JSON persistence
- Trust scorer (14-check canonical scorer)

## [11.3.1] — 2025-03-15

### Added
- Anomaly patcher: 26 phases, 103+ detection vectors
- Profile injector: 11 injection targets
- Wallet provisioner: Google Pay, Play Store, Chrome autofill, GMS billing
- Android profile forge: circadian-weighted data generation
- GApps bootstrap: automated GMS/Play Store/Chrome installation
- Device presets: 30+ Android device identities

## [11.3.0] — 2025-03-14

### Added
- Initial Cuttlefish-based architecture (migrated from Redroid)
- Device manager with KVM VM lifecycle (launch_cvd/stop_cvd)
- ADB utilities with error classification and circuit breaker
- Docker Compose stack (API + ws-scrcpy + nginx + SearXNG)
