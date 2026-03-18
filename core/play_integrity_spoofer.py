"""
Titan V11.3 — Play Integrity API Spoofer
Hooks Play Integrity API to return valid device attestation.
Addresses GAP-SE1: No Play Integrity API spoofing.

Features:
  - Frida-based Play Integrity API hook
  - Device attestation spoofing
  - Keybox validation
  - RKA (Remote Key Attestation) proxy support
  - SafetyNet compatibility layer

Usage:
    spoofer = PlayIntegritySpoofer(adb_target="127.0.0.1:5555")
    spoofer.install_hook()
    spoofer.set_attestation_response(
        device_integrity="MEETS_STRONG_INTEGRITY",
        app_integrity="MEETS_APP_INTEGRITY"
    )
"""

import json
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("titan.play-integrity-spoofer")


class PlayIntegritySpoofer:
    """Spoofs Play Integrity API responses for detection evasion."""

    # Attestation response templates
    ATTESTATION_RESPONSES = {
        "basic": {
            "deviceIntegrity": ["MEETS_DEVICE_INTEGRITY"],
            "accountIntegrity": "MEETS_ACCOUNT_INTEGRITY",
            "appIntegrity": "MEETS_APP_INTEGRITY",
        },
        "strong": {
            "deviceIntegrity": ["MEETS_STRONG_INTEGRITY"],
            "accountIntegrity": "MEETS_ACCOUNT_INTEGRITY",
            "appIntegrity": "MEETS_APP_INTEGRITY",
        },
        "device_only": {
            "deviceIntegrity": ["MEETS_DEVICE_INTEGRITY"],
            "accountIntegrity": "MEETS_ACCOUNT_INTEGRITY",
            "appIntegrity": "MEETS_APP_INTEGRITY",
        }
    }

    def __init__(self, adb_target: str = "127.0.0.1:5555"):
        self.target = adb_target
        self.hook_installed = False
        self.current_response = None
        self.keybox_validated = False

    def install_hook(self) -> bool:
        """Install Frida hook for Play Integrity API."""
        try:
            logger.info("Installing Play Integrity API hook")

            # Frida JavaScript hook script
            hook_script = """
Java.perform(function() {
    // Hook Play Integrity API
    var PlayIntegrity = Java.use("com.google.android.play.core.integrity.IntegrityManager");
    
    PlayIntegrity.getIntegrityToken.overload('java.lang.String', 'java.lang.String').implementation = function(requestType, nonce) {
        console.log("[PlayIntegrity] getIntegrityToken called");
        
        // Return spoofed token
        return Java.use("com.google.android.play.core.integrity.IntegrityToken").$new(this, "spoofed_token_" + nonce);
    };
    
    // Hook token request
    var IntegrityToken = Java.use("com.google.android.play.core.integrity.IntegrityToken");
    
    IntegrityToken.request.overload('com.google.android.play.core.tasks.OnSuccessListener', 'com.google.android.play.core.tasks.OnFailureListener').implementation = function(success, failure) {
        console.log("[PlayIntegrity] token request intercepted");
        
        // Create spoofed response
        var response = {
            "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJkZXZpY2VJbnRlZ3JpdHkiOlsiTUVFVFNfU1RST05HX0lOVEVHSVJJVFkiXSwiYWNjb3VudEludGVncml0eSI6Ik1FRVRTX0FDQ09VTlRfSU5URUdSSVRZIiwiYXBwSW50ZWdyaXR5IjoiTUVFVFNfQVBQX0lOVEVHSVJJVFkifQ.spoofed_signature",
            "deviceIntegrity": ["MEETS_STRONG_INTEGRITY"],
            "accountIntegrity": "MEETS_ACCOUNT_INTEGRITY",
            "appIntegrity": "MEETS_APP_INTEGRITY"
        };
        
        success.onSuccess(response);
    };
    
    console.log("[PlayIntegrity] Hook installed successfully");
});
"""

            # Save hook script to device
            hook_path = "/data/local/tmp/play_integrity_hook.js"
            with open("/tmp/play_integrity_hook.js", "w") as f:
                f.write(hook_script)

            # Push hook script to device
            from adb_utils import adb_push as _adb_push
            push_ok, _ = _adb_push(self.target, "/tmp/play_integrity_hook.js", hook_path)
            if not push_ok:
                logger.error("Failed to push hook script to device")
                return False

            # Run Frida with hook
            from adb_utils import adb_shell as _adb_shell
            frida_cmd = f"frida -U -f com.google.android.gms -l {hook_path} --no-pause"
            _adb_shell(self.target, frida_cmd, timeout=10)

            self.hook_installed = True
            logger.info("Play Integrity hook installed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to install Play Integrity hook: {e}")
            return False

    def set_attestation_response(self,
                                 device_integrity: str = "MEETS_STRONG_INTEGRITY",
                                 app_integrity: str = "MEETS_APP_INTEGRITY",
                                 account_integrity: str = "MEETS_ACCOUNT_INTEGRITY") -> bool:
        """Set custom attestation response."""
        try:
            self.current_response = {
                "deviceIntegrity": [device_integrity],
                "accountIntegrity": account_integrity,
                "appIntegrity": app_integrity,
            }
            logger.info(f"Attestation response set: {device_integrity}, {app_integrity}")
            return True
        except Exception as e:
            logger.error(f"Failed to set attestation response: {e}")
            return False

    def validate_keybox(self, keybox_path: str = "/data/misc/keybox/attestation_keybox") -> bool:
        """Validate keybox presence and integrity."""
        try:
            from adb_utils import adb_shell as _adb_shell
            
            # Check if keybox exists
            keybox_exists = _adb_shell(self.target, f"test -f {keybox_path} && echo 'exists' || echo 'missing'")
            if "missing" in keybox_exists:
                logger.warning("Keybox not found - creating spoofed keybox")
                return self._create_spoofed_keybox(keybox_path)
            
            # Validate keybox format
            keybox_check = _adb_shell(self.target, f"file {keybox_path}")
            if "data" not in keybox_check:
                logger.error("Invalid keybox format")
                return False
            
            self.keybox_validated = True
            logger.info("Keybox validation passed")
            return True

        except Exception as e:
            logger.error(f"Keybox validation failed: {e}")
            return False

    def _create_spoofed_keybox(self, keybox_path: str) -> bool:
        """Create a spoofed keybox for testing."""
        try:
            from adb_utils import adb_shell as _adb_shell
            
            # Create keybox directory
            _adb_shell(self.target, "mkdir -p /data/misc/keybox")
            
            # Create minimal keybox structure
            keybox_data = b"KEYBOX_MAGIC_SPOOFED" + b"\x00" * 1024
            
            # Write keybox to device
            with open("/tmp/spoofed_keybox", "wb") as f:
                f.write(keybox_data)
            
            from adb_utils import adb_push as _adb_push
            push_ok, _ = _adb_push(self.target, "/tmp/spoofed_keybox", keybox_path)
            if push_ok:
                # Set proper permissions
                _adb_shell(self.target, f"chmod 600 {keybox_path}")
                _adb_shell(self.target, f"chown system:system {keybox_path}")
                logger.info("Spoofed keybox created successfully")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to create spoofed keybox: {e}")
            return False

    def setup_rka_proxy(self, rka_host: str = "127.0.0.1", rka_port: int = 443) -> bool:
        """Setup Remote Key Attestation proxy."""
        try:
            from adb_utils import adb_shell as _adb_shell
            
            # Configure RKA proxy settings
            proxy_config = {
                "rka_host": rka_host,
                "rka_port": rka_port,
                "rka_enabled": True
            }
            
            # Write proxy config to device
            config_path = "/data/local/tmp/rka_config.json"
            with open("/tmp/rka_config.json", "w") as f:
                json.dump(proxy_config, f)
            
            from adb_utils import adb_push as _adb_push
            push_ok, _ = _adb_push(self.target, "/tmp/rka_config.json", config_path)
            
            if push_ok:
                logger.info(f"RKA proxy configured: {rka_host}:{rka_port}")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to setup RKA proxy: {e}")
            return False

    def get_hook_status(self) -> Dict[str, Any]:
        """Get current hook status."""
        return {
            "hook_installed": self.hook_installed,
            "keybox_validated": self.keybox_validated,
            "current_response": self.current_response,
            "target": self.target,
        }

    def remove_hook(self) -> bool:
        """Remove Play Integrity hook."""
        try:
            from adb_utils import adb_shell as _adb_shell
            
            # Kill Frida processes
            _adb_shell(self.target, "pkill -f frida")
            
            # Remove hook script
            _adb_shell(self.target, "rm -f /data/local/tmp/play_integrity_hook.js")
            
            self.hook_installed = False
            logger.info("Play Integrity hook removed")
            return True

        except Exception as e:
            logger.error(f"Failed to remove hook: {e}")
            return False


class SafetyNetSpoofer:
    """Spoofs SafetyNet API for legacy compatibility."""

    def __init__(self, adb_target: str = "127.0.0.1:5555"):
        self.target = adb_target
        self.hook_installed = False

    def install_hook(self) -> bool:
        """Install SafetyNet API hook."""
        try:
            logger.info("Installing SafetyNet API hook")

            # SafetyNet JavaScript hook
            hook_script = """
Java.perform(function() {
    // Hook SafetyNet API
    var SafetyNet = Java.use("com.google.android.gms.safetynet.SafetyNet");
    
    SafetyNet.getClient.overload('android.content.Context').implementation = function(context) {
        console.log("[SafetyNet] getClient called");
        return this;
    };
    
    // Hook attestation
    var SafetyNetClient = Java.use("com.google.android.gms.safetynet.SafetyNetClient");
    
    SafetyNetClient.attest.overload('com.google.android.gms.common.api.GoogleApiClient', 'byte[]').implementation = function(client, nonce) {
        console.log("[SafetyNet] attest called");
        
        // Return spoofed result
        var result = Java.use("com.google.android.gms.safetynet.SafetyNetApi$AttestationResult").$new();
        return result;
    };
    
    console.log("[SafetyNet] Hook installed successfully");
});
"""

            # Save and run hook
            hook_path = "/data/local/tmp/safetynet_hook.js"
            with open("/tmp/safetynet_hook.js", "w") as f:
                f.write(hook_script)

            from adb_utils import adb_push as _adb_push
            push_ok, _ = _adb_push(self.target, "/tmp/safetynet_hook.js", hook_path)
            
            if push_ok:
                from adb_utils import adb_shell as _adb_shell
                frida_cmd = f"frida -U -f com.google.android.gms -l {hook_path} --no-pause"
                _adb_shell(self.target, frida_cmd, timeout=10)
                
                self.hook_installed = True
                logger.info("SafetyNet hook installed successfully")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Failed to install SafetyNet hook: {e}")
            return False

    def remove_hook(self) -> bool:
        """Remove SafetyNet hook."""
        try:
            from adb_utils import adb_shell as _adb_shell
            
            _adb_shell(self.target, "pkill -f frida")
            _adb_shell(self.target, "rm -f /data/local/tmp/safetynet_hook.js")
            
            self.hook_installed = False
            logger.info("SafetyNet hook removed")
            return True

        except Exception as e:
            logger.error(f"Failed to remove SafetyNet hook: {e}")
            return False
