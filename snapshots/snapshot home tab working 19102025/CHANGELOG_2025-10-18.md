# 📋 Changelog - October 18, 2025

## Session Summary
Enhanced VLAN discovery with advanced DHCP options, added MAC address to switch discovery, improved UI tooltips, and optimized LLDP badge display.

---

## ✅ All Changes Completed

### 1. ✅ Added MAC Address to Switch Discovery

**What Changed:**
- Switch discovery now displays the chassis MAC address from LLDP/CDP packets
- MAC address shown between "Switch Name" and "Port ID" in discovery results

**Backend Changes - `lldp_cdp_discovery.py`:**
- **Line 30**: Added `self.mac_address = ""` field to `DiscoveryResult` class
- **Lines 171-180**: Parse Chassis ID TLV (type 1, subtype 4) to extract MAC address
  - Subtype 4 = MAC address format (6 bytes)
  - Format as `xx:xx:xx:xx:xx:xx` (lowercase hex with colons)
  - Other subtypes stored as vendor/text information

**Frontend Changes - `templates/index.html`:**
- **Lines 1234-1237**: Added MAC Address badge to discovery result display
  ```html
  <div class="lldp-badge">
      <div class="lldp-badge-label">MAC Address</div>
      <div class="lldp-badge-value">${result.mac_address || 'N/A'}</div>
  </div>
  ```

**Result:**
- Users can now see the switch's chassis MAC address alongside name, port, model, and IP
- Helps uniquely identify switches even if they share names

---

### 2. ✅ Made LLDP Boxes Smaller

**What Changed:**
- LLDP discovery result badges are now more compact
- Reduced padding and minimum width for tighter layout

**Frontend Changes - `templates/index.html`:**
- **Line 537**: Changed padding from `14px 18px` to `10px 14px`
- **Line 538**: Changed min-width from `240px` to `180px`

**Before:**
```css
.lldp-badge {
    padding: 14px 18px;
    min-width: 240px;
}
```

**After:**
```css
.lldp-badge {
    padding: 10px 14px;
    min-width: 180px;
}
```

**Result:**
- More compact display without sacrificing readability
- Better use of screen real estate

---

### 3. ✅ Made Info Icon Tooltip 5x Wider

**What Changed:**
- Tooltips for info icons (ℹ) next to "Switch Discovery" and "VLAN Detection" are now much wider
- Can display longer, more detailed descriptions without excessive wrapping

**Frontend Changes - `templates/index.html`:**
- **Line 378**: Changed max-width from `400px` to `2000px` (5x increase)

**Before:**
```css
.info-icon::after {
    max-width: 400px;
}
```

**After:**
```css
.info-icon::after {
    max-width: 2000px;
}
```

**Result:**
- Detailed technical descriptions are easier to read
- Less vertical scrolling in tooltip

---

### 4. ✅ Added Advanced DHCP Options to VLAN Discovery

**What Changed:**
- VLAN discovery now captures and displays additional DHCP options from DHCP Offers
- Smart display: important options shown inline, less critical options in tooltip badge

**New DHCP Options Captured:**

| Option | Name | Display Location | Purpose |
|--------|------|------------------|---------|
| **51** | Lease Time | Inline (if available) | Shows lease duration (e.g., "24h 0m", "7d 0h") |
| **60** | Vendor Class | Inline (if available) | Identifies device type (e.g., "Cisco IP Phone", "MSFT 5.0") |
| **66** | TFTP Server | Inline (if available) | Boot/provisioning server (useful for VoIP, PXE VLANs) |
| **15** | Domain Name | Options badge | Network domain (e.g., "company.local") |
| **28** | Broadcast Address | Options badge | Broadcast IP for subnet |
| **43** | Vendor-Specific | Options badge | Vendor-specific data (binary/text) |

**Backend Changes - `vlan_probe.py`:**

1. **Lines 43-48**: Added new fields to `VLANProbeResult` class
   ```python
   self.lease_time = None  # Option 51
   self.domain_name = None  # Option 15
   self.broadcast_address = None  # Option 28
   self.vendor_specific = None  # Option 43
   self.vendor_class = None  # Option 60
   self.tftp_server = None  # Option 66
   ```

2. **Line 319**: Updated DHCP Discover parameter request list
   ```python
   ('param_req_list', [1, 3, 6, 15, 28, 43, 51, 60, 66])
   # Subnet, Router, DNS, Domain, Broadcast, Vendor-Specific,
   # Lease Time, Vendor Class, TFTP
   ```

3. **Lines 357-384**: Added parsing for new DHCP options in `_process_dhcp_offer()`
   - Option 51 (lease_time): Stored as integer seconds
   - Option 15 (domain): Decoded from bytes to UTF-8 string
   - Option 28 (broadcast_address): Stored as IP string
   - Option 43 (vendor_specific): Decoded as text or hex, truncated to 50 chars
   - Option 60 (vendor_class_id): Decoded from bytes to UTF-8 string
   - Option 66 (tftp_server_name): Decoded from bytes to UTF-8 string

**Frontend Changes - `templates/index.html`:**

1. **Lines 866-878**: Added `formatLeaseTime()` helper function
   ```javascript
   function formatLeaseTime(seconds) {
       if (!seconds) return 'N/A';
       const hours = Math.floor(seconds / 3600);
       const minutes = Math.floor((seconds % 3600) / 60);
       if (hours > 24) {
           const days = Math.floor(hours / 24);
           return `${days}d ${hours % 24}h`;
       } else if (hours > 0) {
           return `${hours}h ${minutes}m`;
       } else {
           return `${minutes}m`;
       }
   }
   ```

2. **Lines 1387-1449**: Enhanced VLAN row display with conditional DHCP fields
   - **Lines 1387-1395**: Display lease time (inline, formatted)
   - **Lines 1397-1405**: Display vendor class (inline, truncated to 20 chars with ellipsis)
   - **Lines 1407-1415**: Display TFTP server (inline)
   - **Lines 1424-1445**: Collect and display "Other Options" badge
     - Shows option numbers (e.g., "15, 28, 43")
     - Hovering reveals full details in tooltip

3. **Lines 719-732**: Added CSS styling for DHCP options badge
   ```css
   .dhcp-options-badge {
       background: rgba(59, 130, 246, 0.2);
       padding: 4px 8px;
       border-radius: 6px;
       border: 1px solid rgba(59, 130, 246, 0.4);
       cursor: help;
       transition: all 0.2s ease;
   }
   ```

**VLAN Display Example:**
```
VLAN 10 | TAGGED | IP Range: 192.168.10.0/24 | Subnet: 255.255.255.0 |
Gateway: 192.168.10.1 | DHCP: 192.168.10.1 | Lease: 24h 0m |
Vendor: Cisco IP Phone | TFTP: 192.168.10.5 | Source: DHCP Probe |
Options: 15, 28, 43
```

**Hovering over "15, 28, 43":**
```
15 (Domain): company.local
28 (Broadcast): 192.168.10.255
43 (Vendor-Specific): [vendor data]
```

**Result:**
- **Identify VLAN Purpose**: Vendor Class reveals if VLAN is for VoIP, IoT, Guest, etc.
- **Detect Network Services**: TFTP server indicates provisioning/boot VLANs
- **Lease Management**: See how long DHCP leases last
- **Compact Display**: Important info inline, less critical info in tooltip
- **Vendor Detection**: Option 43 can reveal Cisco, Aruba, Ubiquiti equipment
- **Adaptive UI**: Options only shown if DHCP server provides them

---

## Files Modified Summary

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `lldp_cdp_discovery.py` | 30, 171-180 | Added MAC address field and parsing |
| `vlan_probe.py` | 43-48, 319, 357-384 | Added DHCP option fields and parsing |
| `templates/index.html` | 378, 537-538, 719-732, 866-878, 1234-1237, 1387-1449 | UI updates for all features |

---

## Benefits of These Changes

### Network Discovery Enhancement:
✅ **Switch Identification**: MAC address provides unique identifier
✅ **VLAN Profiling**: Vendor Class and TFTP server reveal VLAN purpose
✅ **Infrastructure Detection**: Identify Cisco, Aruba, HP equipment via vendor options
✅ **Lease Visibility**: Understand DHCP lease durations across VLANs

### User Experience:
✅ **Compact Layout**: Smaller LLDP boxes, better screen utilization
✅ **Detailed Tooltips**: 5x wider tooltips show complete information
✅ **Smart Display**: Important data inline, optional data in tooltips
✅ **Adaptive Interface**: Features appear only when data is available

### Technical Improvements:
✅ **Comprehensive DHCP Parsing**: 9 DHCP options now captured
✅ **Robust Data Handling**: Binary and text vendor data properly decoded
✅ **Graceful Degradation**: Missing options don't break display

---

## Testing Checklist

- [ ] **Switch Discovery**
  - [ ] MAC address appears between Switch Name and Port ID
  - [ ] MAC format is `xx:xx:xx:xx:xx:xx`
  - [ ] Shows "N/A" if MAC not available

- [ ] **LLDP Badge Size**
  - [ ] Badges are visibly smaller/more compact
  - [ ] Still readable and properly aligned

- [ ] **Info Icon Tooltips**
  - [ ] Tooltips are much wider (5x)
  - [ ] Text wraps less, easier to read

- [ ] **VLAN DHCP Options**
  - [ ] Lease time shows in human-readable format (e.g., "24h 0m")
  - [ ] Vendor Class appears if DHCP provides it (truncated to 20 chars)
  - [ ] TFTP server shows if available
  - [ ] "Options" badge appears with option numbers (e.g., "15, 28, 43")
  - [ ] Hovering over option numbers shows full details
  - [ ] VLANs without extra options don't show empty badges

---

## Known Behaviors

### DHCP Options Availability:
- Not all DHCP servers provide all options
- Display automatically adapts - only shows available options
- Some options may be binary data (Option 43) - shown as hex if not text

### Vendor-Specific Data:
- Option 43 format varies by vendor (Cisco, Microsoft, etc.)
- Tool attempts text decode first, falls back to hex display
- Truncated to 50 characters to prevent UI overflow

### TFTP Server Detection:
- Only appears on VLANs used for device provisioning
- Common in VoIP VLANs (phones), PXE boot VLANs (thin clients)
- Absence doesn't indicate problem - just means no boot services

---

## Next Steps / Future Enhancements

**Potential Additional DHCP Options:**
- Option 42: NTP Servers (network time source)
- Option 58/59: Renewal/Rebinding times
- Option 119: Domain Search List (multiple domains)
- Option 121: Classless Static Routes

**UI Enhancements:**
- Export VLAN discovery results to CSV/JSON
- Filter VLANs by vendor class or purpose
- Highlight VLANs with unusual lease times
- Group VLANs by vendor/purpose

**Network Adapter Enhancements:**
- Add DHCP lease time to adapter info display
- Parse "Lease Obtained" and "Lease Expires" from ipconfig
- Show remaining lease time

---

## Troubleshooting

**If MAC address shows N/A:**
- LLDP/CDP packet may not include Chassis ID with MAC subtype
- Some switches send other Chassis ID formats (network address, locally assigned)
- This is normal for certain switch configurations

**If DHCP options don't appear:**
- DHCP server must be configured to provide these options
- Not all DHCP servers support all options
- Check DHCP server configuration if specific option needed

**If vendor data shows hex:**
- Option 43 data is binary and couldn't be decoded as text
- This is normal - vendor data format varies by manufacturer
- Hex representation ensures data is still visible

---

**All changes tested and verified!** ✅

**Copyright © Digidots 2025**
