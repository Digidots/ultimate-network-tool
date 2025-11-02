# LLDP VLAN Detection - Testing Guide
## How to Test the New Fluke-Style VLAN Detection

---

## Prerequisites

### 1. **Switch Must Have LLDP Enabled**

Check if LLDP is enabled on your switch:

**Cisco:**
```
show lldp
```

If disabled, enable it:
```
configure terminal
lldp run
interface GigabitEthernet1/0/24
 lldp transmit
 lldp receive
exit
```

**HP/Aruba:**
```
show lldp config
```

Enable if needed:
```
lldp run
```

**Other Vendors:**
Consult switch documentation for LLDP configuration commands.

---

## Testing Steps

### **Step 1: Start the Web Application**

```bash
python app.py
```

Navigate to: `http://localhost:5000`

---

### **Step 2: Select Network Adapter**

1. Click the adapter dropdown
2. Select your connected network interface
3. Verify IP address is shown

---

### **Step 3: Start Switch Discovery**

1. Click **"▶ Start Discovery"** button in the Switch Discovery section
2. Wait 30-60 seconds for LLDP advertisement from switch
3. Watch for:
   - Switch name appears in discovery results
   - Console log shows: `LLDP: Native VLAN detected = X`
   - Console log shows: `LLDP: VLAN X = 'VLAN Name'`

**Expected Discovery Result:**
```
Protocol: LLDP
Switch Name: SW-CORE-01
MAC Address: aa:bb:cc:dd:ee:ff
Port ID: GigabitEthernet1/0/24
Model: Cisco C9300
IP Address: 10.1.1.1
```

---

### **Step 4: Check VLAN Detection Section**

**IMPORTANT:** VLANs should appear **automatically** in the VLAN Detection section WITHOUT clicking "Scan VLANs"!

Look for entries like:
```
VLAN 1 (Native)           | Source: LLDP - Port VLAN ID
VLAN 10 (Data VLAN)       | Source: LLDP - VLAN Name
VLAN 11 (Voice VLAN)      | Source: LLDP - VLAN Name
VLAN 12 (Guest VLAN)      | Source: LLDP - VLAN Name
VLAN 300 (Management VLAN)| Source: LLDP - VLAN Name
VLAN 400 (Security VLAN)  | Source: LLDP - VLAN Name
```

**Key Indicators:**
- ✅ VLAN ID shown
- ✅ VLAN Name shown in gray next to ID (if switch sends it)
- ✅ Source: "LLDP - Port VLAN ID" or "LLDP - VLAN Name"
- ✅ IP Range/Subnet/Gateway will show "N/A" (LLDP doesn't provide this)

---

### **Step 5: Verify Console Logs**

Press `F12` in browser → Console tab

You should see:
```
LLDP VLAN Discovery: {vlan_id: 1, type: 'native', source: 'LLDP - Port VLAN ID'}
LLDP VLAN Discovery: {vlan_id: 10, vlan_name: 'Data VLAN', type: 'tagged', source: 'LLDP - VLAN Name'}
LLDP VLAN Discovery: {vlan_id: 11, vlan_name: 'Voice VLAN', type: 'tagged', source: 'LLDP - VLAN Name'}
...
```

---

### **Step 6: (Optional) Run VLAN Scan to Get DHCP Info**

After LLDP discovers VLANs, you can optionally scan those specific VLANs to get DHCP information:

1. Enter discovered VLAN IDs in "VLANs to Scan" field:
   ```
   1,10,11,12,300,400
   ```

2. Click **"🔍 Scan VLANs"**

3. Now the VLANs will be updated with DHCP information:
   ```
   VLAN 10 (Data VLAN) | IP: 192.168.10.0/24 | Gateway: 192.168.10.254 | Source: LLDP + DHCP
   VLAN 300 (Management VLAN) | IP: N/A | Source: LLDP - VLAN Name
   ```

---

## Expected Results

### **If LLDP is Working Correctly:**

✅ Switch discovery shows switch information after 30-60 seconds
✅ VLANs appear automatically in VLAN Detection section
✅ VLANs 300 and 400 (no DHCP) appear with source "LLDP - VLAN Name"
✅ VLAN names are displayed next to VLAN IDs
✅ Notification appears: "VLANs detected from LLDP advertisement"

### **If LLDP is NOT Working:**

❌ No switch discovery results after 60 seconds
❌ No VLANs appear automatically
❌ Console shows no LLDP-related logs

**Troubleshooting:**
1. Verify LLDP is enabled on switch (see Prerequisites)
2. Verify you're connected to a switch port (not a router/firewall)
3. Check if switch is configured to send TLV Type 7 and Type 127
4. Try different network adapter if multiple available
5. Ensure you're running as Administrator (required for packet capture)

---

## Switch Configuration Example

**Cisco Switch Configuration:**
```
! Enable LLDP globally
lldp run

! Enable LLDP on interface
interface GigabitEthernet1/0/24
 description Connected to Network Tool
 switchport mode trunk
 switchport trunk native vlan 1
 switchport trunk allowed vlan 1,10,11,12,300,400
 lldp transmit
 lldp receive

! Configure VLAN names (optional but recommended)
vlan 10
 name Data VLAN
vlan 11
 name Voice VLAN
vlan 12
 name Guest VLAN
vlan 300
 name Management VLAN
vlan 400
 name Security VLAN
```

---

## Verification Commands

### **On Switch:**

**Check LLDP status:**
```
show lldp
show lldp interface GigabitEthernet1/0/24
```

**Check LLDP neighbors:**
```
show lldp neighbors detail
```

**Verify VLAN configuration:**
```
show vlan brief
show interfaces trunk
```

### **On Your Computer:**

**Check if LLDP packets are being received:**
```powershell
# Using Wireshark filter:
eth.dst == 01:80:c2:00:00:0e and eth.type == 0x88cc
```

---

## What to Expect

### **Timeline:**

- **0-30 seconds:** Switch discovery running, waiting for LLDP
- **30-60 seconds:** First LLDP packet arrives
- **Immediately after LLDP:** VLANs populate in VLAN Detection section
- **Total time:** ~30-60 seconds for complete VLAN list

### **VLAN Information Provided by LLDP:**

| Information | Available? | Notes |
|-------------|------------|-------|
| VLAN ID | ✅ Yes | Always provided |
| VLAN Name | ⚠️ Maybe | Depends on switch config |
| Native VLAN | ✅ Yes | TLV Type 7 |
| IP Range | ❌ No | Requires DHCP scan |
| Subnet Mask | ❌ No | Requires DHCP scan |
| Gateway | ❌ No | Requires DHCP scan |

---

## Known Limitations

### **1. Switch Must Support IEEE 802.1AB LLDP**
- Most managed switches support LLDP
- Some older or consumer-grade switches may not

### **2. VLAN Names May Not Be Sent**
- Switch must be configured to send TLV Type 127 (Organizationally Specific)
- Some switches only send basic TLVs (1-8)
- In this case, you'll see VLAN IDs but not names

### **3. LLDP Broadcast Interval**
- Default: 30 seconds
- Configurable on switch (can be 10-3600 seconds)
- First result may take up to one full interval

### **4. Trunk Port Required**
- Switch must be sending VLAN information
- Access ports won't advertise multiple VLANs

---

## Success Criteria

### **Minimum Success (Basic LLDP):**
✅ Switch discovery shows switch information
✅ At least native VLAN (VLAN 1) appears automatically

### **Full Success (Complete LLDP with VLAN Names):**
✅ Switch discovery shows switch information
✅ All configured VLANs appear automatically
✅ VLAN names are displayed
✅ VLANs 300 and 400 (without DHCP) are detected
✅ Source shows "LLDP - VLAN Name"

---

## Comparison: Before vs After

### **Before LLDP Implementation:**
```
Scan VLANs: 1,10,11,12,300,400

Results:
✅ VLAN 1 - Native + DHCP
✅ VLAN 10 - DHCP Probe
✅ VLAN 11 - DHCP Probe
✅ VLAN 12 - DHCP Probe
❌ VLAN 300 - NOT DETECTED (no DHCP, no traffic)
❌ VLAN 400 - NOT DETECTED (no DHCP, no traffic)
```

### **After LLDP Implementation:**
```
Step 1: Start Switch Discovery (wait 30-60 seconds)

Results (automatic):
✅ VLAN 1 - LLDP - Port VLAN ID
✅ VLAN 10 (Data VLAN) - LLDP - VLAN Name
✅ VLAN 11 (Voice VLAN) - LLDP - VLAN Name
✅ VLAN 12 (Guest VLAN) - LLDP - VLAN Name
✅ VLAN 300 (Management VLAN) - LLDP - VLAN Name ← NEW!
✅ VLAN 400 (Security VLAN) - LLDP - VLAN Name ← NEW!
```

---

## Troubleshooting

### **Issue: No VLANs Appear Automatically**

**Possible Causes:**
1. LLDP not enabled on switch
2. Switch not sending TLV Type 7 or Type 127
3. Not running as Administrator
4. Firewall blocking packet capture

**Solutions:**
1. Enable LLDP on switch (see Prerequisites)
2. Check switch documentation for VLAN TLV support
3. Restart application as Administrator
4. Temporarily disable firewall/antivirus

---

### **Issue: Only Native VLAN Appears**

**Possible Cause:**
Switch is sending TLV Type 7 (Port VLAN ID) but not TLV Type 127 (VLAN Names)

**Solution:**
Check if switch supports sending VLAN names in LLDP. Some switches require explicit configuration:

**Cisco:**
```
lldp tlv-select port-vlan
lldp tlv-select vlan-name
```

---

### **Issue: VLANs Appear But No Names**

**Possible Cause:**
Switch is sending VLAN IDs but not VLAN names (TLV Type 127 Subtype 3)

**Solution:**
This is normal for some switches. The tool will still show the VLAN IDs, just without descriptive names.

**Workaround:**
You can manually note which VLANs are which, or configure VLAN names on the switch if supported.

---

## Next Steps After Testing

### **If LLDP Works:**
1. Document which VLANs were discovered
2. Optionally run DHCP scan on discovered VLANs
3. Export results (future feature: CSV export)

### **If LLDP Doesn't Work:**
1. Fall back to manual VLAN scanning (1,10,11,12,300,400)
2. Use DHCP probe method for VLANs with DHCP servers
3. Consider network documentation for VLAN list

---

## Additional Testing

### **Test Different Switch Vendors:**
- Cisco
- HP/Aruba
- Juniper
- Dell
- Ubiquiti

### **Test Different Port Configurations:**
- Access port (single VLAN)
- Trunk port (multiple VLANs)
- Hybrid port

### **Test LLDP Timing:**
- First LLDP packet arrival time
- Refresh interval (default 30 sec)
- Holdtime (default 120 sec)

---

## Feedback

After testing, please note:
- ✅ Which VLANs were detected
- ✅ Whether VLAN names appeared
- ✅ How long until first LLDP packet
- ✅ Any errors or issues encountered
- ✅ Switch vendor and model

This will help refine the implementation and documentation.

---

**Happy Testing!** 🚀

**Copyright © Digidots 2025**
