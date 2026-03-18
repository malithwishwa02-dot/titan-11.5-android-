# Device Aging Pipeline: Comprehensive Gap Analysis

**Date**: 2026-03-18  
**Scope**: Full audit of 9-stage device aging pipeline  
**Focus**: Profile forging → injection → patching → wallet provisioning → payment detection evasion  
**Status**: CRITICAL GAPS IDENTIFIED - 12 patches required  

---

## EXECUTIVE SUMMARY

The device aging pipeline has **12 critical gaps** preventing reliable payment app acceptance and detection evasion:

| Category | Gap Count | Severity | Impact |
|----------|-----------|----------|--------|
| Payment History | 3 | CRITICAL | Google Pay/banking apps detect new accounts |
| Wallet Injection | 2 | CRITICAL | NFC tap-and-pay fails, Play Integrity rejected |
| Detection Evasion | 4 | CRITICAL | Apps detect virtual device via Play Integrity/SafetyNet |
| Injection Completeness | 2 | HIGH | Missing app-specific data, timestamp inconsistencies |
| OTP Handling | 1 | CRITICAL | Payment verification fails |

---

## 1. PAYMENT HISTORY GAPS (GAP-PH1, GAP-PH2, GAP-PH3)

### GAP-PH1: No Transaction History Injection

**Current State**:
- `android_profile_forge.py` generates: contacts, SMS, call logs, cookies, history, gallery, WiFi, app installs, play purchases, app usage, maps history
- **MISSING**: Transaction history, payment receipts, purchase confirmations, refund records

**Impact**:
- Google Pay detects account as brand new (no prior transactions)
- Banking apps reject card (fraud detection flags new account)
- BNPL apps require transaction history for credit assessment
- Payment apps see inconsistency: card exists but no purchase history

**Root Cause**:
- `profile_injector.py` has `_inject_play_purchases()` but only injects app purchase records
- No transaction history in banking app databases
- No payment receipt injection
- No purchase confirmation emails

**Detection Vector**:
```
Google Pay checks:
  - tapandpay.db token creation timestamp
  - GMS billing history (vending.db)
  - Play Store purchase history depth
  - If all recent (< 24h), flags as suspicious
```

**Patch Required**: P3-1 (Payment History Forging)
- Generate realistic transaction history (50-200 transactions based on age_days)
- Add merchant category diversity (grocery, gas, restaurants, retail, utilities)
- Include refunds/chargebacks (2-5% of transactions)
- Inject into banking app databases
- Add payment receipt emails
- Backdate all timestamps to match profile age

---

### GAP-PH2: No OTP Interception/Handling

**Current State**:
- SMS injection includes OTP templates in `SMS_TEMPLATES["otp"]`
- **MISSING**: OTP interception during payment flows, auto-fill mechanism

**Impact**:
- Payment verification popups appear (user must manually enter OTP)
- Device appears unattended (no human interaction)
- Apps detect automated behavior
- Future payments fail (OTP not intercepted)

**Root Cause**:
- `profile_injector.py` injects SMS but doesn't hook payment flows
- No OTP interception service running
- No auto-fill mechanism for payment verification
- No SMS listener for real-time OTP capture

**Detection Vector**:
```
Payment apps check:
  - OTP popup appears → device not responding
  - No human interaction detected
  - Flags as bot/automated device
```

**Patch Required**: P3-3 (OTP Interception & Handling)
- Implement SMS listener service
- Hook payment app OTP flows
- Auto-fill OTP in verification dialogs
- Handle time-limited OTP codes
- Support multiple OTP formats (6-digit, alphanumeric)

---

### GAP-PH3: No Payment Pattern Modeling

**Current State**:
- `android_profile_forge.py` generates purchase history but with random timestamps
- **MISSING**: Realistic payment patterns (spending by time/location/merchant)

**Impact**:
- Fraud detection flags unrealistic patterns
- Spending appears random (no circadian pattern)
- No merchant category clustering
- No location-based spending patterns

**Root Cause**:
- Purchase generation uses `self._rng.randint()` for timestamps
- No circadian weighting for payment times
- No merchant category analysis
- No spending amount distribution modeling

**Detection Vector**:
```
Fraud detection checks:
  - Spending patterns (time-of-day, day-of-week)
  - Merchant category clustering
  - Location consistency
  - Amount distribution (normal vs anomalous)
  - If patterns appear random → flags as suspicious
```

**Patch Required**: P3-6 (Payment Pattern Modeling)
- Generate realistic spending patterns by time-of-day
- Add merchant category clustering
- Model spending by location
- Create realistic amount distributions
- Include recurring transactions (subscriptions)

---

## 2. WALLET INJECTION GAPS (GAP-WP1, GAP-WP2)

### GAP-WP1: Incomplete Google Pay Tokenization

**Current State**:
- `wallet_provisioner.py` generates DPAN and writes to `tapandpay.db`
- **MISSING**: Complete EMV tokenization flow, NFC tap-and-pay simulation

**Impact**:
- NFC tap-and-pay fails (incomplete token)
- Play Integrity checks fail (no valid token)
- Banking apps reject card (token validation fails)
- Payment apps detect incomplete wallet setup

**Root Cause**:
- `generate_dpan()` creates DPAN but doesn't validate against real tokenization
- No EMV handshake simulation
- No NFC tap-and-pay flow
- Missing token metadata (expiry, issuer, risk level)

**Detection Vector**:
```
Google Pay checks:
  - Token validity (EMV compliance)
  - DPAN matches issuer BIN range
  - Token expiry date
  - NFC capability flags
  - If token invalid → rejects card
```

**Patch Required**: P3-2 (Google Pay Tokenization Completion)
- Validate DPAN against real TSP BIN ranges
- Add token metadata (expiry, issuer, risk)
- Implement EMV handshake simulation
- Add NFC tap-and-pay flow
- Validate token against issuer requirements

---

### GAP-WP2: Missing Play Store Billing Integration

**Current State**:
- `wallet_provisioner.py` has `_provision_play_store()` but incomplete
- **MISSING**: Full Play Store billing database schema, payment method visibility

**Impact**:
- Play Store doesn't recognize card as payment method
- App purchases fail (no valid payment method)
- Billing history doesn't show card
- Apps detect missing Play Store integration

**Root Cause**:
- `_provision_play_store()` only writes basic fields
- Missing COIN.xml structure
- No payment method visibility flags
- Missing billing preference fields

**Detection Vector**:
```
Play Store checks:
  - Payment method in vending.db
  - Billing history (COIN.xml)
  - Payment method visibility
  - If missing → shows "Add payment method" prompt
```

**Patch Required**: P3-2 (included in tokenization patch)
- Complete Play Store billing schema
- Add COIN.xml structure
- Set payment method visibility flags
- Add billing history records

---

## 3. DETECTION EVASION GAPS (GAP-SE1, GAP-SE2, GAP-SE3, GAP-SE4)

### GAP-SE1: No Play Integrity API Spoofing

**Current State**:
- `anomaly_patcher.py` patches 103+ system properties
- **MISSING**: Play Integrity API hook, device attestation spoofing

**Impact**:
- Play Integrity API returns "DEVICE_INTEGRITY_FAILED"
- Payment apps reject device (fails Play Integrity check)
- Google Play rejects device (fails attestation)
- Banking apps detect virtual device

**Root Cause**:
- No hook for Play Integrity API calls
- No device attestation spoofing
- No keybox.xml validation
- Missing RKA (Remote Key Attestation) implementation

**Detection Vector**:
```
Play Integrity API checks:
  - Device certification (MEETS_DEVICE_INTEGRITY, MEETS_STRONG_INTEGRITY)
  - App integrity (MEETS_APP_INTEGRITY)
  - If fails → device rejected
```

**Patch Required**: P3-4 (Play Integrity API Spoofing)
- Implement Play Integrity API hook
- Return valid device attestation
- Spoof device certification
- Implement keybox.xml validation
- Add RKA proxy support

---

### GAP-SE2: No SafetyNet Attestation Spoofing

**Current State**:
- `anomaly_patcher.py` patches properties but not SafetyNet
- **MISSING**: SafetyNet attestation hook, JWS token spoofing

**Impact**:
- SafetyNet attestation fails
- Apps using SafetyNet reject device
- Banking apps detect virtual device
- Payment apps fail attestation check

**Root Cause**:
- No SafetyNet API hook
- No JWS token generation
- No attestation response spoofing

**Detection Vector**:
```
SafetyNet checks:
  - ctsProfileMatch (device passes CTS)
  - basicIntegrity (basic device integrity)
  - evaluationType (BASIC vs STRONG)
  - If fails → device rejected
```

**Patch Required**: P3-4 (included in Play Integrity patch)
- Implement SafetyNet API hook
- Generate valid JWS tokens
- Spoof attestation responses

---

### GAP-SE3: Device Property Inconsistency

**Current State**:
- `anomaly_patcher.py` patches properties but may have inconsistencies
- **MISSING**: Property consistency validation, cross-app validation

**Impact**:
- Apps detect property inconsistencies
- Device fingerprinting identifies virtual device
- Payment apps reject device
- Forensic analysis detects spoofing

**Root Cause**:
- Properties patched independently
- No consistency checks across apps
- No validation against real device profiles
- Missing property interdependencies

**Detection Vector**:
```
Apps check:
  - ro.product.model consistency
  - ro.product.brand consistency
  - ro.product.manufacturer consistency
  - ro.build.fingerprint consistency
  - If inconsistent → flags as suspicious
```

**Patch Required**: P3-5 (Device Property Validation)
- Audit all system properties
- Ensure consistency across apps
- Validate against real device profiles
- Check property interdependencies

---

### GAP-SE4: Missing Keybox/Attestation Chain

**Current State**:
- `anomaly_patcher.py` has `_patch_keybox()` but incomplete
- **MISSING**: Full keybox.xml structure, attestation chain validation

**Impact**:
- Play Integrity Strong fails (no valid keybox)
- NFC tap-and-pay fails (no keybox for EMV)
- Banking apps reject device (keybox validation fails)
- Payment apps detect missing attestation

**Root Cause**:
- Keybox.xml incomplete or missing
- No attestation chain validation
- Missing certificate chain
- No TEE simulation

**Detection Vector**:
```
Attestation checks:
  - Keybox.xml validity
  - Certificate chain validation
  - TEE presence check
  - If invalid → fails attestation
```

**Patch Required**: P3-4 (included in Play Integrity patch)
- Complete keybox.xml structure
- Add full certificate chain
- Implement TEE simulation
- Validate attestation chain

---

## 4. INJECTION COMPLETENESS GAPS (GAP-INJ1, GAP-INJ2)

### GAP-INJ1: Limited App-Specific Injection

**Current State**:
- `profile_injector.py` injects generic data
- **MISSING**: Banking app-specific data, BNPL app fields, payment app databases

**Impact**:
- Banking apps detect missing data
- BNPL apps show incomplete profile
- Payment apps missing required fields
- Apps appear newly installed

**Root Cause**:
- `_inject_app_data()` only handles generic SharedPrefs
- No banking app database schema
- No BNPL app-specific fields
- Missing payment app injection

**Patch Required**: P3-7 (App-Specific Injection Expansion)
- Add banking app database schema
- Implement BNPL app field injection
- Add payment app-specific data
- Inject app-specific SharedPrefs

---

### GAP-INJ2: Timestamp Consistency Issues

**Current State**:
- Timestamps generated independently
- **MISSING**: Monotonic progression validation, device age consistency

**Impact**:
- Forensic analysis detects timestamp anomalies
- Apps detect inconsistent timestamps
- Device age doesn't match data age
- Timestamps appear out-of-order

**Root Cause**:
- Timestamps generated with `self._rng.randint()`
- No monotonic progression checks
- No device age validation
- Missing timestamp consistency across databases

**Patch Required**: P3-8 (Timestamp Consistency Validation)
- Audit all timestamps
- Ensure monotonic progression
- Validate against device age
- Check consistency across databases

---

## 5. WORKFLOW ORCHESTRATION GAPS

### GAP-WO1: Stage Ordering Issues

**Current State** (from `workflow_engine.py` lines 136-157):
```
0. bootstrap_gapps  → Install GMS/Play Store/Chrome/GPay
1. forge_profile    → Generate persona data
2. install_apps     → Install apps via AI agent
3. inject_profile   → Inject forged data
4. setup_wallet     → Provision payment cards
5. patch_device     → Apply stealth patches
6. warmup_browse    → Natural browsing
7. warmup_youtube   → Natural YouTube usage
8. verify_report    → Generate verification report
```

**Issue**: Wallet injection (stage 4) happens BEFORE patching (stage 5)
- Wallet data written before stealth patches applied
- Timestamps may be inconsistent with patched properties
- Device properties change after wallet injection

**Impact**:
- Wallet data timestamps don't match patched device age
- Property changes after wallet injection may invalidate tokens
- Inconsistency between wallet data and device properties

**Fix**: Reorder stages to: forge → patch → inject → wallet → apps → warmup → verify

---

## 6. CRITICAL DETECTION VECTORS

### Vector 1: Play Integrity API
```
Apps affected: Google Play, banking apps, BNPL apps, payment apps
Check: MEETS_DEVICE_INTEGRITY, MEETS_STRONG_INTEGRITY
Current status: UNPROTECTED
```

### Vector 2: SafetyNet Attestation
```
Apps affected: Legacy banking apps, payment apps
Check: ctsProfileMatch, basicIntegrity
Current status: UNPROTECTED
```

### Vector 3: Payment History Depth
```
Apps affected: Google Pay, banking apps, BNPL apps
Check: Transaction count, merchant diversity, spending patterns
Current status: UNPROTECTED
```

### Vector 4: OTP Interception
```
Apps affected: All payment apps
Check: OTP popup response time, auto-fill capability
Current status: UNPROTECTED
```

### Vector 5: Device Property Consistency
```
Apps affected: All apps
Check: Property consistency, fingerprint validity
Current status: PARTIALLY PROTECTED
```

---

## 7. PATCH IMPLEMENTATION PLAN

### Phase 3A: Payment History & Realism (3 patches)

**P3-1: Payment History Forging** (4 hours)
- File: `core/payment_history_forge.py` (NEW)
- Generate transaction history (50-200 based on age_days)
- Add merchant category diversity
- Include refunds/chargebacks
- Integrate with `android_profile_forge.py`

**P3-2: Google Pay Tokenization Completion** (5 hours)
- File: `core/wallet_provisioner.py` (MODIFY)
- Complete EMV tokenization flow
- Add token metadata validation
- Implement NFC tap-and-pay simulation
- Complete Play Store billing schema

**P3-3: OTP Interception & Handling** (3 hours)
- File: `core/otp_interceptor.py` (NEW)
- Implement SMS listener service
- Hook payment app OTP flows
- Auto-fill OTP in dialogs
- Handle time-limited codes

### Phase 3B: Detection Evasion (3 patches)

**P3-4: Play Integrity API Spoofing** (4 hours)
- File: `core/play_integrity_spoofer.py` (NEW)
- Hook Play Integrity API
- Return valid attestation
- Implement keybox validation
- Add RKA proxy support

**P3-5: Device Property Validation** (3 hours)
- File: `core/property_validator.py` (NEW)
- Audit all system properties
- Ensure consistency
- Validate against real devices
- Check interdependencies

**P3-6: Payment Pattern Modeling** (3 hours)
- File: `core/payment_pattern_forge.py` (NEW)
- Generate realistic spending patterns
- Add merchant clustering
- Model location-based spending
- Include recurring transactions

### Phase 3C: Injection Completeness (2 patches)

**P3-7: App-Specific Injection Expansion** (4 hours)
- File: `core/profile_injector.py` (MODIFY)
- Add banking app schema
- Implement BNPL fields
- Add payment app data
- Expand SharedPrefs injection

**P3-8: Timestamp Consistency Validation** (2 hours)
- File: `core/timestamp_validator.py` (NEW)
- Audit all timestamps
- Ensure monotonic progression
- Validate device age consistency
- Check database consistency

---

## 8. TESTING STRATEGY

### Unit Tests
- Payment history generation (realistic patterns)
- OTP interception (SMS parsing, auto-fill)
- Play Integrity spoofing (API responses)
- Property validation (consistency checks)
- Timestamp validation (monotonic progression)

### Integration Tests
- Full pipeline with all patches
- Device aging with payment history
- Wallet injection with tokenization
- Payment app acceptance
- OTP handling in payment flows

### Real-World Tests
- Google Pay acceptance
- Banking app acceptance
- BNPL app acceptance
- Payment verification (OTP)
- Fraud detection evasion

---

## 9. SUCCESS CRITERIA

- [ ] Payment history injection working (50-200 transactions)
- [ ] Google Pay tokenization complete (EMV + NFC)
- [ ] OTP interception functional (auto-fill in payment flows)
- [ ] Play Integrity spoofing working (MEETS_STRONG_INTEGRITY)
- [ ] Device property consistency validated
- [ ] Payment pattern modeling realistic
- [ ] App-specific injection expanded
- [ ] Timestamp consistency validated
- [ ] All 8 patches tested and documented
- [ ] End-to-end pipeline validation passing
- [ ] Real payment app acceptance (Google Pay, banking apps)

---

## 10. RISK ASSESSMENT

### High Risk
- Play Integrity spoofing (frequent API updates)
- SafetyNet attestation (deprecated but still used)
- OTP interception (app-specific implementations)

### Medium Risk
- Payment history injection (database schema changes)
- Device property consistency (property interdependencies)
- Timestamp validation (forensic detection)

### Low Risk
- Payment pattern modeling (statistical analysis)
- App-specific injection (database schema stable)

---

## CONCLUSION

The device aging pipeline has **12 critical gaps** preventing reliable payment app acceptance. The most critical gaps are:

1. **No payment history** (apps detect new accounts)
2. **No Play Integrity spoofing** (apps reject device)
3. **No OTP interception** (verification fails)
4. **Incomplete wallet tokenization** (NFC fails)
5. **No payment pattern modeling** (fraud detection flags)

All gaps are addressable with the 8-patch remediation plan. Implementation should proceed sequentially with comprehensive testing at each stage.

