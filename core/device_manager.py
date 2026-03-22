"""
Titan V12.0 — Device Manager (Cuttlefish KVM Backend)
Creates, destroys, patches, and manages Cuttlefish Android virtual machines.
Each device gets: unique ADB port, KVM instance, identity preset, anomaly patching.

Cuttlefish uses launch_cvd / stop_cvd binaries to manage full Android VMs
running under KVM with near-native performance.

Usage:
    mgr = DeviceManager()
    dev = await mgr.create_device(CreateDeviceRequest(
        model="samsung_s25_ultra", country="US", carrier="tmobile_us"
    ))
    await mgr.patch_device(dev.id)
    await mgr.destroy_device(dev.id)
"""

import asyncio
import glob
import json
import logging
import os
import secrets
import shutil
import signal
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.device_state_db import DeviceStateDB

logger = logging.getLogger("titan.device-manager")

TITAN_DATA = Path(os.environ.get("TITAN_DATA", "/opt/titan/data"))
DEVICES_DIR = TITAN_DATA / "devices"
CVD_HOME_BASE = Path(os.environ.get("CVD_HOME_BASE", "/opt/titan/cuttlefish"))
CVD_BIN_DIR = Path(os.environ.get("CVD_BIN_DIR", "/opt/titan/cuttlefish/cf/bin"))
CVD_IMAGES_DIR = Path(os.environ.get("CVD_IMAGES_DIR", "/opt/titan/cuttlefish/images"))
BASE_ADB_PORT = 6520
BASE_VNC_PORT = 6444
MAX_DEVICES = 8
INSTANCE_PREFIX = "titan-cvd-"


# ═══════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class CreateDeviceRequest:
    model: str = "samsung_s25_ultra"
    country: str = "US"
    carrier: str = "tmobile_us"
    phone_number: str = ""
    android_version: str = "14"
    screen_width: int = 1080
    screen_height: int = 2400
    dpi: int = 420
    memory_mb: int = 4096
    cpus: int = 4
    numa_node: int = -1          # -1 = auto-detect, 0+ = pin to specific NUMA node
    cpu_governor: str = "schedutil"  # schedutil|performance|powersave
    gpu_mode: str = "auto"  # auto|guest_swiftshader|drm_virgl|gfxstream


@dataclass
class DeviceInstance:
    id: str = ""
    container: str = ""               # legacy compat — maps to instance name
    adb_port: int = 6520
    adb_target: str = "127.0.0.1:6520"
    config: Dict[str, Any] = field(default_factory=dict)
    state: str = "created"
    created_at: str = ""
    error: str = ""
    patch_result: Dict[str, Any] = field(default_factory=dict)
    installed_apps: List[str] = field(default_factory=list)
    stealth_score: int = 0
    device_type: str = "cuttlefish"    # "cuttlefish" (KVM-based Android VM)
    instance_num: int = 1              # Cuttlefish --base_instance_num
    cvd_home: str = ""                 # Cuttlefish HOME directory for this instance
    vnc_port: int = 6444               # VNC display port

    def to_dict(self) -> dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════
# SHELL HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _run(cmd: str, timeout: int = 60, env: Dict[str, str] = None) -> Dict[str, Any]:
    try:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, env=run_env)
        return {"ok": r.returncode == 0, "stdout": r.stdout.strip(), "stderr": r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "timeout"}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e)}


def _adb(target: str, cmd: str, timeout: int = 15) -> Dict[str, Any]:
    return _run(f"adb -s {target} {cmd}", timeout=timeout)


def _adb_shell(target: str, cmd: str, timeout: int = 15) -> str:
    from adb_utils import adb_shell
    return adb_shell(target, cmd, timeout=timeout)


# ═══════════════════════════════════════════════════════════════════════
# DEVICE MANAGER
# ═══════════════════════════════════════════════════════════════════════

class DeviceManager:
    """Manages multiple Cuttlefish Android virtual machines via launch_cvd/stop_cvd."""

    # Required kernel modules for Cuttlefish KVM operation
    REQUIRED_MODULES = ["kvm", "vhost_vsock", "vhost_net"]
    OPTIONAL_MODULES = ["binder_linux", "ashmem_linux", "v4l2loopback"]

    def __init__(self):
        DEVICES_DIR.mkdir(parents=True, exist_ok=True)
        CVD_HOME_BASE.mkdir(parents=True, exist_ok=True)
        self._devices: Dict[str, DeviceInstance] = {}
        self._numa_topology: Optional[Dict] = None
        self._db = DeviceStateDB(str(TITAN_DATA / "devices.db"))
        self._load_state()

    # ─── NUMA / CPU AFFINITY ──────────────────────────────────────────

    def _detect_numa_topology(self) -> Dict[str, Any]:
        """Detect NUMA topology for CPU pinning optimization.

        On multi-socket servers (e.g., AMD EPYC), pinning Cuttlefish VMs
        to a specific NUMA node prevents cross-socket memory access latency
        and reduces performance jitter that can be detected by timing-based
        RASP analysis.
        """
        if self._numa_topology:
            return self._numa_topology

        topology = {"nodes": [], "total_cpus": 0, "numa_available": False}

        r = _run("lscpu --parse=CPU,NODE 2>/dev/null | grep -v '^#'", timeout=5)
        if r["ok"] and r["stdout"]:
            nodes: Dict[int, List[int]] = {}
            for line in r["stdout"].strip().split("\n"):
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    try:
                        cpu_id, node_id = int(parts[0]), int(parts[1])
                        nodes.setdefault(node_id, []).append(cpu_id)
                    except ValueError:
                        continue

            for node_id in sorted(nodes.keys()):
                topology["nodes"].append({
                    "id": node_id,
                    "cpus": sorted(nodes[node_id]),
                    "cpu_count": len(nodes[node_id]),
                })
            topology["total_cpus"] = sum(len(n) for n in nodes.values())
            topology["numa_available"] = len(nodes) > 1

        self._numa_topology = topology
        return topology

    def _select_numa_cpus(self, req: CreateDeviceRequest) -> Optional[str]:
        """Select CPUs for NUMA-aware pinning. Returns taskset CPU list or None."""
        topo = self._detect_numa_topology()
        if not topo["numa_available"]:
            return None

        node_id = req.numa_node
        if node_id == -1:
            # Auto-select: pick the NUMA node with the most free CPUs
            # (approximation: pick node with most CPUs)
            best = max(topo["nodes"], key=lambda n: n["cpu_count"])
            node_id = best["id"]

        # Find the requested NUMA node
        target_node = None
        for node in topo["nodes"]:
            if node["id"] == node_id:
                target_node = node
                break

        if not target_node or len(target_node["cpus"]) < req.cpus:
            logger.warning(f"NUMA node {node_id} has insufficient CPUs "
                           f"({len(target_node['cpus'] if target_node else [])} < {req.cpus})")
            return None

        # Select the first N CPUs from this node
        selected = target_node["cpus"][:req.cpus]
        cpu_list = ",".join(str(c) for c in selected)
        logger.info(f"NUMA pinning: node={node_id}, cpus={cpu_list}")
        return cpu_list

    def _ensure_kernel_modules(self):
        """Verify and load required kernel modules for Cuttlefish."""
        for mod in self.REQUIRED_MODULES:
            r = _run(f"lsmod | grep -q '^{mod}' || modprobe {mod} 2>/dev/null", timeout=10)
            if not r["ok"]:
                logger.warning(f"Kernel module '{mod}' not available — Cuttlefish may fail")

        for mod in self.OPTIONAL_MODULES:
            _run(f"lsmod | grep -q '^{mod}' || modprobe {mod} 2>/dev/null", timeout=5)

    def _set_cpu_governor(self, governor: str = "schedutil"):
        """Set CPU frequency governor for consistent VM performance."""
        valid = {"schedutil", "performance", "powersave", "ondemand", "conservative"}
        if governor not in valid:
            governor = "schedutil"
        _run(f"for f in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; "
             f"do echo {governor} > $f 2>/dev/null; done", timeout=5)

    def _ensure_cvd_host_files(self, cvd_home: Optional[Path] = None):
        """Ensure host-side Cuttlefish support files are available in /root/etc and per-instance cvd_home."""
        root_etc = Path("/root/etc")
        root_etc.mkdir(parents=True, exist_ok=True)

        default_input = root_etc / "default_input_devices"
        if not default_input.exists():
            source_dir = CVD_HOME_BASE / "etc" / "default_input_devices"
            if not source_dir.exists():
                source_dir = Path("/usr/lib/cuttlefish-common/etc/default_input_devices")
            if source_dir.exists():
                try:
                    default_input.symlink_to(source_dir)
                    logger.info(f"Symlinked default input devices from {source_dir} to {default_input}")
                except FileExistsError:
                    pass
                except Exception as e:
                    logger.warning(f"Failed to symlink default input devices: {e}")

        # Ensure cvd_config fallback exists in /root/etc/cvd_config
        root_cvd_config = root_etc / "cvd_config"
        if not root_cvd_config.exists():
            root_cvd_config.mkdir(parents=True, exist_ok=True)
            base_cvd_config = CVD_HOME_BASE / "etc" / "cvd_config"
            if base_cvd_config.exists():
                for entry in base_cvd_config.glob("*.json"):
                    target = root_cvd_config / entry.name
                    if not target.exists():
                        try:
                            target.symlink_to(entry)
                        except Exception:
                            pass

        instance_etc = None
        if cvd_home is not None:
            instance_etc = cvd_home / "etc"
            instance_etc.mkdir(parents=True, exist_ok=True)

        # Ensure per-instance android-info config exists for assemble_cvd
        self._ensure_instance_android_info(cvd_home)

        if instance_etc is not None:
            keys = [
                "cvd_avb_testkey_rsa2048.pem",
                "cvd_avb_testkey_rsa4096.pem",
                "cvd_rsa2048.avbpubkey",
                "cvd_rsa4096.avbpubkey",
            ]
            for key in keys:
                target = instance_etc / key
                if not target.exists():
                    source = CVD_HOME_BASE / "etc" / key
                    if not source.exists():
                        source = root_etc / key
                    if source.exists():
                        try:
                            target.symlink_to(source)
                        except FileExistsError:
                            pass
                        except Exception as e:
                            logger.warning(f"Failed to symlink AVB key {key} for {cvd_home}: {e}")

            # Ensure default input device templates are available under per-instance etc if requested
            if (instance_etc / "default_input_devices").exists() is False:
                if default_input.exists():
                    try:
                        (instance_etc / "default_input_devices").symlink_to(default_input)
                    except Exception as e:
                        logger.warning(f"Failed to symlink instance default input devices: {e}")

            # Ensure OpenWRT images are accessible for each instance
            openwrt_source = CVD_HOME_BASE / "etc" / "openwrt" / "images"
            if not openwrt_source.exists():
                openwrt_source = Path("/opt/titan/cuttlefish/home-cvd1/etc/openwrt/images")
            if openwrt_source.exists():
                openwrt_images_target = instance_etc / "openwrt" / "images"
                if not openwrt_images_target.exists():
                    try:
                        (instance_etc / "openwrt").mkdir(parents=True, exist_ok=True)
                        openwrt_images_target.symlink_to(openwrt_source)
                    except Exception as e:
                        logger.warning(f"Failed to symlink OpenWRT images for {cvd_home}: {e}")

    def _ensure_instance_android_info(self, cvd_home: Path):
        """Create per-instance android-info.txt from available template."""
        if not cvd_home:
            return
        info_path = cvd_home / "android-info.txt"
        if info_path.exists():
            return

        candidates = [
            CVD_IMAGES_DIR / "android-info.txt",
            CVD_HOME_BASE / "images" / "android-info.txt",
            CVD_HOME_BASE / "android-info.txt",
            Path("/opt/titan/cuttlefish/images/android-info.txt"),
        ]

        content = None
        for cand in candidates:
            if cand.exists() and cand.is_file():
                try:
                    content = cand.read_text()
                    break
                except Exception:
                    continue

        if content is None:
            content = "config=phone\ngfxstream=supported\ngfxstream_gl_program_binary_link_status=supported\n"

        try:
            info_path.write_text(content)
            logger.info(f"Wrote android-info config {info_path}")
        except Exception as e:
            logger.warning(f"Failed to write android-info.txt to {info_path}: {e}")

    def _detect_gpu_mode(self) -> str:
        """Auto-detect the best GPU acceleration mode for Cuttlefish.

        Priority:
          1. gfxstream  — requires host GPU + Vulkan (NVIDIA/AMD discrete)
          2. drm_virgl  — requires virglrenderer (works with most GPUs + Mesa)
          3. guest_swiftshader — pure software fallback (always works, slow)

        gfxstream gives ~60 FPS in-VM UI, drm_virgl ~30 FPS, swiftshader ~10 FPS.
        """
        # Check for discrete GPU with Vulkan support (gfxstream)
        r = _run("vulkaninfo --summary 2>/dev/null | head -20", timeout=5)
        if r["ok"] and "deviceName" in r["stdout"]:
            # Detect llvmpipe-only environments and fallback to software mode
            if "llvmpipe" in r["stdout"].lower():
                logger.info("GPU auto-detect: llvmpipe only, using guest_swiftshader")
                return "guest_swiftshader"

            # Has Vulkan — check if gfxstream renderer is available
            gfx_lib = _run("ldconfig -p 2>/dev/null | grep -i gfxstream", timeout=3)
            if gfx_lib["ok"] and "gfxstream" in gfx_lib["stdout"]:
                logger.info("GPU auto-detect: gfxstream (Vulkan GPU found)")
                return "gfxstream"

        # Check for virgl renderer (Mesa 3D) — REQUIRES a render node to actually work
        has_render_node = bool(glob.glob("/dev/dri/renderD*"))
        if has_render_node:
            virgl = _run("virgl_test_server --help 2>&1 || ldconfig -p 2>/dev/null | grep virgl", timeout=3)
            if virgl["ok"] or "virgl" in virgl.get("stderr", ""):
                logger.info("GPU auto-detect: drm_virgl (virglrenderer + render node found)")
                return "drm_virgl"
        else:
            logger.info("GPU auto-detect: no /dev/dri/renderD* nodes — skipping drm_virgl")

        logger.info("GPU auto-detect: guest_swiftshader (no GPU acceleration found)")
        return "guest_swiftshader"

    # ─── STATE PERSISTENCE ────────────────────────────────────────────

    def _load_state(self):
        """Load device state from SQLite database."""
        try:
            devices_data = self._db.load_all_devices()
            for dev_dict in devices_data:
                dev = DeviceInstance(
                    id=dev_dict["id"],
                    adb_target=dev_dict["adb_target"],
                    state=dev_dict["state"],
                    device_type=dev_dict["device_type"],
                    instance_num=dev_dict["instance_num"],
                    adb_port=dev_dict["adb_port"],
                    vnc_port=dev_dict["vnc_port"],
                    config=dev_dict["config"],
                    patch_result=dev_dict["patch_result"],
                    stealth_score=dev_dict["stealth_score"],
                    created_at=dev_dict["created_at"],
                    error=dev_dict["error"],
                )
                self._devices[dev.id] = dev
            logger.info(f"Loaded {len(self._devices)} devices from SQLite database")
        except Exception as e:
            logger.warning(f"Failed to load state from database: {e}")

    def _save_state(self):
        """Save device state to SQLite database."""
        for dev in self._devices.values():
            dev_dict = dev.to_dict()
            self._db.save_device(dev_dict)

    # ─── CVD PROCESS MANAGEMENT ──────────────────────────────────────

    CVD_CHILD_PROCESSES = [
        "crosvm", "run_cvd", "launch_cvd", "modem_simulator", "netsimd",
        "operator_proxy", "tombstone_receiver", "cf_vhost_user_input",
        "wmediumd", "screen_recording_server", "control_env_proxy_server",
        "echo_server", "gnss_grpc_proxy", "secure_env", "socket_vsock_pr",
        "casimir", "rootcanal", "adb_connector", "webRTC",
    ]

    def _kill_stale_cvd_processes(self, instance_num: int = None):
        """Kill orphaned Cuttlefish child processes that hold ports and block re-launch.

        BUG-C fix: After stop_cvd or cvd reset, child processes like modem_simulator,
        netsimd, tombstone_receiver etc. can survive and hold sockets (port 9600, 7300, etc.)
        causing 'Address already in use' on next launch.
        """
        killed = []
        for proc_name in self.CVD_CHILD_PROCESSES:
            r = _run(f"pkill -9 -f '{proc_name}' 2>/dev/null", timeout=5)
            if r["ok"]:
                killed.append(proc_name)

        if killed:
            logger.info(f"Killed stale CVD processes: {killed}")

        # Clean temp directories that Cuttlefish leaves behind
        for pattern in ["/tmp/cf_avd_*", "/tmp/cf_env_*", "/tmp/modem_simulator*"]:
            for p in glob.glob(pattern):
                try:
                    if os.path.isdir(p):
                        shutil.rmtree(p, ignore_errors=True)
                    else:
                        os.remove(p)
                except Exception:
                    pass

        # Wait for sockets to release
        time.sleep(2)

    def _launch_cvd_detached(self, cmd: str, cvd_home: str) -> Dict[str, Any]:
        """Launch CVD in a fully detached process group so it survives API restarts.

        BUG-A fix: Using subprocess.Popen with start_new_session=True instead of
        _run() so the VM process tree is completely independent of the uvicorn worker.
        """
        env = os.environ.copy()
        env["HOME"] = cvd_home

        log_path = os.path.join(cvd_home, "launch_cvd.log")
        try:
            with open(log_path, "w") as log_file:
                proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,  # setsid equivalent — new process group
                    close_fds=True,
                )

            # Wait up to 300s for launch_cvd to finish (it exits after VM starts in --daemon mode)
            try:
                returncode = proc.wait(timeout=300)
            except subprocess.TimeoutExpired:
                # launch_cvd still running — check if VM is coming up
                returncode = None

            # Read the log for diagnostics
            try:
                with open(log_path, "r") as f:
                    output = f.read()
            except Exception:
                output = ""

            if returncode is not None and returncode != 0:
                return {"ok": False, "stdout": output, "stderr": output}
            elif returncode is None:
                # Process still running — could be booting
                return {"ok": True, "stdout": output, "stderr": "", "pid": proc.pid}
            else:
                return {"ok": True, "stdout": output, "stderr": ""}

        except Exception as e:
            return {"ok": False, "stdout": "", "stderr": str(e)}

    def _ensure_cvd_home_symlinks(self, cvd_home: Path):
        """Symlink all required directories from CVD host package into per-instance home.

        BUG-E fix: launch_cvd (specifically assemble_cvd and avbtool) expects
        $HOME/bin, $HOME/etc, $HOME/lib64, $HOME/usr to contain host-package files.
        Only bin/ was symlinked — etc/, lib64/, usr/ were missing.
        """
        cf_root = CVD_BIN_DIR.parent  # e.g. /opt/titan/cuttlefish/cf
        for dirname in ["bin", "lib64", "usr"]:
            target = cvd_home / dirname
            source = cf_root / dirname
            if not target.exists() and source.exists():
                try:
                    target.symlink_to(source)
                    logger.info(f"Symlinked {source} -> {target}")
                except Exception as e:
                    logger.warning(f"Failed to symlink {dirname} for {cvd_home}: {e}")

        # etc/ needs special handling — we create a REAL directory and selectively
        # copy/symlink contents to avoid corrupting shared cvd_config presets
        etc_target = cvd_home / "etc"
        etc_source = cf_root / "etc"
        if not etc_target.exists() and etc_source.exists():
            etc_target.mkdir(parents=True, exist_ok=True)
            # Symlink individual entries except cvd_config (handled separately per-device)
            for entry in etc_source.iterdir():
                dest = etc_target / entry.name
                if entry.name == "cvd_config":
                    continue  # Per-device config created in create_device
                if not dest.exists():
                    try:
                        dest.symlink_to(entry)
                    except Exception as e:
                        logger.warning(f"Failed to symlink etc/{entry.name}: {e}")

    def _post_boot_setup(self, dev: DeviceInstance):
        """Post-boot device configuration.

        BUG-F fix: Disable screen timeout so device doesn't go to sleep,
        which causes black screenshots and viewer failures.
        """
        t = dev.adb_target
        # Disable screen timeout
        _adb(t, "shell settings put system screen_off_timeout 2147483647", timeout=5)
        # Keep screen on while charging (always true for VMs)
        _adb(t, "shell svc power stayon true", timeout=5)
        # Wake device and dismiss keyguard
        _adb(t, "shell input keyevent KEYCODE_WAKEUP", timeout=5)
        time.sleep(0.5)
        _adb(t, "shell input keyevent 82", timeout=5)
        logger.info(f"Post-boot setup complete for {dev.id}: screen timeout disabled, device awake")

    # ─── DEVICE CRUD ──────────────────────────────────────────────────

    def list_devices(self) -> List[DeviceInstance]:
        return list(self._devices.values())

    def get_device(self, device_id: str) -> Optional[DeviceInstance]:
        return self._devices.get(device_id)

    def _next_instance_num(self) -> int:
        used = {d.instance_num for d in self._devices.values()}
        for num in range(1, MAX_DEVICES + 5):
            if num not in used:
                return num
        raise RuntimeError("No available Cuttlefish instance numbers")

    def _is_adb_port_conflict(self, port: int) -> bool:
        """Check if the ADB host port is already in use (from existing devices, adb server, or other services)."""
        # Existing managed devices with same port
        for d in self._devices.values():
            if d.adb_port == port:
                return True

        # Check whether socket is listening already
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            try:
                s.connect(("127.0.0.1", port))
                return True
            except (ConnectionRefusedError, OSError, socket.timeout):
                return False

    def _instance_adb_port(self, instance_num: int) -> int:
        default_port = BASE_ADB_PORT + instance_num - 1
        if not self._is_adb_port_conflict(default_port):
            return default_port

        # If default is occupied, find next free port in range.
        for offset in range(MAX_DEVICES + 20):
            candidate = BASE_ADB_PORT + offset
            if not self._is_adb_port_conflict(candidate):
                logger.warning(f"ADB port {default_port} in use; switching to {candidate}")
                return candidate

        raise RuntimeError("No available ADB port around base port")

    def _resolve_system_image_dir(self) -> Optional[Path]:
        candidates = [
            Path(os.environ.get("CVD_IMAGES_DIR", "/opt/titan/cuttlefish/images")),
            Path("/opt/titan/cuttlefish/images"),
            Path("/opt/android-cuttlefish/images"),
            CVD_HOME_BASE / "images",
            Path("/opt/titan/cuttlefish/home-cvd1/images"),
        ]
        required_markers = ["system.img", "super.img", "boot.img", "super_raw.img", "userdata.img", "vbmeta.img"]

        for candidate in candidates:
            if not candidate.exists() or not candidate.is_dir():
                continue
            # Accept either dynamic partition image set (super.img) or classic system image set
            if any((candidate / marker).exists() for marker in required_markers):
                logger.info(f"Resolved system_image_dir: {candidate}")
                return candidate

        # If not found, try fallback to any image dir that contains a zygote or placeholder
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir() and any(candidate.glob("*.img")):
                logger.warning(f"Fallback system_image_dir by image pattern: {candidate}")
                return candidate

        logger.error("No valid Cuttlefish system_image_dir found among candidates: %s", candidates)
        return None

    def _instance_vnc_port(self, instance_num: int) -> int:
        return BASE_VNC_PORT + instance_num - 1

    def _generate_cvd_config(self, req: CreateDeviceRequest,
                              preset=None) -> Dict[str, Any]:
        """Generate Cuttlefish JSON config for launch_cvd.

        IMPORTANT: Only androidboot.* and sys.* keys are valid bootconfig
        entries.  ro.* system properties MUST NOT go here — they are applied
        post-boot by the anomaly patcher via resetprop.
        """
        # Only valid bootconfig keys (androidboot.* / sys.*)
        boot_props = [
            "androidboot.verifiedbootstate=green",
            "androidboot.vbmeta.device_state=locked",
            "sys.use_memfd=true",
        ]
        if preset:
            boot_props.append(f"androidboot.hardware={preset.hardware}")

        config = {
            "instances": [{
                "vm": {
                    "memory_mb": req.memory_mb,
                    "cpus": req.cpus,
                },
                "graphics": {
                    "displays": [{
                        "width": req.screen_width,
                        "height": req.screen_height,
                        "dpi": req.dpi,
                    }]
                },
                "boot": {
                    "extra_bootconfig_args": "\n".join(boot_props),
                },
            }]
        }
        return config

    async def create_device(self, req: CreateDeviceRequest) -> DeviceInstance:
        if len(self._devices) >= MAX_DEVICES:
            raise RuntimeError(f"Max {MAX_DEVICES} devices reached")

        # Pre-flight: ensure kernel modules, GPU mode, and set performance CPU governor
        self._ensure_kernel_modules()
        self._set_cpu_governor("performance")  # Max VM responsiveness

        initial_gpu_mode = req.gpu_mode
        if req.gpu_mode == "auto":
            req.gpu_mode = self._detect_gpu_mode()

        dev_id = f"dev-{secrets.token_hex(3)}"
        instance_num = self._next_instance_num()
        adb_port = self._instance_adb_port(instance_num)
        vnc_port = self._instance_vnc_port(instance_num)
        instance_name = f"{INSTANCE_PREFIX}{dev_id}"

        # BUG-C: Kill any stale CVD processes before attempting launch
        self._kill_stale_cvd_processes(instance_num)

        # Create per-instance home directory for Cuttlefish
        cvd_home = CVD_HOME_BASE / dev_id
        cvd_home.mkdir(parents=True, exist_ok=True)

        # BUG-E: Symlink ALL required host dirs (bin, lib64, usr, etc) into per-instance home
        self._ensure_cvd_home_symlinks(cvd_home)

        # Also create device data dir for Titan metadata
        data_dir = DEVICES_DIR / dev_id
        data_dir.mkdir(parents=True, exist_ok=True)

        # Ensure host-side Cuttlefish data dependencies are available for launch_cvd.
        self._ensure_cvd_host_files()
        self._ensure_instance_android_info(cvd_home)

        dev = DeviceInstance(
            id=dev_id,
            container=instance_name,
            adb_port=adb_port,
            adb_target=f"127.0.0.1:{adb_port}",
            config=asdict(req) if hasattr(req, '__dataclass_fields__') else req.__dict__,
            state="creating",
            created_at=datetime.now(timezone.utc).isoformat(),
            device_type="cuttlefish",
            instance_num=instance_num,
            cvd_home=str(cvd_home),
            vnc_port=vnc_port,
        )
        self._devices[dev_id] = dev
        self._save_state()

        # Resolve device preset for identity props
        from core.device_presets import DEVICE_PRESETS
        preset = DEVICE_PRESETS.get(req.model)

        # Generate Cuttlefish JSON config with device identity baked in
        cvd_config = self._generate_cvd_config(req, preset)
        config_path = cvd_home / "cvd_config.json"
        config_path.write_text(json.dumps(cvd_config, indent=2))

        # Ensure Cuttlefish host files and legacy config directory exist (launch_cvd expects this)
        self._ensure_cvd_host_files(cvd_home=cvd_home)

        config_dir = cvd_home / "etc" / "cvd_config"
        config_dir.mkdir(parents=True, exist_ok=True)

        legacy_config_path = config_dir / "cvd_config.json"
        if legacy_config_path.exists() or legacy_config_path.is_symlink():
            legacy_config_path.unlink()
        legacy_config_path.symlink_to(config_path)

        # Generate a config preset that matches Cuttlefish --config=phone expectations
        legacy_config_phone_path = config_dir / "cvd_config_phone.json"
        phone_config = {
            "x_res": req.screen_width,
            "y_res": req.screen_height,
            "dpi": req.dpi,
            "memory_mb": req.memory_mb,
            "ddr_mem_mb": max(req.memory_mb + 512, req.memory_mb),
        }
        legacy_config_phone_path.write_text(json.dumps(phone_config, indent=2))

        logger.info(f"Wrote CVD config: {config_path}")
        logger.info(f"Symlinked legacy CVD config: {legacy_config_path}")
        logger.info(f"Wrote legacy CVD config phone: {legacy_config_phone_path}")
        logger.info(f"Legacy config dir listing: {list(config_dir.iterdir())}")

        # Determine launch_cvd binary path
        launch_cvd = CVD_BIN_DIR / "launch_cvd"
        if not launch_cvd.exists():
            # Fallback: check if it's on PATH
            launch_cvd = Path(shutil.which("launch_cvd") or "launch_cvd")

        # Ensure stale CVD instance is reset (covers "instance directory files in use" errors)
        cvd_reset = CVD_BIN_DIR / "cvd"
        if not cvd_reset.exists():
            cvd_reset = Path(shutil.which("cvd") or "cvd")
        try:
            _run(f"{cvd_reset} reset --base_instance_num={instance_num}", timeout=30)
            logger.info(f"Called cvd reset for base_instance_num={instance_num}")
        except Exception as e:
            logger.warning(f"cvd reset command failed (non-fatal): {e}")

        # Pre-resolve image dir once
        system_image_dir = self._resolve_system_image_dir()
        if not system_image_dir:
            logger.warning(f"Using fallback system_image_dir: {CVD_IMAGES_DIR}")
            system_image_dir = CVD_IMAGES_DIR

        # Helper to build launch command with runtime options
        def _build_cvd_command(gpu_mode: str) -> str:
            extra_bootconfig = cvd_config["instances"][0]["boot"]["extra_bootconfig_args"]
            cvd_cmd = (
                f"{launch_cvd} "
                f"--config=phone "  # Cuttlefish presets use phone base config
                f"--base_instance_num={instance_num} "
                f"--daemon "
                f"--gpu_mode={gpu_mode} "
                f"--cpus={req.cpus} "
                f"--memory_mb={req.memory_mb} "
                f"--display0=width={req.screen_width},height={req.screen_height},dpi={req.dpi} "
                f'--extra_bootconfig_args="{extra_bootconfig}" '
                f"--report_anonymous_usage_stats=n "
                f"--system_image_dir={system_image_dir} "
            )

            numa_cpus = self._select_numa_cpus(req)
            if numa_cpus:
                cvd_cmd = f"taskset -c {numa_cpus} {cvd_cmd}"
                logger.info(f"NUMA pinning active: CPUs {numa_cpus}")

            return cvd_cmd

        # Create Cuttlefish device with GPU fallback (drm_virgl -> guest_swiftshader only for auto)
        logger.info(f"Creating Cuttlefish device {dev_id} (instance {instance_num})")
        final_result: Dict[str, Any] = {"ok": False, "stderr": ""}

        if initial_gpu_mode == "auto":
            attempted_modes = [req.gpu_mode]
            if req.gpu_mode != "guest_swiftshader":
                attempted_modes.append("guest_swiftshader")
        else:
            attempted_modes = [req.gpu_mode]

        for mode in attempted_modes:
            current_cmd = _build_cvd_command(mode)
            logger.info(f"launch_cvd command (gpu_mode={mode}): {current_cmd}")
            # BUG-A: Use detached launch so VM survives API restarts
            result = self._launch_cvd_detached(current_cmd, str(cvd_home))
            if result["ok"]:
                final_result = result
                req.gpu_mode = mode
                dev.config["gpu_mode"] = mode
                break

            # Detect early retry conditions for GPU mode failures
            stderr_lower = result.get("stderr", "").lower()
            if mode != "guest_swiftshader" and (
                "--gpu_mode=drm_virgl was requested" in stderr_lower
                or "failed to initialize display" in stderr_lower
                or "graphics check failure" in stderr_lower
            ):
                logger.warning(f"GPU mode {mode} failed, retrying with guest_swiftshader: {stderr_lower}")
                final_result = result
                continue

            final_result = result
            break

        if not final_result["ok"]:
            if final_result["stderr"] == "timeout":
                check = _run("pgrep -fa launch_cvd || true", timeout=5)
                if check["ok"] and "launch_cvd" in check["stdout"]:
                    logger.info("launch_cvd process is still running after timeout; continuing boot wait")
                    dev.state = "booting"
                    dev.error = "launch_cvd timeout, process still running"
                    self._save_state()
                else:
                    dev.state = "error"
                    dev.error = final_result["stderr"]
                    self._save_state()
                    raise RuntimeError(f"launch_cvd failed: {final_result['stderr']}")
            else:
                dev.state = "error"
                dev.error = final_result["stderr"]
                self._save_state()
                raise RuntimeError(f"launch_cvd failed: {final_result['stderr']}")
        else:
            dev.state = "booting"
            self._save_state()

        # Wait for ADB
        try:
            await self._wait_for_adb(dev)
        except RuntimeError as e:
            # If we timed out on a non-software GPU mode, retry once with guest_swiftshader.
            if req.gpu_mode != "guest_swiftshader":
                logger.warning(f"ADB boot timeout for {dev_id}; retrying with guest_swiftshader: {e}")
                await self.destroy_device(dev_id)
                req.gpu_mode = "guest_swiftshader"
                return await self.create_device(req)

            dev.state = "error"
            dev.error = str(e)
            self._save_state()
            raise

        # BUG-F: Post-boot setup — disable screen timeout, wake device
        self._post_boot_setup(dev)

        dev.state = "ready"
        self._save_state()
        logger.info(f"Device {dev_id} ready on {dev.adb_target} (CVD instance {instance_num})")

        # Start continuous sensor injection daemon (prevents RASP stale-sensor detection)
        try:
            from sensor_simulator import SensorSimulator
            brand = preset.brand if preset else "samsung"
            sensor_sim = SensorSimulator(adb_target=dev.adb_target, brand=brand)
            sensor_sim.start_background_noise()
            sensor_sim.start_continuous_injection(interval_s=2.0)
            logger.info(f"Sensor daemon started for {dev_id}")
        except Exception as e:
            logger.warning(f"Sensor daemon start failed (non-fatal): {e}")

        return dev

    async def _wait_for_adb(self, dev: DeviceInstance, timeout: int = 120):
        """Poll until ADB connects and Cuttlefish VM boots."""
        target = dev.adb_target
        start = time.time()

        # Connect ADB — Cuttlefish exposes ADB on 0.0.0.0:<port>
        while time.time() - start < timeout:
            r = _adb(target, "connect " + target)
            stdout = r.get("stdout", "").lower()
            if "connected" in stdout or "already" in stdout:
                break
            await asyncio.sleep(3)

        # Wait for boot_completed
        while time.time() - start < timeout:
            val = _adb_shell(target, "getprop sys.boot_completed")
            if val.strip() == "1":
                return
            await asyncio.sleep(3)

        dev.state = "error"
        dev.error = "ADB boot timeout"
        self._save_state()
        raise RuntimeError(f"ADB boot timeout for device {dev.id} after {timeout}s")

    async def destroy_device(self, device_id: str) -> bool:
        dev = self._devices.get(device_id)
        if not dev:
            return False

        logger.info(f"Destroying device {device_id}")

        # Stop sensor daemon and screen streamer
        try:
            from sensor_simulator import SensorSimulator
            sim = SensorSimulator(adb_target=dev.adb_target)
            sim.stop_continuous_injection()
        except Exception:
            pass
        try:
            from screen_streamer import remove_streamer
            remove_streamer(device_id)
        except Exception:
            pass

        # Stop Cuttlefish VM
        stop_cvd = CVD_BIN_DIR / "stop_cvd"
        if not stop_cvd.exists():
            stop_cvd = Path(shutil.which("stop_cvd") or "stop_cvd")
        cvd_home = dev.cvd_home or str(CVD_HOME_BASE / device_id)
        _run(f"{stop_cvd} --base_instance_num={dev.instance_num}",
             timeout=30, env={"HOME": cvd_home})

        # Disconnect ADB
        _run(f"adb disconnect {dev.adb_target}", timeout=5)

        # Remove instance home directory
        cvd_path = Path(cvd_home)
        if cvd_path.exists():
            shutil.rmtree(cvd_path, ignore_errors=True)

        # Remove device data
        data_dir = DEVICES_DIR / device_id
        if data_dir.exists():
            shutil.rmtree(data_dir, ignore_errors=True)

        deleted = self._db.delete_device(device_id)
        if not deleted:
            logger.warning(f"Failed to delete device {device_id} from database")

        # Remove from in-memory registry so destroyed devices are not retained
        if device_id in self._devices:
            del self._devices[device_id]

        self._save_state()
        return True

    async def restart_device(self, device_id: str) -> bool:
        dev = self._devices.get(device_id)
        if not dev:
            return False

        # Restart Cuttlefish: stop then re-launch with same config
        stop_cvd = CVD_BIN_DIR / "stop_cvd"
        if not stop_cvd.exists():
            stop_cvd = Path(shutil.which("stop_cvd") or "stop_cvd")
        cvd_home = dev.cvd_home or str(CVD_HOME_BASE / device_id)
        _run(f"{stop_cvd} --base_instance_num={dev.instance_num}",
             timeout=30, env={"HOME": cvd_home})

        await asyncio.sleep(2)

        # Re-launch with existing config
        config_path = Path(cvd_home) / "cvd_config.json"
        launch_cvd = CVD_BIN_DIR / "launch_cvd"
        if not launch_cvd.exists():
            launch_cvd = Path(shutil.which("launch_cvd") or "launch_cvd")

        cvd_cmd = (
            f"{launch_cvd} "
            f"--config=phone "
            f"--base_instance_num={dev.instance_num} "
            f"--daemon "
            f"--report_anonymous_usage_stats=n "
        )

        system_image_dir = self._resolve_system_image_dir()
        if system_image_dir:
            cvd_cmd += f"--system_image_dir={system_image_dir} "
        else:
            cvd_cmd += f"--system_image_dir={CVD_IMAGES_DIR} "
            logger.warning(f"Restart: Fallback system_image_dir: {CVD_IMAGES_DIR}")

        # BUG-C: Kill stale processes before restart
        self._kill_stale_cvd_processes(dev.instance_num)

        # BUG-A: Use detached launch so VM survives API restarts
        self._launch_cvd_detached(cvd_cmd, cvd_home)

        dev.state = "booting"
        self._save_state()

        await self._wait_for_adb(dev)

        # BUG-F: Post-boot setup — disable screen timeout, wake device
        self._post_boot_setup(dev)

        dev.state = "ready"
        self._save_state()
        return True

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get live device info via ADB."""
        dev = self._devices.get(device_id)
        if not dev or dev.state not in ("ready", "patched", "running"):
            return None

        t = dev.adb_target
        return {
            "id": dev.id,
            "device_type": dev.device_type,
            "instance_num": dev.instance_num,
            "model": _adb_shell(t, "getprop ro.product.model"),
            "brand": _adb_shell(t, "getprop ro.product.brand"),
            "android": _adb_shell(t, "getprop ro.build.version.release"),
            "sdk": _adb_shell(t, "getprop ro.build.version.sdk"),
            "fingerprint": _adb_shell(t, "getprop ro.build.fingerprint"),
            "serial": _adb_shell(t, "getprop ro.serialno"),
            "imei": _adb_shell(t, "service call iphonesubinfo 1 | grep -oP \"[0-9a-f]{8}\" | head -4"),
            "carrier": _adb_shell(t, "getprop gsm.sim.operator.alpha"),
            "sim_state": _adb_shell(t, "getprop gsm.sim.state"),
            "battery": _adb_shell(t, "dumpsys battery | grep level"),
            "boot_completed": _adb_shell(t, "getprop sys.boot_completed"),
            "uptime": _adb_shell(t, "uptime"),
        }

    async def screenshot(self, device_id: str) -> Optional[bytes]:
        """Capture device screenshot as JPEG bytes."""
        dev = self._devices.get(device_id)
        if not dev or dev.state not in ("ready", "patched", "running"):
            return None

        for attempt in range(2):
            try:
                # Use raw binary mode — text mode corrupts PNG data
                proc = subprocess.run(
                    ["adb", "-s", dev.adb_target, "exec-out", "screencap", "-p"],
                    capture_output=True, timeout=10,
                )
                if proc.returncode != 0 or len(proc.stdout) < 100:
                    if attempt == 0:
                        # Try ADB reconnect before giving up
                        subprocess.run(
                            ["adb", "connect", dev.adb_target],
                            capture_output=True, timeout=5,
                        )
                        continue
                    return None

                png_bytes = proc.stdout

                try:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(png_bytes))
                    img = img.convert("RGB")
                    w, h = img.size
                    img = img.resize((w // 2, h // 2))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=70)
                    return buf.getvalue()
                except Exception:
                    # If PIL fails, return raw PNG
                    return png_bytes
            except Exception:
                if attempt == 0:
                    try:
                        subprocess.run(
                            ["adb", "connect", dev.adb_target],
                            capture_output=True, timeout=5,
                        )
                    except Exception:
                        pass
                    continue
                return None
        return None
