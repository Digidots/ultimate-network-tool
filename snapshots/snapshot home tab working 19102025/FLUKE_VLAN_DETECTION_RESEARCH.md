# Fluke VLAN Detection Research
## How Professional Network Testers Detect VLANs

---

## Fluke LinkRunner AT/G2 VLAN Detection Methods

### **Method 1: IEEE 802.1AB (LLDP) VLAN Discovery** ⭐ PRIMARY
**Source:** LLDP TLV Type 7 (Port VLAN ID)

**How Fluke Does It:**
1. Listens for LLDP packets from connected switch
2. Extracts **Port VLAN ID** from TLV Type 7
3. Extracts **VLAN Name** from TLV Type 127 (Organizationally Specific)
4. Gets complete list of **allowed VLANs** on trunk port

**LLDP Packet Structure:**
```
Ethernet Frame
├── Destination: 01:80:c2:00:00:0e (LLDP multicast)
├── Source: Switch MAC
├── Type: 0x88CC (LLDP)
└── TLVs:
    ├── TLV Type 1: Chassis ID
    ├── TLV Type 2: Port ID
    ├── TLV Type 7: Port VLAN ID ← NATIVE VLAN
    ├── TLV Type 127: IEEE 802.1 Organizationally Specific
    │   └── Subtype 3: VLAN Name
    │   └── Subtype 4: Protocol VLAN ID (PPVID)
    └── TLV Type 0: End of LLDPDU
```

**What We Can Extract:**
- Native VLAN ID (untagged)
- VLAN names
- List of voice VLANs
- Protocol VLANs

**Advantage:**
- ✅ Authoritative source (from switch)
- ✅ No active probing required
- ✅ Safe (passive listening)
- ✅ Gets VLAN list in ~30 seconds

---

### **Method 2: CDP (Cisco Discovery Protocol)** ⭐ CISCO NETWORKS
**Source:** CDP Native VLAN field

**How Fluke Does It:**
1. Listens for CDP packets from Cisco switches
2. Extracts **Native VLAN** from CDP TLV Type 0x0A
3. Gets **VTP Management Domain** (indicates VLAN database)

**CDP Packet Structure:**
```
Ethernet Frame
├── Destination: 01:00:0c:cc:cc:cc (CDP multicast)
├── Type: 0x2000 (CDP)
└── TLVs:
    ├── Type 0x0001: Device ID
    ├── Type 0x0003: Port ID
    ├── Type 0x000A: Native VLAN ← UNTAGGED VLAN
    ├── Type 0x0009: VTP Management Domain
    └── Type 0x0000: End
```

**Advantage:**
- ✅ Gets native VLAN reliably
- ✅ Cisco-specific but widely used
- ✅ Passive listening

---

### **Method 3: DHCP Probing** ⭐ ACTIVE DETECTION
**What Fluke Does:**
1. Sends DHCP Discover on each VLAN (1-4094)
2. Waits for DHCP Offer
3. If offer received → VLAN exists and has DHCP

**Our Implementation:**
- ✅ Already implemented!
- ✅ Works perfectly for DHCP-enabled VLANs

---

### **Method 4: IEEE 802.1Q Tag Analysis** ⚠️ TRUNK PORT ONLY
**What Fluke Does:**
1. **Requires trunk port connection**
2. Listens for 802.1Q tagged frames
3. Counts unique VLAN IDs seen in tags
4. After 60 seconds, reports all VLANs with traffic

**Our Implementation:**
- ✅ Already implemented (passive listening)!
- ⚠️ Only works on trunk ports
- ⚠️ Requires active traffic on VLAN

---

### **Method 5: IEEE 802.3ad (LACP) - Optional**
**What Fluke Does:**
- Detects if port is part of link aggregation
- LACP frames sometimes contain VLAN info

**Usefulness:** Low (not for VLAN discovery)

---

## What Fluke Does NOT Do

❌ **ARP Flooding** - Too disruptive
❌ **Random Layer-2 Probes** - Can confuse switches
❌ **Ping Sweeps** - Layer-3, not Layer-2
❌ **Gratuitous ARP** - Can trigger security alerts

---

## Fluke's Actual VLAN Detection Strategy

### **Phase 1: Passive Discovery (30-60 seconds)**
1. Listen for **LLDP** packets → Extract Port VLAN ID + VLAN Names
2. Listen for **CDP** packets → Extract Native VLAN
3. Listen for **tagged traffic** → Count unique VLAN IDs

**Result:** List of VLANs on trunk port

### **Phase 2: Active Verification (Optional)**
1. Send **DHCP Discover** on detected VLANs
2. Confirm VLAN has DHCP server
3. Get network configuration (IP, gateway, etc.)

**Result:** Network info for each VLAN

---

## Why Our Layer-2 Probing Failed

**The Issue:**
- Sending custom tagged frames → Switch may not respond
- Empty VLANs (no devices) → No responses
- Own packets reflected back → False positives

**Fluke's Solution:**
- **Don't send custom frames**
- **Only listen** for switch advertisements (LLDP/CDP)
- **Parse VLAN info** from existing protocols

---

## Recommended Implementation for Our Tool

### ✅ **Implement LLDP VLAN Extraction**

**This is the key missing piece!**

Fluke gets the complete VLAN list from LLDP **without sending a single probe packet**.

**Implementation Plan:**

#### **1. Enhance `lldp_cdp_discovery.py`**

Add VLAN extraction from LLDP TLV Type 7:

```python
def _parse_lldp_packet(self, pkt):
    # ... existing code ...

    # NEW: Extract VLAN information
    vlans_detected = []

    # TLV Type 7: Port VLAN ID (Native VLAN)
    if tlv_type == 7:
        native_vlan = struct.unpack('!H', tlv_value)[0]
        result.native_vlan = native_vlan
        vlans_detected.append(native_vlan)

    # TLV Type 127: Organizationally Specific (IEEE 802.1)
    elif tlv_type == 127:
        # Check if it's IEEE 802.1 (OUI: 00-80-c2)
        if tlv_value[0:3] == b'\x00\x80\xc2':
            subtype = tlv_value[3]

            # Subtype 3: VLAN Name
            if subtype == 3:
                vlan_id = struct.unpack('!H', tlv_value[4:6])[0]
                vlan_name = tlv_value[6:].decode('utf-8', errors='ignore')
                vlans_detected.append((vlan_id, vlan_name))

            # Subtype 4: Protocol VLAN ID (PPVID)
            elif subtype == 4:
                vlan_id = struct.unpack('!H', tlv_value[4:6])[0]
                vlans_detected.append(vlan_id)

    return vlans_detected
```

#### **2. Create VLAN-Specific Callback**

```python
def vlan_discovery_callback(vlan_list):
    """Called when LLDP reports VLANs"""
    for vlan_id in vlan_list:
        result = VLANProbeResult(vlan_id)
        result.status = "Active"
        result.source = "LLDP"
        # Store and display
```

#### **3. Updated Scan Strategy**

```
PHASE 1: LLDP/CDP Listening (30 seconds)
  ├─ Extract native VLAN from LLDP TLV Type 7
  ├─ Extract VLAN names from LLDP TLV Type 127
  ├─ Extract native VLAN from CDP
  └─ Result: Authoritative VLAN list from switch

PHASE 2: DHCP Probing (10-15 seconds)
  ├─ Probe VLANs discovered in Phase 1
  ├─ Get network configuration (IP, gateway, etc.)
  └─ Result: Network info for each VLAN

PHASE 3: Passive Traffic Analysis (optional 60 seconds)
  ├─ Listen for additional VLAN-tagged traffic
  ├─ Catch VLANs not advertised by LLDP
  └─ Result: Complete VLAN list
```

---

## Benefits of LLDP-Based Detection

✅ **Authoritative** - Information comes from switch
✅ **Fast** - Results in 30 seconds (LLDP broadcast interval)
✅ **Safe** - Passive listening only, no probing
✅ **Comprehensive** - Gets ALL configured VLANs on trunk
✅ **No False Positives** - Switch tells us exactly what exists
✅ **VLAN Names** - Not just IDs, but descriptive names!
✅ **Works on Empty VLANs** - Doesn't require traffic or DHCP

---

## LLDP TLV Reference

| TLV Type | Name | Contains | Useful? |
|----------|------|----------|---------|
| 1 | Chassis ID | Switch MAC/Name | ✅ Already parsing |
| 2 | Port ID | Port number | ✅ Already parsing |
| 3 | TTL | Time to live | ❌ Not needed |
| 4 | Port Description | "GigabitEthernet1/0/24" | ✅ Already parsing |
| 5 | System Name | "SW-CORE-01" | ✅ Already parsing |
| 6 | System Description | Model/version | ✅ Already parsing |
| 7 | **Port VLAN ID** | **Native VLAN** | ⭐ **NEED THIS!** |
| 8 | Management Address | Switch IP | ✅ Already parsing |
| 127 | Org-Specific | **VLAN Names** | ⭐ **NEED THIS!** |

---

## Example LLDP VLAN Information

**Switch Configuration:**
```
interface GigabitEthernet1/0/24
 switchport mode trunk
 switchport trunk native vlan 1
 switchport trunk allowed vlan 1,10,11,12,300,400
```

**LLDP Advertisement Contains:**
```
TLV Type 7 (Port VLAN ID): 1 ← Native VLAN
TLV Type 127 (Org-Specific):
  - Subtype 3: VLAN 10 "Data VLAN"
  - Subtype 3: VLAN 11 "Voice VLAN"
  - Subtype 3: VLAN 12 "Guest VLAN"
  - Subtype 3: VLAN 300 "Management VLAN"
  - Subtype 3: VLAN 400 "Security VLAN"
```

**Result:** Complete VLAN list in one LLDP packet! ✅

---

## Implementation Timeline

### **High Priority:**
1. ✅ Parse LLDP TLV Type 7 (Native VLAN) - 30 minutes
2. ✅ Parse LLDP TLV Type 127 Subtype 3 (VLAN Names) - 45 minutes
3. ✅ Add VLAN callback to discovery - 15 minutes
4. ✅ Integrate with VLAN Detection UI - 30 minutes

**Total Time:** ~2 hours

**Result:** Professional-grade VLAN detection like Fluke devices!

---

## Testing Strategy

1. **Enable LLDP on switch:**
   ```
   lldp run
   interface GigabitEthernet1/0/24
    lldp transmit
   ```

2. **Run LLDP discovery for 30 seconds**

3. **Check if VLANs appear in discovery results**

4. **Compare with switch config:**
   ```
   show interfaces trunk
   show vlan brief
   ```

---

## Conclusion

**Fluke's secret:** They don't probe VLANs actively - they **extract VLAN information from LLDP/CDP advertisements**!

This is:
- ✅ More reliable than active probing
- ✅ Safer (no packets sent)
- ✅ Faster (30 seconds vs 60-90 seconds)
- ✅ More complete (gets ALL VLANs on trunk)
- ✅ Gets VLAN names (bonus!)

**Next Step:** Implement LLDP VLAN extraction!
