# RDP Browser & IDE Login Issues - Root Cause Analysis & Fixes

## Root Causes Identified

### 1. Missing XDG Runtime Directory (`/run/user/0`)
- **Symptom**: Browsers and IDEs couldn't create portal files, causing crashes and warnings
- **Error**: `cannot write file at /run/user/0/.portals-unavailable: no such file or directory`
- **Impact**: Firefox and Chrome couldn't initialize properly in RDP session

### 2. Snap Browser Isolation Issues
- **Symptom**: Chromium and Firefox snap packages had mount namespace conflicts
- **Error**: `cannot change mount namespace according to change mount` warnings
- **Impact**: Browsers couldn't access host filesystem paths, causing launch failures

### 3. Browser Sync/Login Prompts
- **Symptom**: Firefox and Chrome constantly asking for account login
- **Impact**: Annoying login prompts on every browser launch

### 4. IDE Settings Sync Prompts
- **Symptom**: VSCode and Windsurf asking for account login repeatedly
- **Impact**: Constant authentication requests in development environment

## Fixes Applied

### ✓ XDG Runtime Directory
- Created `/run/user/0` with proper permissions (700, root:root)
- Updated `/etc/xrdp/startwm.sh` to auto-create on RDP login
- Added `/etc/profile.d/xdg-runtime-root.sh` for shell sessions

### ✓ Native Browser Installation
- **Removed**: Firefox snap, Chromium snap (both had isolation issues)
- **Installed**: 
  - Firefox 148.0.2 from Mozilla PPA (native .deb)
  - Google Chrome 146.0.7680.153 (native .deb)
- **Configured**: Chrome as default browser

### ✓ Browser Configuration
- **Firefox**: Created `/root/.mozilla/firefox/default-release/user.js`
  - Disabled Firefox Sync (`identity.fxaccounts.enabled = false`)
  - Disabled welcome screens and first-run UI
  - Disabled telemetry and update prompts
  
- **Chrome**: Created `/root/.config/google-chrome/Default/Preferences`
  - Disabled sign-in prompts (`signin.allowed = false`)
  - Disabled sync promo on first run
  - Skipped first-run UI

### ✓ IDE Configuration
- **VSCode**: `/root/.config/Code/User/settings.json`
  - Disabled telemetry and auto-updates
  - Disabled settings sync prompts
  
- **Windsurf**: `/root/.config/Windsurf/User/settings.json`
  - Same configuration as VSCode

## Verification

Run the diagnostic script:
```bash
/usr/local/bin/rdp-browser-test
```

Expected output:
- ✓ /run/user/0 exists
- ✓ Firefox and Chrome can initialize
- ✓ Default browser set to google-chrome.desktop

## Files Modified

1. `/etc/xrdp/startwm.sh` - XDG runtime setup for RDP sessions
2. `/etc/profile.d/xdg-runtime-root.sh` - XDG runtime for shell sessions
3. `/etc/apt/preferences.d/mozilla-firefox` - Pin Mozilla PPA packages
4. `/root/.mozilla/firefox/profiles.ini` - Firefox profile configuration
5. `/root/.mozilla/firefox/default-release/user.js` - Firefox preferences
6. `/root/.config/google-chrome/Default/Preferences` - Chrome preferences
7. `/root/.config/Code/User/settings.json` - VSCode settings
8. `/root/.config/Windsurf/User/settings.json` - Windsurf settings
9. `/usr/local/bin/rdp-browser-test` - Diagnostic script

## Testing

After reconnecting to RDP:
1. Open Firefox - should launch without login prompts
2. Open Chrome - should launch without sync prompts
3. Open VSCode - should not ask for account login
4. Open Windsurf - should not ask for account login

## Notes

- The sandbox warning `CanCreateUserNamespace() unshare(CLONE_NEWPID): EPERM` is expected when running as root and doesn't affect functionality
- You need to **reconnect your RDP session** for the `/etc/xrdp/startwm.sh` changes to take effect
- All browser data is stored in `/root/.mozilla` and `/root/.config/google-chrome`
