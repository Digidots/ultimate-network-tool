# Ultimate Network Tool - Version History

## Current Version: 3.1.1

---

## Version 3.1.1 (2025-11-19)

### Ping Monitor Enhancements
- **Event Detection Fix** - Events now only track hosts that were initially reachable
  - Filters out always-unreachable hosts from event detection
  - More accurate percentage calculations based on reachable hosts
  - Prevents false positives from misconfigured IPs
- **Host Tagging System** - NEW feature to organize and categorize hosts
  - Tag hosts with custom labels (e.g., "Server", "Switch", "Workstation")
  - Click the edit icon (✎) in the Tag column to add/edit tags
  - Tags persist across sessions via localStorage
  - Tag badges displayed with purple styling
- **Correlation Analysis** - NEW feature showing which hosts fail together
  - Automatically detects co-failure patterns (hosts failing simultaneously)
  - Displayed in Statistics section below standard metrics
  - Helps identify shared infrastructure or network segments
  - Shows top 10 correlations with minimum 3 co-failures
- **GUI Performance Improvement** - Reduced update throttle from 500ms to 100ms
  - 5x faster UI updates (10 times per second vs 2 times per second)
  - More responsive real-time monitoring

### Technical Improvements
- Added `wasEverReachable` flag to host failure tracking
- Implemented `hostTags` Map with localStorage persistence
- Added `coFailureTracking` Map for correlation analysis
- Enhanced event detection with reachability filtering
- Optimized render throttle for better responsiveness

---

## Version 3.1.0 (2025-11-19)

### Ping Monitor Enhancements
- **Network Event Viewer** - NEW dedicated Events view in Ping Monitor
  - Automatically detects when 3+ hosts fail simultaneously for 3+ consecutive pings
  - Event classification: 🔴 Network Outages (50%+ hosts), 🟠 Partial Outages (20-49%), 🟡 Host Group Failures (3-19%)
  - Event timeline with timestamps and affected host lists
  - Filterable event view (All Events, Network Outages, Partial Outages, Group Failures)
  - Event statistics dashboard showing total events by type
- **Unlimited Ping History** - Removed 1000-ping limit, now stores complete history
- **Improved Results Display** - Compact table with smaller fonts and tighter spacing
  - Reduced font sizes (11px table, 9px headers)
  - Reduced padding (6px vs 8px)
  - Better readability with lots of hosts
- **Removed Heatmap View** - Replaced with Events view for better usability

### Technical Improvements
- Added `detectNetworkEvent()` function with intelligent failure tracking
- Tracks consecutive failures per host with `hostFailureTracking` Map
- Real-time event detection on each ping update
- Duplicate event prevention logic
- Events data structure includes type, timestamp, affected hosts, and percentages

---

## Version 3.0.0 (2025-11-19)

### UI/UX Improvements
- **Added version display** in GUI header - version now visible in title bar
- **Merged menu items** - Combined "Switch Discovery" and "VLAN Detection" into single "Network Discovery" menu item
  - Both features remain on the same page with full functionality
  - Simplified menu structure for better user experience
- **Fixed menu styling** - Prevented sidebar menu from overlapping hamburger icon
  - Added flexbox layout to sidebar
  - Fixed header area prevents content scroll-up
  - Menu content now properly contained and scrollable

### Technical Changes
- Restructured sidebar HTML with `.menu-container` wrapper for better scroll management
- Updated CSS for proper flexbox layout
- Maintained all existing functionality for VLAN and switch detection

---

## Version 2.0 - Flask Web Application (2025-11-02)

### Major Rewrite
- **Complete transition** from Tkinter GUI to Flask web application
- **Web interface** - Modern browser-based UI accessible at http://localhost:5000
- **Electron packaging** - Desktop app wrapper for Flask backend
- **Real-time updates** - WebSocket integration via Socket.IO

### Features from October 19, 2025
- **Fluke-Style LLDP VLAN Detection** - Extracts VLANs directly from LLDP advertisements
  - Native VLAN detection from TLV Type 7
  - VLAN names from TLV Type 127 (IEEE 802.1)
  - Authoritative information directly from switch
- **Enhanced DHCP Options** - Displays all 9 DHCP options with hover tooltips
  - Options: 1 (Subnet), 3 (Gateway), 6 (DNS), 15 (Domain), 28 (Broadcast)
  - Options: 43 (Vendor-Specific), 51 (Lease), 54 (DHCP Server), 60 (Vendor Class), 66 (TFTP)
- **Improved VLAN Detection Accuracy**
  - MIN_PACKETS = 5 (prevents false positives)
  - Hybrid active (DHCP) + passive (traffic listening) detection
- **Better Tooltips** - Detailed explanations with proper positioning

### Additional Features
- **Ping Monitor** - Network connectivity monitoring
- **MTU Backend** - MTU testing infrastructure (CLI available via `mtu_cli.py`)
- **Comprehensive Logging** - Detailed activity logs
- **Admin Detection** - Visual privilege status indicator

---

## Version 1.0 - Tkinter GUI (2025-10-18)

### Initial Release
- **Standalone Tkinter application** (`unt_final.py`)
- **Modern card-based UI** - Dark glassmorphism design
- **LLDP/CDP Discovery** - Passive switch detection
- **VLAN Probing** - Basic VLAN detection with passive listening
- **Network Adapter Selection** - Dropdown adapter management
- **IP Refresh** - DHCP release/renew functionality
- **Comprehensive Logging** - File-based logging system

---

## Version Numbering Scheme

**Format:** MAJOR.MINOR.PATCH

- **MAJOR** - Significant architectural changes (GUI framework change, complete rewrites)
- **MINOR** - New features, significant improvements
- **PATCH** - Bug fixes, small improvements

---

## Files by Version

### Version 3.0.0 (Current)
- `app.py` - Flask web server
- `templates/index.html` - Web UI
- All core modules remain unchanged

### Version 2.0 (Archived)
- Located in: `/snapshots/snapshot-20-10-2025/`

### Version 1.0 (Archived)
- `unt_final.py` - Archived in `/archive/old-gui-versions/`
- `unt.py` - Archived in `/archive/old-gui-versions/`
- `unt_gui_modern.py` - Archived in `/archive/old-gui-versions/`
- `unt_gui.py` - Archived in `/archive/old-gui-versions/`

---

**Copyright © Digidots 2025**
