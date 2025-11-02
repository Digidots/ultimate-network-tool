# Ultimate Network Tool - Changelog

## Version 2.0 - Final Modern Release (2025-10-18)

### 🎨 Complete GUI Redesign

**New Modern Interface:**
- Dark glassmorphism design inspired by professional network tools
- Single-tab layout with all features in one view
- Left column: Adapter Information + Switch Discovery (LLDP/CDP)
- Right column: VLAN Detection + Summary
- Dark gradient background (#0f172a to #1e293b)
- Modern card-based components with subtle shadows

**Visual Improvements:**
- Emoji icons for better user experience (🔍, 🔄, ▶, ■)
- Color-coded status indicators (green for admin/success, red for user/stop)
- Professional typography (Segoe UI headings, Consolas for data)
- Consistent spacing and modern button styles
- Glassmorphism effects on all cards

### ✨ New Features

**1. IP Refresh Button**
- Renew DHCP lease with single click
- Runs `ipconfig /release` and `ipconfig /renew`
- Automatically reloads adapter information
- Requires administrator privileges

**2. Styled LLDP/CDP Result Boxes**
- Individual cards for each discovery result
- Protocol badge (LLDP = blue, CDP = orange)
- Timestamp display for each discovery
- Structured information rows:
  - Switch name
  - Port ID
  - Model
  - Vendor information
- Color-coded values (green for detected items)

**3. Separate VLAN Display Boxes**
- **Native/Untagged VLAN:** Large prominent display box
- **Tagged VLANs:** Scrollable list of all additional VLANs
- Clear visual separation
- Real-time updates during scanning
- Summary card showing total VLAN count

### 🐛 Bug Fixes

**VLAN Probe Logic Fixed:**
- Changed from sending tagged packets to passive listening
- Now uses BPF filter to detect actual VLAN traffic
- More accurate VLAN detection
- Proper status reporting (Active, Inactive, Error)
- First detected VLAN automatically marked as Native/Untagged
- Subsequent VLANs marked as Tagged

### 📦 Files

**Launch File:** `unt_final.py` (recommended)

**Legacy Files:**
- `unt_gui.py` - Original simple GUI
- `unt_gui_modern.py` - Tabbed modern GUI

**Core Modules:**
- `logger.py` - Logging system
- `network_adapter.py` - Adapter management
- `lldp_cdp_discovery.py` - Switch discovery
- `vlan_probe.py` - VLAN detection (updated)

### 🚀 Quick Start

```bash
# Run as Administrator
python unt_final.py
```

### 💡 Key Improvements

1. **Better Space Utilization:** All features visible in one view
2. **Professional Appearance:** Matches modern network tool aesthetics
3. **Improved Usability:** Clear visual hierarchy and intuitive layout
4. **Enhanced Functionality:** IP refresh and better VLAN detection
5. **Better Results Display:** Styled boxes instead of plain text

---

## Version 1.0 - Initial Release (2025-10-18)

### Features
- LLDP/CDP passive discovery
- VLAN probing (basic)
- Network adapter selection
- Admin privilege detection
- Comprehensive logging
- Basic GUI with tabs

---

**Copyright © Digidots 2025**
