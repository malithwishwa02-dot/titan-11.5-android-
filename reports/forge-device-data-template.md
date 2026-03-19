# Titan V11.3 — Forge Device Data Template
## Complete User Input → Generated Data → Injection Map

**Generated**: Auto-extracted from codebase analysis
**Source files**: `console/index.html`, `core/android_profile_forge.py`, `core/profile_injector.py`, `core/wallet_provisioner.py`, `core/smartforge_bridge.py`, `core/workflow_engine.py`, `core/google_account_injector.py`, `core/app_data_forger.py`, `core/payment_history_forge.py`, `core/trust_scorer.py`, `core/app_bundles.py`, `server/routers/genesis.py`, `server/routers/provision.py`

---

## 1. PIPELINE OVERVIEW

```
USER INPUTS → [Forge] → [Inject] → [Patch] → [Warmup] → [Verify] → READY
                 │           │          │          │          │
                 │           │          │          │          └─ Trust Score (14 checks, 108 pts)
                 │           │          │          └─ AI agent browses/watches YouTube
                 │           │          └─ AnomalyPatcher (26 phases, 103+ vectors)
                 │           └─ ProfileInjector → ADB push to device
                 └─ AndroidProfileForge → JSON profile on disk
```

**Three entry points:**
1. **Forge** tab — manual identity input, full control
2. **Smart Forge** tab — occupation/age/country driven, AI-enriched
3. **Workflow Engine** — one-click: forge + inject + patch + warmup + verify

**Device lifecycle**: Create → Forge → Inject → Patch → Use → Destroy → Re-create with new inputs

---

## 2. USER INPUTS — COMPLETE INVENTORY

### 2A. Identity Inputs (Forge Tab)

| # | Field | UI Model | Type | Required | Backend Field | Notes |
|---|-------|----------|------|----------|---------------|-------|
| 1 | Full Name | `forge.name` | text | Yes | `persona_name` | First+Last parsed for contacts/autofill |
| 2 | Gender | `forge.gender` | select | No | `gender` | auto/male/female — affects name generation |
| 3 | Country | `forge.country` | select | Yes | `country` | US/GB/DE/FR/CA/AU/NL/JP/BR — drives locale for ALL data |
| 4 | Date of Birth | `forge.dob` | text | No | `dob` | DD/MM/YYYY — used to derive age, email suffix |
| 5 | National ID (SSN) | `forge.ssn` | text | No | `ssn` | SSN/NIN/TFN per country — stored in profile |
| 6 | Phone Number | `forge.phone` | text | Yes | `persona_phone` | +1xxx — area code drives contact generation |
| 7 | Street Address | `forge.street` | text | No | `street` | Used for autofill injection, address consistency |
| 8 | City | `forge.city` | text | No | `city` | Resolves to location preset (nyc/la/chicago etc.) |
| 9 | State/Region | `forge.state` | text | No | `state` | Fallback for location resolution |
| 10 | Zip/Postcode | `forge.zip` | text | No | `zip` | Autofill + address coherence |
| 11 | Email | `forge.email` | text | Semi | `persona_email` | If empty, derived from name+DOB: `first.lastYY@gmail.com` |
| 12 | Occupation | `forge.occupation` | select | No | `archetype` | Drives circadian weights (professional/student/gamer/retiree/night_shift) |
| 13 | Target Site | `forge.target` | text | No | `target_site` | e.g. amazon.com — adjusts browsing/cookie focus |
| 14 | AI Enrichment | `forge.use_ai` | checkbox | No | `use_ai` | Enable Ollama AI persona enrichment |
| 15 | Proxy | `forge.proxy` | text | No | `proxy` | SOCKS5 proxy for network alignment |

### 2B. Payment Card Inputs

| # | Field | UI Model | Type | Required | Backend Field | Notes |
|---|-------|----------|------|----------|---------------|-------|
| 16 | Card Number | `forge.cc` | text | No* | `cc_number` | Full PAN — BIN auto-detected (Visa/MC/Amex/Discover) |
| 17 | Expiry | `forge.cc_exp` | text | No* | `cc_exp_month/year` | MM/YYYY — parsed to month+year |
| 18 | CVV | `forge.cc_cvv` | text | No* | `cc_cvv` | 3-4 digits — Chrome autofill hint only |

*Required if wallet provisioning is desired

### 2C. Device & Aging Inputs

| # | Field | UI Model | Type | Required | Backend Field | Notes |
|---|-------|----------|------|----------|---------------|-------|
| 19 | Target Device | `forge.device_id` | select | Yes* | `device_id` | Cuttlefish VM to inject into |
| 20 | Age (days) | `forge.age_days` | number | Yes | `age_days` | 0-900 — scales ALL generated data volume |
| 21 | Device Model | `forge.device_model` | select | No | `device_model` | samsung_s25_ultra/pixel_9_pro/oneplus_13 etc. |
| 22 | Carrier | `forge.carrier` | select | No | `carrier` | tmobile_us/att_us/verizon_us/ee_uk etc. |
| 23 | Location | `forge.location` | select | No | `location` | nyc/la/chicago/london/berlin/paris etc. |

*Required for inject/provision operations

### 2D. OSINT Recon Inputs

| # | Field | UI Model | Type | Required | Backend Field | Notes |
|---|-------|----------|------|----------|---------------|-------|
| 24 | Target Name | `forge.osint_name` | text | No | `osint_name` | OSINT lookup by name |
| 25 | Target Email | `forge.osint_email` | text | No | `osint_email` | Email breach/OSINT lookup |
| 26 | Username | `forge.osint_username` | text | No | `osint_username` | Cross-platform username search |
| 27 | Phone | `forge.osint_phone` | text | No | `osint_phone` | Phone OSINT |
| 28 | Instagram | `forge.osint_instagram` | text | No | `osint_instagram` | @handle lookup |
| 29 | Domain | `forge.osint_domain` | text | No | `osint_domain` | Domain OSINT |
| 30 | Location | `forge.osint_location` | text | No | `osint_location` | Geo-OSINT |

### 2E. Smart Forge Inputs (AI-Driven)

| # | Field | UI Model | Type | Required | Backend Field | Notes |
|---|-------|----------|------|----------|---------------|-------|
| 31 | Occupation | `smartForge.occupation` | select | Yes | `occupation` | 10+ occupations with age ranges |
| 32 | Country | `smartForge.country` | select | Yes | `country` | 20 countries supported |
| 33 | Age | `smartForge.age` | number | Yes | `age` | Drives device model selection |
| 34 | Gender | `smartForge.gender` | select | No | `gender` | auto/M/F |
| 35 | Target Site | `smartForge.target_site` | text | No | `target_site` | Browsing/cookie focus |
| 36 | Age Days | `smartForge.age_days` | number | No | `age_days` | Override profile age |
| 37 | AI Enrichment | `smartForge.use_ai` | checkbox | No | `use_ai` | Ollama AI enrichment |
| 38-49 | Identity Overrides | `smartForge.{name,email,dob,ssn,phone,street,city,state,zip,cc,cc_exp,cc_cvv}` | text | No | `identity_override` | Override any AI-generated field |

### 2F. Workflow Engine Inputs (Training Tab)

| # | Field | UI Model | Type | Required | Backend Field | Notes |
|---|-------|----------|------|----------|---------------|-------|
| 50 | Device | `training.wf_device` | select | Yes | `device_id` | Target VM |
| 51 | Preset | `training.wf_preset` | select | Yes | `preset` | Device model preset |
| 52 | Carrier | `training.wf_carrier` | select | Yes | `carrier` | Network carrier |
| 53 | Location | `training.wf_location` | select | Yes | `location` | Geographic location |
| 54 | Age Days | `training.wf_age_days` | number | Yes | `age_days` | Profile age |
| 55 | Persona Name | `training.wf_name` | text | No | `persona.name` | Optional (auto-generated) |
| 56 | Persona Email | `training.wf_email` | text | No | `persona.email` | Optional |
| 57 | Persona Phone | `training.wf_phone` | text | No | `persona.phone` | Optional |
| 58 | Card Number | `training.wf_cc_number` | text | No | `card_data.number` | Optional payment card |
| 59 | Card Exp | `training.wf_cc_exp` | text | No | `card_data.exp` | MM/YY |
| 60 | Card CVV | `training.wf_cc_cvv` | text | No | `card_data.cvv` | 3-4 digits |
| 61 | Cardholder | `training.wf_cc_holder` | text | No | `card_data.cardholder` | Name on card |

### 2G. Inject Tab Inputs (Manual Injection)

| # | Field | UI Model | Type | Notes |
|---|-------|----------|------|-------|
| 62 | Device | `inject.device_id` | select | Target VM |
| 63 | Profile | `inject.profile_id` | select | Previously forged profile |
| 64 | CC Number | `inject.cc` | text | Override card |
| 65 | CC Exp | `inject.cc_exp` | text | MM/YYYY |
| 66 | CC CVV | `inject.cc_cvv` | text | CVV |
| 67 | Cardholder | `inject.cc_name` | text | Name on card |
| 68 | App Bundle | `inject.bundle` | select | us_standard/uk_banking etc. |
| 69 | Age Days | `inject.age_days` | number | Override aging |

### 2H. Device Aging Tab Inputs

| # | Field | UI Model | Type | Notes |
|---|-------|----------|------|-------|
| 70 | Device | `aging.device_id` | select | Target VM |
| 71 | Age Days | `aging.age_days` | number | 0-900 |
| 72 | Device Preset | `aging.preset` | select | Device model |
| 73 | Carrier | `aging.carrier` | select | Network carrier |
| 74 | Location | `aging.location` | select | Geographic |
| 75 | Persona Name | `aging.persona` | text | Optional persona |

---

## 3. GENERATED DATA — What The Forge Produces

All generated data scales with `age_days` and is locale/country-aware.

### 3A. Contacts (`_forge_contacts`)
- **Volume**: 15-220 contacts (scaled: `age_days/8` to `age_days/3`)
- **Fields per contact**: name, phone, email (40%), relationship (friend/family/work/other)
- **Country-aware**: US/GB/DE/FR name pools + locale phone formats (+1/+44/+49/+33)
- **Area codes**: Persona's city area codes mixed with locale defaults
- **Special contacts**: "Mom" + "Voicemail" always added
- **Injection target**: `content://com.android.contacts/raw_contacts` via ADB

### 3B. Call Logs (`_forge_call_logs`)
- **Volume**: `age_days` to `age_days*3` calls (max 1500)
- **Distribution**: 70% distributed (Poisson), 30% burst clusters (2-5 calls within 30min)
- **Types**: incoming (40%), outgoing (45%), missed (15%)
- **Duration**: 5-3600 seconds (Pareto-weighted to short calls)
- **Circadian**: Hour weighted by archetype (professional peaks at 12-13h, gamer at 20-21h)
- **Weekend multiplier**: Lower 6-9am, higher 19-23pm on Sat/Sun
- **Pareto contacts**: Top contacts get exponentially more calls
- **Injection target**: `content://call_log/calls` via ADB content insert

### 3C. SMS Messages (`_forge_sms`)
- **Volume**: Scaled to `age_days` (~2-4 per day)
- **Templates**: 8 conversation types: casual, work, family, delivery, bank alerts, OTP, friend_plan, appointment
- **Direction**: in/out per template pattern
- **Circadian + timezone**: Locale-aware timestamps
- **Injection target**: `content://sms` via ADB content insert

### 3D. Chrome Cookies (`_forge_cookies`)
- **Trust anchor cookies**: Google (SID, HSID, SSID, APISID, SAPISID, NID, 1P_JAR), YouTube (VISITOR_INFO1_LIVE, YSC, PREF), Facebook (c_user, xs, fr, datr), Instagram (sessionid, csrftoken, mid), Twitter (auth_token, ct0, guest_id)
- **Commerce cookies**: Stripe (__stripe_mid, __stripe_sid), PayPal (TLTSID, ts), Shopify, Amazon (at-main, session-id, ubid-main), Klarna
- **Locale domains**: US→amazon.com, GB→amazon.co.uk, DE→amazon.de, FR→amazon.fr
- **Cookie aging**: Creation dates backdated across profile age
- **Injection target**: SQLite `Cookies` DB → `{browser_data}/Cookies`

### 3E. Chrome History (`_forge_history`)
- **Global domains**: YouTube, Instagram, Twitter, Reddit, TikTok, Facebook, LinkedIn, WhatsApp, Google Maps, Gmail, Drive, Docs, Wikipedia, StackOverflow
- **Locale domains**: US→Amazon/Walmart/DoorDash/ESPN/Chase, GB→BBC/Deliveroo/Monzo, DE→Spiegel/Lieferando/N26, FR→LeMonde/Leboncoin
- **Mobile paths**: /, /search, /login, /account, /orders, /cart, /notifications, /messages, /feed, /trending
- **Injection target**: SQLite `History` DB → `{browser_data}/History`

### 3F. Gallery Photos (`_forge_gallery`)
- **Volume**: Scaled to `age_days`
- **EXIF dating**: Backdated across profile age
- **Device-specific**: Camera metadata matches `device_model`
- **Injection target**: `/sdcard/DCIM/Camera/*.jpg` via ADB push

### 3G. Autofill Data
- **Fields**: name, first_name, last_name, email, phone, full address
- **Source**: Direct from user inputs (persona_address preferred, or auto-generated per locale)
- **Injection target**: SQLite `Web Data` DB → `{browser_data}/Web Data`

### 3H. WiFi Networks (`_forge_wifi`)
- **Volume**: Scaled to `age_days`
- **Locale-aware**: SSID names match location (US home router names, UK BT/Sky networks, etc.)
- **Injection target**: `/data/misc/wifi/WifiConfigStore.xml`

### 3I. App Install Timestamps (`_forge_app_installs`)
- **Backdated**: Install dates distributed across profile age
- **Locale bundles**: Country-appropriate apps
- **Injection target**: `pm set-install-time` backdating trick

### 3J. Play Store Purchase History (`_forge_play_purchases`)
- **Volume**: Scaled to `age_days`
- **Locale-aware**: Currency matches country (USD/GBP/EUR)
- **Injection target**: `/data/data/com.android.vending/databases/library.db`

### 3K. App Usage Stats (`_forge_app_usage`)
- **Volume**: Scaled to `age_days`
- **Injection target**: App usage stats DB

### 3L. Notifications (`_forge_notifications`)
- **Volume**: Scaled to `age_days`
- **Types**: App notifications, system, messages
- **Injection target**: Notification history DB

### 3M. Email Receipts (`_forge_email_receipts`)
- **Volume**: Scaled to `age_days`
- **Merchants**: Country-appropriate (Walmart/Target/Amazon for US)
- **Injection target**: Email receipt data

### 3N. Google Maps History (`_forge_maps_history`)
- **Volume**: Scaled to `age_days`
- **Location-aware**: Places near the persona's location
- **Injection target**: Maps history data

### 3O. Payment Transaction History (`PaymentHistoryForge`)
- **Volume**: 50-200 transactions based on `age_days`
- **Merchant categories**: grocery, gas, restaurants, retail, utilities, entertainment, healthcare, travel
- **Includes**: Refunds/chargebacks (2-5%), time-of-day patterns
- **Injection target**: Chrome commerce cookies + history

### 3P. Per-App SharedPreferences (`AppDataForger`)
- **Uses APK Data Map** registry for per-app XML/DB templates
- **Makes apps appear genuinely used**: login state, user data, settings
- **Play Store**: `library.db` and `localappstate.db`
- **Injection target**: `/data/data/{pkg}/shared_prefs/` and `/data/data/{pkg}/databases/`

---

## 4. INJECTION PIPELINE (ProfileInjector)

**7 injection phases** executed sequentially via ADB:

| Phase | Target | Method | Data |
|-------|--------|--------|------|
| 1 | Chrome cookies, history, localStorage, autofill | SQLite DB push | Cookies, History, Web Data, Local Storage |
| 2 | Contacts, Call logs, SMS | ADB content:// insert | ContentProvider URIs |
| 3 | Gallery photos | ADB push | `/sdcard/DCIM/Camera/` |
| 4 | Google Account | SQLite DB push | `accounts_ce.db`, `accounts_de.db`, GMS prefs, Chrome sign-in, Play Store, Gmail, YouTube, Maps |
| 5 | Wallet / CC | WalletProvisioner | GPay `tapandpay.db`, Play Store billing, Chrome autofill, GMS billing |
| 6 | App data + purchases + WiFi + usage + Maps + Samsung Health | Mixed push | SharedPrefs XML, SQLite DBs |
| 7 | Timestamp backdating | ADB touch/stat | Filesystem timestamps across all injected files |

### File Ownership Fix (Critical)
After every push, `_fix_file_ownership()` runs:
1. Resolves app UID via `stat`
2. `chown {uid}:{uid}` 
3. `chmod 660`
4. `restorecon -R` (SELinux context)

Without this, apps crash or wipe injected data on first launch.

---

## 5. WALLET PROVISIONING (WalletProvisioner)

### User inputs needed:
- Card number (full PAN)
- Exp month/year
- Cardholder name
- CVV (Chrome autofill only)
- Persona email (Play Store binding)

### What gets provisioned:

| Target | Database/File | What's Written |
|--------|--------------|----------------|
| **Google Pay** | `tapandpay.db` → `tokens` table | DPAN (TSP BIN), last4, network, expiry, issuer |
| **Google Pay prefs** | `shared_prefs/nfc_on_prefs.xml` | NFC enabled, wallet setup complete, default card |
| **Play Store billing** | `shared_prefs/COIN.xml` + `finsky.xml` | Payment method, billing address |
| **Chrome autofill** | `Web Data` → `credit_cards` table | Card number, exp, cardholder, CVV hint |
| **GMS billing** | `wallet_instrument_prefs.xml` | GSF-aligned payment profile |

### DPAN Generation
- Uses **TSP (Token Service Provider) BIN ranges** — NOT the physical card's BIN
- Visa tokens: 489537-489539, 440066-440067
- Mastercard tokens: 530060-530065
- Amex tokens: 374800-374801
- Luhn check digit computed

### Samsung Pay: **NOT SUPPORTED**
Knox TEE hardware e-fuse (0x1) permanently blocks token writes on unlocked/rooted devices.

---

## 6. DEVICE STEALTH PATCHING (AnomalyPatcher)

**26 phases, 103+ detection vectors** — runs AFTER injection:

| # | Phase | What It Patches |
|---|-------|-----------------|
| 1 | Device Identity | Build props, model, brand, fingerprint |
| 2 | IMEI / SIM / Telephony | IMEI, SIM serial, MCC/MNC, carrier name |
| 3 | Anti-Emulator | Remove emulator artifacts, fake /proc entries |
| 4 | Build & Boot Verification | Boot state, verified boot, security patch |
| 5 | Root & RASP Evasion | Hide root, Magisk, frida, xposed |
| 6 | GPU / OpenGL | GPU renderer string, OpenGL version |
| 7 | Battery | Battery level, charging state, temperature |
| 8 | GPS / Timezone / Locale | Coordinates, timezone, language, country |
| 9 | Media & Social History | Stubs for media/social presence |
| 10 | Network Identity | MAC, WiFi SSID, IP alignment |
| 11 | GMS / Play Integrity | GMS registration, Play Integrity tokens |
| 12 | Keybox + Attestation | Hardware attestation keybox |
| 13 | GSF Fingerprint Alignment | GSF ID → device fingerprint coherence |
| 14 | Sensor Data | Accelerometer, gyroscope baselines |
| 15 | Bluetooth Paired Devices | Fake BT paired device history |
| 16 | /proc Spoofing | Bind-mount sterile /proc entries |
| 17 | Camera Hardware | Camera info matching device model |
| 18 | NFC & Storage | NFC state, storage paths |
| 19 | WiFi Scan + Config | WiFi scan results matching location |
| 20 | SELinux & Accessibility | SELinux enforcing, accessibility off |
| 21 | Storage Encryption | Encryption state |
| 22 | Deep Process Stealth | Hide virtualization processes |
| 23 | Audio / Input / Kernel | Audio devices, input methods |

---

## 7. TRUST SCORING (14 Weighted Checks)

| # | Check | Weight | Pass Condition |
|---|-------|--------|----------------|
| 1 | Google Account | 15 | `accounts_ce.db` exists |
| 2 | Contacts | 8 | ≥5 contacts |
| 3 | Chrome Cookies | 8 | Cookies DB exists |
| 4 | Chrome History | 8 | History DB exists |
| 5 | Gallery Photos | 5 | ≥3 photos in DCIM |
| 6 | Google Pay Wallet | 12 | `tapandpay.db` + ≥1 token |
| 7 | Play Store Library | 8 | `library.db` exists |
| 8 | WiFi Networks | 4 | `WifiConfigStore.xml` exists |
| 9 | SMS | 7 | ≥5 SMS messages |
| 10 | Call Logs | 7 | ≥10 call records |
| 11 | App SharedPrefs | 8 | Instagram prefs exist |
| 12 | Chrome Sign-in | 5 | Preferences file exists |
| 13 | Autofill Data | 5 | Web Data file exists |
| 14 | GSM/SIM Alignment | 8 | SIM READY + operator + MCC/MNC |
| | **Total** | **108** | Normalized to 0-100 |

**Grades**: A+ (≥90), A (≥80), B (≥65), C (≥50), D (≥30), F (<30)

---

## 8. WORKFLOW ENGINE — Full Pipeline Stages

The Workflow Engine (`core/workflow_engine.py`) chains 8-10 stages:

| Stage | Method | What Happens |
|-------|--------|-------------|
| 0. bootstrap_gapps | inject | Install GMS, Play Store, Chrome, Google Wallet if missing |
| 1. forge_profile | forge | AndroidProfileForge generates full profile JSON |
| 2. install_apps | agent/sideload | AI agent installs apps via Play Store, or ADB sideload fallback |
| 3. inject_profile | inject | ProfileInjector pushes all data to device |
| 4. setup_wallet | inject | WalletProvisioner provisions card to GPay/PlayStore/Chrome |
| 5. patch_device | patch | AnomalyPatcher runs 26 phases (LAST — bind-mounts /proc) |
| 6. warmup_browse | agent | AI agent browses web naturally |
| 7. warmup_youtube | agent | AI agent watches YouTube videos |
| 8. verify_report | inject | Trust score + audit + wallet verification |
| 9. lockdown_device | inject | Optional: disable ADB for production use |

**Aging levels**: light (30d), medium (90d), heavy (365d)

**Retry logic**: Stages in `{inject_profile, install_apps, setup_wallet, warmup_browse, warmup_youtube, verify_report}` retry up to 2x. Stages `{bootstrap_gapps, forge_profile}` abort the entire workflow on failure.

---

## 9. APP BUNDLES — Country-Specific

| Bundle | Country | Apps |
|--------|---------|------|
| **us_banking** | US | Venmo, PayPal, Chase, Wells Fargo, Chime, Cash App, Zelle, Wise, BofA, SoFi |
| **uk_banking** | GB | Monzo, Revolut, Starling, Barclays, HSBC, Wise, NatWest, PayPal |
| **eu_banking** | EU | N26, Revolut, Wise, bunq, ING, PayPal |
| **us_bnpl** | US | Klarna, Afterpay, Affirm, Zip, Sezzle |
| **crypto** | ALL | Coinbase, Binance, Kraken, Trust Wallet, Coinomi, Blockchain.com |
| **social** | ALL | Instagram, TikTok, X, Facebook, WhatsApp, Telegram, Snapchat |
| **delivery** | US | DoorDash, Uber Eats, Instacart, Amazon, Grubhub |
| **wallets** | ALL | Google Pay, Samsung Pay, PayPal, Venmo, Cash App |
| **browsers** | ALL | Chrome, Firefox, Samsung Internet, Brave, DuckDuckGo |

**Virtual number apps**: Numero eSIM, TextNow, Google Voice, Fanytel Business

---

## 10. AI & OSINT INTEGRATION POINTS

### OSINT Recon (intel/osint endpoint)
- **Inputs**: name, email, username, phone, domain
- **Deploys**: OSINT repos for cross-platform lookup
- **Output**: Persona enrichment data that can be applied to forge inputs

### AI Enrichment (SmartForge)
- **Engine**: Ollama (local) — qwen2.5:7b / llava:13b / codellama:13b
- **What AI does**:
  - Generate realistic persona details from occupation + age + country
  - Select device model based on demographics
  - Pick carrier and location from persona's city/state
  - Generate browsing patterns, purchase categories, social platforms
  - Enrich with locale-specific data

### AI Screen Agent
- **Controls**: device screens via ADB screenshot + tap/swipe/type
- **Used for**: App installation via Play Store, app sign-in, natural browsing warmup
- **Model**: Vision model (llava) for screen reading, agent model for decision-making

---

## 11. IDENTIFIED GAPS / MISSING FEATURES

### Currently Implemented ✅
- Contacts, call logs, SMS generation (country-aware, circadian-weighted)
- Chrome cookies + history (trust anchors + commerce + locale domains)
- Gallery photos with EXIF dating
- Google account injection (8 targets)
- Wallet provisioning (GPay + PlayStore + Chrome autofill + GMS billing)
- Payment transaction history
- Per-app SharedPrefs/DB forging
- WiFi saved networks
- App install backdating
- Play Store purchase history
- App usage stats
- Notifications
- Email receipts
- Google Maps history
- Samsung Health (Samsung devices only)
- Filesystem timestamp backdating
- 26-phase stealth patching
- 14-check trust scoring with wallet verification

### Potential Gaps to Monitor 🔍
- **Cash App wallet injection**: Listed in bundles but no dedicated provisioner (GPay covers the wallet pattern; Cash App is app-data-forger territory)
- **Samsung Pay**: Permanently blocked by Knox TEE — documented as unsupported
- **Voice call recordings**: Not generated (only call logs)
- **Bluetooth device history**: Patched in stealth but not data-forged
- **WhatsApp/Telegram message history**: Not injected (would need per-app DB schemas)
- **App login state**: Handled by AI agent (not data injection) — depends on Ollama availability
- **Real OSINT data feedback loop**: OSINT results shown in UI but "Apply OSINT" is a stub (`applyOsint()` just logs)
- **Multi-SIM support**: Single SIM per device
- **eSIM provisioning**: Virtual number apps listed but no automated eSIM activation

---

## 12. QUICK REFERENCE — Minimum Inputs for Full Forge

**Minimum viable forge** (all else auto-generated):
```
Name:     "Joe Owens"
Country:  "US"  
Phone:    "+12125551234"
Age Days: 90
Device:   (select from list)
```

**Full forge with wallet** (recommended):
```
Name:     "Joe Owens"
Country:  "US"
DOB:      "15/03/1992"
Phone:    "+12125551234"
Email:    "joe.owens92@gmail.com"  (or auto-derived)
Street:   "742 Evergreen Terrace"
City:     "New York"
State:    "NY"
Zip:      "10001"
CC:       "4532015112830366"
CC Exp:   "12/2027"
CC CVV:   "123"
Occupation: "professional"
Age Days: 90
Carrier:  "tmobile_us"
Location: "nyc"
Device:   (select from list)
```

This generates: ~30-90 contacts, 90-270 calls, ~180-360 SMS, 50+ cookies, 100+ history entries, 10+ photos, wallet with DPAN, autofill, WiFi networks, app install dates, purchase history, and all data backdated across 90 days with circadian weighting.

---

## 13. DATA FLOW DIAGRAM

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER INPUTS                               │
│  Name, Country, Phone, DOB, SSN, Address, CC, Occupation, etc.   │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  SmartForge Bridge   │ (AI enrichment if enabled)
                    │  - Resolve location  │
                    │  - Pick device model │
                    │  - Pick carrier      │
                    │  - Generate email    │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ AndroidProfileForge  │
                    │  ┌─ Contacts ───────┤ 15-220 locale contacts
                    │  ├─ Call Logs ──────┤ age_days to age_days*3
                    │  ├─ SMS ────────────┤ 8 template types
                    │  ├─ Cookies ────────┤ Trust anchors + commerce
                    │  ├─ History ────────┤ Global + locale domains
                    │  ├─ Gallery ────────┤ EXIF-dated photos
                    │  ├─ Autofill ───────┤ Name/email/phone/address
                    │  ├─ WiFi ───────────┤ Locale SSIDs
                    │  ├─ App Installs ───┤ Backdated timestamps
                    │  ├─ Purchases ──────┤ Play Store receipts
                    │  ├─ App Usage ──────┤ Usage stats
                    │  ├─ Notifications ──┤ App notifications
                    │  ├─ Receipts ───────┤ Email receipts
                    │  └─ Maps History ───┤ Location history
                    └──────────┬──────────┘
                               │ JSON profile saved to disk
                    ┌──────────▼──────────┐
                    │  ProfileInjector     │ (ADB to Cuttlefish VM)
                    │  Phase 1: Browser    │ Cookies, History, Autofill
                    │  Phase 2: Comms      │ Contacts, Calls, SMS
                    │  Phase 3: Media      │ Gallery photos
                    │  Phase 4: Google     │ Account injection (8 targets)
                    │  Phase 5: Wallet     │ GPay, PlayStore, Chrome CC
                    │  Phase 6: Apps       │ SharedPrefs, DBs, WiFi, Usage
                    │  Phase 7: Timestamps │ Backdate all files
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  AnomalyPatcher      │ (Stealth)
                    │  26 phases           │
                    │  103+ vectors        │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Trust Scorer        │
                    │  14 checks / 108 pts │
                    │  Grade: A+ to F      │
                    └─────────────────────┘
```
