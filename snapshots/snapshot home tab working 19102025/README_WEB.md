# Ultimate Network Tool - Web Version

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run as Administrator

```bash
# IMPORTANT: Run Command Prompt as Administrator
python app.py
```

### 3. Open Browser

Navigate to: **http://localhost:5000**

---

## ✨ Features

### Modern Web Interface
- **Glassmorphism Design** - Dark gradient with beautiful card-based layout
- **Real-Time Updates** - WebSocket integration for live data streaming
- **Responsive Grid** - Perfectly aligned cards and information displays
- **Small Notifications** - Subtle in-app notifications (no popups)

### Network Adapter Information
Displayed in a clean 2x3 grid:
- IP Address
- Subnet Mask
- Gateway
- DNS Server
- DHCP Server
- MAC Address

### Switch Discovery (LLDP/CDP)
- **Passive Listening** - No active probing, only listens for switch advertisements
- **Protocol Badges** - LLDP (blue) and CDP (orange) color-coded
- **Separate Cards** - Each discovered switch in its own modern card
- **Complete Info:**
  - Switch Name
  - Port Number
  - Switch Model
  - Switch IP Address (from Management TLV)

### VLAN Detection
- **Native/Untagged VLAN** - Large prominent display (green card)
- **Tagged VLANs** - Badge-style display with all discovered VLANs
- **Configurable Range** - Scan any VLAN range (1-4094)
- **Auto-Complete** - Scanning stops automatically when finished
- **Real-Time Updates** - VLANs appear as they're detected

---

## 🎨 Design Highlights

**Color Scheme:**
- Background: Dark gradient (#0f172a to #1e293b)
- Primary: Blue (#60a5fa)
- Success: Green (#10b981)
- Warning: Orange (#f59e0b)
- Error: Red (#ef4444)

**Modern Elements:**
- Card-based information display
- Color-coded protocol badges
- Clean button styles with hover effects
- Small, subtle notifications
- No visible scrollbars
- Professional glassmorphism aesthetic

---

## 🔧 Technical Details

### Architecture

```
Browser (HTML/CSS/JS) <--WebSocket--> Flask Server <--Scapy--> Network
```

### Backend (Python)
- **Flask** - Web server framework
- **Flask-SocketIO** - WebSocket support for real-time updates
- **Scapy** - Packet capture (same as desktop version)
- **Existing Modules:**
  - `logger.py` - Logging system
  - `network_adapter.py` - Adapter enumeration
  - `lldp_cdp_discovery.py` - LLDP/CDP parsing
  - `vlan_probe.py` - VLAN detection

### Frontend (Web)
- **HTML/CSS** - Modern glassmorphism design
- **JavaScript** - Socket.IO client for real-time communication
- **No Framework** - Pure vanilla JS for simplicity

### Protocol Details

**LLDP (Link Layer Discovery Protocol):**
- Ethertype: 0x88CC
- TLV Parsing:
  - System Name (type 5)
  - System Description (type 6) - parsed for model/version
  - Management Address (type 8) - IPv4/IPv6 extraction
  - Port ID (type 2)

**CDP (Cisco Discovery Protocol):**
- LLC SNAP frames
- Destination MAC: 01:00:0C:CC:CC:CC
- TLV Types: Device ID, Port ID, Platform, Version

**VLAN Detection:**
- Native VLAN: Listens for untagged traffic (filter: "not vlan")
- Tagged VLANs: Listens for 802.1Q frames (filter: "vlan {id}")

---

## 📊 System Requirements

- **OS:** Windows 10/11
- **Python:** 3.8 or higher
- **Privileges:** Administrator (for packet capture)
- **Driver:** Npcap installed
- **Network:** Active Ethernet connection

---

## 💡 Usage Tips

1. **Run as Administrator** - Required for raw packet capture
2. **Wait for Discovery** - LLDP/CDP may take 30-60 seconds (switches send periodic advertisements)
3. **VLAN Range** - Start with small ranges (1-100) for faster scans
4. **Network Activity** - More traffic = better VLAN detection results
5. **Browser Compatibility** - Works best in Chrome, Edge, Firefox

---

## 🐛 Troubleshooting

### "Permission denied" error
- Make sure you're running `python app.py` as Administrator
- Verify Npcap is installed

### No LLDP/CDP results
- Wait at least 30-60 seconds (switches advertise periodically)
- Ensure switch has LLDP/CDP enabled
- Check if connected to a managed switch

### VLAN scan finds nothing
- Ensure there's network traffic on the VLANs
- Try a larger VLAN range
- Native VLAN detection requires untagged traffic

### WebSocket disconnection
- Check if Flask server is still running
- Refresh the browser page
- Restart the Flask server

---

## 🆚 Web vs Desktop Version

| Feature | Desktop (tkinter) | Web Version |
|---------|-------------------|-------------|
| Interface | Python tkinter GUI | HTML/CSS/JS |
| Design | Limited styling | Full glassmorphism |
| Real-Time | Threading callbacks | WebSocket push |
| Accessibility | Local only | Network accessible |
| Packet Capture | Scapy | Scapy (same) |
| Admin Required | Yes | Yes |
| Performance | Native | Browser overhead |
| Updates | Manual refresh | Auto real-time |

---

## 📁 File Structure

```
UNT/
├── app.py                    # ← LAUNCH THIS (Web Server)
├── templates/
│   └── index.html            # Web frontend (HTML/CSS/JS)
├── logger.py                 # Logging system
├── network_adapter.py        # Adapter management
├── lldp_cdp_discovery.py     # LLDP/CDP parsing (with IP extraction)
├── vlan_probe.py             # VLAN detection
├── requirements.txt          # Python dependencies
├── README_WEB.md             # This file
└── development_log.md        # Development history
```

---

## 🔒 Security Notes

- Flask runs on localhost:5000 by default
- To access from other devices, change `host='0.0.0.0'` in app.py
- Only run on trusted networks
- Admin privileges required for packet capture

---

## 🎯 What's New in Web Version

### Fixed Issues:
1. **LLDP IP Address** - Now properly extracts from Management Address TLV (type 8)
2. **Model vs Version** - Separated into distinct fields with smart parsing
3. **Better Alignment** - CSS Grid ensures perfect card alignment
4. **Smaller Notifications** - Compact notification banners instead of large popups
5. **Smaller Cards** - Compact 2x3 grid for adapter information

### New Features:
1. **WebSocket Real-Time** - Live updates without polling
2. **Better UI/UX** - True modern web design
3. **Network Accessible** - Can be accessed from any device on network (if configured)
4. **Responsive Design** - Adapts to different screen sizes

---

**Copyright © Digidots 2025**
