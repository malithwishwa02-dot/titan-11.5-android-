"""
Titan V11.3 — Device Recovery Manager
Monitors device health and automatically recovers stuck devices.
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Any

logger = logging.getLogger("titan.device-recovery")


class DeviceRecoveryManager:
    """Monitors and recovers stuck devices."""
    
    def __init__(
        self,
        device_manager: Any,
        check_interval: int = 60,
        boot_timeout: int = 300,
        error_timeout: int = 600,
    ):
        """
        Initialize recovery manager.
        
        Args:
            device_manager: DeviceManager instance
            check_interval: Seconds between health checks
            boot_timeout: Max seconds in 'booting' state before restart
            error_timeout: Max seconds in 'error' state before cleanup
        """
        self.dm = device_manager
        self.check_interval = check_interval
        self.boot_timeout = boot_timeout
        self.error_timeout = error_timeout
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start recovery monitoring."""
        if self._running:
            logger.warning("Recovery manager already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Device recovery manager started")
    
    async def stop(self):
        """Stop recovery monitoring."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Device recovery manager stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_devices()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in recovery monitor: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_devices(self):
        """Check all devices for stuck states."""
        devices = self.dm.list_devices()
        current_time = time.time()
        
        for dev in devices:
            try:
                # Check for stuck booting state
                if dev.state == "booting":
                    elapsed = current_time - (dev.created_at if isinstance(dev.created_at, float) 
                                             else time.time())
                    if elapsed > self.boot_timeout:
                        logger.warning(
                            f"Device {dev.id} stuck in booting for {elapsed:.0f}s, restarting"
                        )
                        await self._recover_device(dev.id, "restart")
                
                # Check for stuck error state
                elif dev.state == "error":
                    elapsed = current_time - (dev.created_at if isinstance(dev.created_at, float)
                                             else time.time())
                    if elapsed > self.error_timeout:
                        logger.warning(
                            f"Device {dev.id} in error state for {elapsed:.0f}s, destroying"
                        )
                        await self._recover_device(dev.id, "destroy")
                
                # Check ADB connectivity for ready devices
                elif dev.state in ("ready", "patched", "running"):
                    if not await self._is_device_responsive(dev.adb_target):
                        logger.warning(f"Device {dev.id} not responsive, reconnecting")
                        await self._recover_device(dev.id, "reconnect")
            
            except Exception as e:
                logger.error(f"Error checking device {dev.id}: {e}")
    
    async def _is_device_responsive(self, adb_target: str) -> bool:
        """Check if device is responsive via ADB."""
        try:
            from adb_utils import is_device_connected
            return is_device_connected(adb_target)
        except Exception as e:
            logger.debug(f"Failed to check device responsiveness: {e}")
            return False
    
    async def _recover_device(self, device_id: str, action: str):
        """Execute recovery action on device."""
        try:
            if action == "restart":
                logger.info(f"Restarting device {device_id}")
                await self.dm.restart_device(device_id)
                logger.info(f"Device {device_id} restarted successfully")
            
            elif action == "reconnect":
                logger.info(f"Reconnecting device {device_id}")
                dev = self.dm.get_device(device_id)
                if dev:
                    from adb_utils import reconnect_device
                    success = reconnect_device(dev.adb_target, max_retries=3)
                    if success:
                        logger.info(f"Device {device_id} reconnected")
                        dev.state = "ready"
                        self.dm._save_state()
                    else:
                        logger.warning(f"Failed to reconnect device {device_id}")
            
            elif action == "destroy":
                logger.info(f"Destroying device {device_id}")
                await self.dm.destroy_device(device_id)
                logger.info(f"Device {device_id} destroyed")
        
        except Exception as e:
            logger.error(f"Recovery action '{action}' failed for device {device_id}: {e}")


class RecoveryMetrics:
    """Track recovery metrics."""
    
    def __init__(self):
        self.restarts = 0
        self.reconnects = 0
        self.destroys = 0
        self.last_recovery_time = 0
    
    def record_restart(self):
        """Record device restart."""
        self.restarts += 1
        self.last_recovery_time = time.time()
    
    def record_reconnect(self):
        """Record device reconnect."""
        self.reconnects += 1
        self.last_recovery_time = time.time()
    
    def record_destroy(self):
        """Record device destroy."""
        self.destroys += 1
        self.last_recovery_time = time.time()
    
    def get_stats(self) -> dict:
        """Get recovery statistics."""
        return {
            "restarts": self.restarts,
            "reconnects": self.reconnects,
            "destroys": self.destroys,
            "last_recovery_time": self.last_recovery_time,
        }
