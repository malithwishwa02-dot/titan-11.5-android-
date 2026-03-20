---
name: codebase-auditor
description: "Deep codebase audit for Titan-X Android. Use when: finding gaps, stubs, placeholders, half-implemented code, TODO/FIXME/HACK markers, dead imports, missing error handling, hardcoded values, test coverage gaps, v12 spec delta, or generating implementation task lists. Scans core/, server/, scripts/, console/, desktop/, docker/, tests/, wallet/, cuttlefish/ exhaustively."
---

# Titan-X Codebase Auditor

Deep-analysis skill that scans every directory, file, and function in the Titan-X workspace to identify gaps, stubs, incomplete implementations, and generate actionable task lists.

## When to Use
- Audit the full codebase for implementation gaps
- Find TODO/FIXME/HACK/PLACEHOLDER/STUB/XXX markers
- Identify half-finished functions (`pass`, `return None`, `NotImplementedError`)
- Detect dead imports, dead code, unreachable paths
- Check error handling coverage on I/O, subprocess, ADB calls
- Find hardcoded values (IPs, credentials, paths, model names)
- Compare current implementation against v12 upgrade spec
- Generate a prioritized task/fix list
- Pre-flight check before deployment or PR

## Procedure

### Phase 1: Discovery Scan
Scan every Python/JS/Shell file. Run these searches in parallel:

1. **Stubs & placeholders**
   ```
   grep -rn "TODO\|FIXME\|HACK\|XXX\|PLACEHOLDER\|STUB\|WIP\|NOT IMPLEMENTED\|TEMP" --include="*.py" --include="*.js" --include="*.sh"
   grep -rn "pass$\|return None$\|return {}$\|raise NotImplementedError" --include="*.py"
   grep -rn '"stub": True\|"stub":True' --include="*.py"
   ```

2. **Dead imports**
   ```
   # For each .py file, extract imports and check usage
   # Focus on: ImportError catch-all patterns that silently degrade
   grep -rn "except ImportError" --include="*.py"
   grep -rn "except.*:.*pass$" --include="*.py"
   ```

3. **Missing error handling**
   ```
   grep -rn "subprocess\.\|_adb\|adb_shell\|adb_push\|run_in_terminal" --include="*.py" | grep -v "try\|except\|catch"
   ```

4. **Hardcoded values**
   ```
   grep -rn "127\.0\.0\.1\|localhost\|0\.0\.0\.0" --include="*.py" --include="*.js"
   grep -rn "/opt/titan\|/data/data/\|/sdcard/" --include="*.py"
   grep -rn "password\|api_key\|secret\|token" --include="*.py" --include="*.sh" -i
   ```

5. **Test coverage**
   ```
   # List all core/ modules, then check which have corresponding test files
   ls core/*.py | sed 's|core/||' | while read f; do test -f "tests/test_$f" && echo "✓ $f" || echo "✗ $f"; done
   ```

### Phase 2: Structural Analysis

For each directory, analyze:

| Directory | Check |
|-----------|-------|
| `core/` | Every public class/function has implementation (not stub). Sensor, wallet, profile forge, anomaly patcher completeness. |
| `server/routers/` | Every endpoint returns real data (not `"stub": True`). All imports resolve. Response models match. |
| `server/middleware/` | Auth, rate limiting, CPU monitoring all functional. |
| `console/` | All API calls in frontend have matching backend endpoints. Error states handled. |
| `desktop/` | Electron app launches, tray works, setup wizard complete. |
| `docker/` | All services defined, health checks present, no hardcoded paths. |
| `tests/` | Unit, integration, e2e directories populated. conftest has fixtures. |
| `scripts/` | No deprecated code in active paths. No hardcoded credentials. |
| `wallet/` | Directory populated or removed. Imports from other modules resolve. |
| `cuttlefish/` | Launch config template valid. init.d scripts present. |

### Phase 3: V12 Spec Delta

Compare implementation against [v12 upgrade spec](../../titan-v12-genesis-provisioner-upgrade.md):

| V12 Feature | Check In |
|-------------|----------|
| Life-Path Coherence | `core/android_profile_forge.py`, `server/routers/genesis.py` — calendar/email/GPS correlation |
| Synthetic Social Graph (Hive) | Any cross-device contact/WiFi/SMS coordination code |
| Biometric Sensor Replay | `core/sensor_simulator.py` — continuous injection daemon called from production code |
| Ghost SIM v2.0 | `libril` hooks, virtual modem, cell tower mocking for Cuttlefish |
| Dynamic Wallet Tokenization (HCE) | Kernel-level NFC emulation, `HCEBridge` class |
| Immune System Watchdogs | Syscall interception, probe detection, honeypot props |

### Phase 4: Report Generation

Produce a structured report with:

1. **Summary stats**: total issues by severity (Critical/High/Medium/Low)
2. **Per-directory breakdown**: file → line → category → severity → description
3. **V12 gap matrix**: feature → implementation % → missing pieces
4. **Prioritized task list**: ordered by severity, then by dependency chain
5. **Quick wins**: issues fixable in <30 min each

### Severity Classification

| Level | Definition |
|-------|-----------|
| **Critical** | Feature completely missing, security vulnerability, hardcoded credentials, core pipeline broken |
| **High** | Stub returning fake data in production, missing error handling on critical path, 0% test coverage for module |
| **Medium** | Partial implementation, dead code, hardcoded non-secret values, missing type hints on public API |
| **Low** | Code style, backup files in repo, minor optimization, documentation gaps |

## Current Gap Registry

The latest audit findings are maintained in [./references/gap-registry.md](./references/gap-registry.md). Load this file to see the full inventory without re-scanning.

Key stats from last audit (v11.3):
- **125+ files** across 10 directories
- **81 identified issues** (8 Critical, 23 High, 18 Medium, 12 Low)
- **V12 implementation gap**: ~65% of specified features missing
- **Test coverage**: <5% overall, 0% for 18 API routers
- **Stub endpoints**: 16 returning `"stub": True`
- **Missing modules**: 5 imports reference non-existent modules
- **Hardcoded credentials**: 1 confirmed (visual_pipeline_test.py:320)

## Output Format

Always produce output as a markdown table or checklist that can be directly converted to GitHub Issues or TODO items. Example:

```markdown
### Critical Tasks
- [ ] **[CRITICAL]** Implement `gpu_reenact_client` module — KYC deepfake pipeline non-functional (server/routers/kyc.py:25)
- [ ] **[CRITICAL]** Remove hardcoded password from scripts/visual_pipeline_test.py:320
- [ ] **[CRITICAL]** Implement Ghost SIM v2.0 for Cuttlefish — apps see "No SIM" (v12 spec §2.A)

### High Priority
- [ ] **[HIGH]** Replace 16 stub endpoints with real implementations (server/routers/network.py, targets.py, kyc.py, settings.py)
- [ ] **[HIGH]** Add try/except to 200+ bare subprocess/ADB calls in core/
```
