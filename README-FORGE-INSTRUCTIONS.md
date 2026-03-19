# Jovany Owens Forge Instructions - Updated 2026-03-19

## Quick Start (Once Cuttlefish is Running)

1. **Access Titan Console**
   - URL: http://localhost:8081
   - Browser preview: http://127.0.0.1:33285

2. **Create New Device Profile**
   - Click "Forge" tab
   - Fill with Jovany Owens data (see below)
   - Click "Create Device"

3. **Run Full Provision**
   - Add proxy: `socks5h://2eiw7c10o5p:192aqpgq10x@91.231.186.249:1080`
   - Add Google credentials:
     - Email: `jovany.owens59@gmail.com`
     - Password: `YCCvsukin7S`
     - Real phone: `+14304314828`
   - Click "Forge & Provision"

4. **Monitor Progress**
   - Watch 6-step pipeline in UI
   - Phase 9 should complete in 1-3 minutes (was 8-15 min)
   - Total time: 60-90 minutes (first run), 30-40 minutes (re-provision)

## Jovany Owens Profile Data

```
Name: Jovany OWENS
Email: jovany.owens59@gmail.com
Password: YCCvsukin7S
Phone: (707) 836-1915
DOB: 12/11/1959
Address: 1866 W 11th St, Los Angeles, CA 90006
SSN: 219-19-0937
Location: Los Angeles, CA
Device Model: Samsung Galaxy S24
Carrier: T-Mobile US

Credit Card:
- Number: 4638 5123 2034 0405
- Type: Visa
- Exp: 08/2029
- CVV: 051

Proxy:
- Type: SOCKS5
- URL: socks5h://2eiw7c10o5p:192aqpgq10x@91.231.186.249:1080

OTP Phone: +14304314828
```

## Troubleshooting

### If Cuttlefish VM Won't Start:

**Option 1: Docker Cuttlefish**
```bash
docker run -d --privileged \
  -p 6520:6520 \
  -p 8443:8443 \
  --name cuttlefish \
  google/cuttlefish
```

**Option 2: Reinstall Host Package**
```bash
cd /opt/titan/cuttlefish
rm -rf cf
tar -xzf cvd-host_package_new.tar.gz
unzip -q a14-img.zip -d cf/
```

**Option 3: Check System Resources**
```bash
# Check KVM support
lsmod | grep kvm
# Check RAM
free -h
# Check disk space
df -h /opt/titan/cuttlefish
```

### If Provision Still Hangs:

1. Check logs in Titan Console UI
2. Verify Phase 9 batch sizes are reduced (see FIXES-APPLIED.md)
3. Try manual quick_repatch via API:
   ```bash
   curl -X POST http://localhost:8081/api/stealth/patch \
     -H "Authorization: Bearer 1890157c6d02d2dd0eda674a6a9f5e8e7f4f92b412349580abbb4ce2d2c7f2bd" \
     -d '{"adb_target":"127.0.0.1:6520","preset":"samsung_s24","carrier":"tmobile_us","location":"la","lockdown":false}'
   ```

## Expected Results

After successful forge and provision:
- Trust Score: 84/100 (Grade A)
- Stealth Score: 72-91% (depending on ro.* props)
- All GApps installed (GMS, GSF, Play Store, etc.)
- Profile ID: TITAN-xxxxxx
- Device: dev-cvd001

## Verification

1. Check device status in Titan Console
2. Run stealth audit: `/api/stealth/audit`
3. Verify Google account signed in
4. Check proxy is active
5. Confirm all 6 provision steps completed

## Notes

- The hanging issue has been fixed at the code level
- Phase 9 batch sizes are optimized for Cuttlefish VMs
- Quick re-patch option available for subsequent runs
- All progress now visible in logs at INFO level
