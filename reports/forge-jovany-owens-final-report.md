# Titan Device Forge — Final Report
## Profile: Jovany Owens (TITAN-5180EDF0)

**Date:** 2026-03-19
**Device:** dev-cvd001 (Cuttlefish Android 14, ADB 127.0.0.1:6520)

---

## Identity
| Field | Value |
|-------|-------|
| **Name** | Jovany Owens |
| **Email** | adiniorjuniorjd28@gmail.com |
| **Phone** | +14304314828 |
| **DOB** | 12/11/1959 |
| **Location** | Los Angeles, CA |
| **Device Model** | Samsung Galaxy S24 (SM-S921U) |
| **Carrier** | T-Mobile (310260) LTE |
| **Card** | Visa ****0405 (DPAN ****8132) |

## Stealth Scores
| Metric | Result |
|--------|--------|
| **Patch Score** | 153/153 (100%) |
| **Audit Score** | 4/4 (100%) |
| **Wallet Verify** | 8/8 (100%) |

## Injected Data
| Type | Count |
|------|-------|
| **Contacts** | 257 |
| **Call Logs** | 1,500 |
| **SMS** | 507 |
| **Gallery** | 764 (forged) |
| **Browser History** | 2,500 |
| **WiFi Networks** | 18 |
| **Play Purchases** | 24 |
| **Cookies** | 25 |
| **Email Receipts** | 37 |
| **Maps History** | 1,072 |
| **Notifications** | 301 |
| **App Usage** | 12 |

## Stealth Properties (resetprop)
- **ro.product.model** = SM-S921U
- **ro.product.brand** = samsung
- **ro.build.fingerprint** = samsung/e1qsq/e1q:14/.../user/release-keys
- **ro.kernel.qemu** = 0 (hidden)
- **ro.hardware.virtual** = 0 (hidden)
- **ro.debuggable** = 0
- **ro.secure** = 1
- **ro.build.type** = user
- **ro.boot.verifiedbootstate** = green
- **ro.boot.flash.locked** = 1
- **ro.build.tags** = release-keys

## Google Account
- **Signed in:** adiniorjuniorjd28@gmail.com (com.google)
- **GMS:** Running (3 processes)

## Wallet / Payment
- **Google Pay:** Visa ••••0405 provisioned (tapandpay.db)
- **Play Store billing:** Synced
- **Chrome autofill:** Injected
- **GMS billing:** Synced
- **NFC default:** Google Pay HCE service

## Proxy
- **Global HTTP proxy:** 91.231.186.249:1080
- **Type:** SOCKS5 (global_proxy method)

## GApps Installed
- Google Play Services (GMS) — 19 splits
- Google Services Framework (GSF)
- Play Store
- YouTube
- Google Wallet (8 splits)
- Kiwi Browser

## Notes
- resetprop changes do NOT persist across reboots on erofs — re-patch required after each reboot
- Phase 9 (media history) takes ~200-365s due to gallery/history generation
- Contacts Storage may crash after patcher modifies DB — force-stop resolves it
- Gmail APK not available locally; can be installed from Play Store
- Chrome cannot be installed on Cuttlefish (244MB exceeds binder pipe limit)
