# Titan V11.3 — Copilot Workspace Instructions

## Purpose
This file provides workspace-specific instructions for GitHub Copilot and AI agents working in the Titan V11.3 Android Cloud Device Platform codebase. It encodes conventions, workflows, and project-specific knowledge to maximize agent productivity and code quality.

---

## Key Conventions
- **Cuttlefish-Only:** All device virtualization uses Cuttlefish (KVM-based) VMs. Legacy Redroid/VMOS code is obsolete.
- **DeviceManager:** All device lifecycle, patching, and registry logic is centralized in `core/device_manager.py`.
- **AI Automation:** The `DeviceAgent` (core/device_agent.py) implements a See→Think→Act loop for autonomous Android control. Use this for any agent-driven device automation.
- **Patch Phases:** Anomaly patching is handled by the 26-phase engine in `core/anomaly_patcher.py`. Always invoke this after device creation.
- **Profile/Wallet Injection:** Use `core/profile_injector.py` and `core/wallet` for all identity and payment profile operations. Do not duplicate logic.
- **Test Execution:** E2E tests require a live Cuttlefish VM and are run via scripts in `scripts/` (see `tests/e2e/README.md`).
- **Documentation:** All technical docs are in `docs/`. Link to these instead of duplicating content in code or comments.

---

## Build & Test Commands
- **Build image:** `build/build-image.sh`
- **Install Zygisk modules:** `build/install-zygisk-modules.sh`
- **Patch boot (Magisk):** `build/patch-boot-magisk.sh`
- **Run E2E tests:** See `tests/e2e/README.md` for scripts and prerequisites.

---

## Project Structure
- `core/`: All core logic (device, patching, agent, injection, etc.)
- `wallet/`: Wallet and payment profile logic
- `scripts/`: Automation and test scripts
- `docs/`: All documentation (see `docs/README.md` for index)

---

## Pitfalls & Gotchas
- **No Redroid/VMOS:** Do not reference or revive legacy backends.
- **Device State:** Always update the JSON state file in `data/devices/` when modifying device state.
- **Patch Order:** Always patch before injecting profiles or wallets.
- **Test Environment:** E2E tests require a running Cuttlefish VM and Titan API server.

---

## Example Prompts
- "Create a new device preset for a Samsung S24 Ultra."
- "Add a new anomaly patch phase for /proc/net spoofing."
- "Update the DeviceAgent to support a new LLM model."
- "Write an E2E test for wallet injection."

---

## Related Customizations
- **/create-agent**: For specialized device automation or patching workflows.
- **/create-skill**: For encoding new domain knowledge (e.g., new patch phases, device types).
- **/create-instruction**: For area-specific agent instructions (e.g., wallet, patcher, agent).

---

## Link, Don’t Embed
When referencing technical details, always link to the relevant file in `docs/` or the codebase. Do not duplicate documentation or code snippets in this file.
