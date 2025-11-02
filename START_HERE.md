# 🚀 Ultimate Network Tool - Quick Start Guide

## Active DHCP-Based VLAN Probing (ExtremeCloudIQ Style)

This tool uses **active DHCP Discovery probing** to detect VLANs on your network port, similar to ExtremeCloudIQ VLAN Probing.

---

## 🎯 How to Start the Application

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Run as Administrator

**IMPORTANT: You MUST run as Administrator for packet capture!**

```bash
# Open Command Prompt as Administrator, then:
python app.py
```

### Step 3: Open Web Interface

Navigate to: **http://localhost:5000**

---

## ✨ Key Features

### 🔍 ACTIVE VLAN Probing (NEW!)
- **Technology:** DHCP Discover packets (Layer 2 broadcast with 802.1Q VLAN tags)
- **Protocol Stack:** Ethernet (802.1Q) → IP → UDP → BOOTP → DHCP
- **Simultaneous Probing:** Up to 12 VLANs at once
- **Timeout:** 5 seconds per batch
- **Non-Disruptive:** Does NOT consume DHCP leases (sends Discover, receives Offer, stops)

### 📊 Information Captured Per VLAN:
- ✅ VLAN ID
- ✅ IP Range (network/CIDR)
- ✅ Subnet Mask
- ✅ Default Gateway
- ✅ DHCP Server IP

### 🎛️ Two Scanning Modes:
1. **Range Mode:** Scan VLAN 1-100, 1-4094, etc.
2. **Specific VLANs:** Scan exact VLANs (e.g., `1,10,20,300` or `1-10,50,100,300`)

---

## 🔧 How VLAN Probing Works

### Technical Details
```
1. Tool sends DHCP Discover on VLAN X:
   Ether(dst=broadcast) / Dot1Q(vlan=X) / IP / UDP / BOOTP / DHCP(discover)

2. If VLAN is allowed on port and has DHCP:
   DHCP Server responds with DHCP Offer containing:
   - Offered IP address
   - Subnet mask
   - Gateway (router option)
   - DHCP server ID

3. Tool captures response and displays network configuration
4. Tool does NOT request IP (no DHCP handshake completion)
```

###Why This Works:
- **Managed switches** allow tagged VLANs configured on the trunk port
- **DHCP servers** respond to Discover even without completing the handshake
- **Non-disruptive** - no IP assignment, no network interference
- **Fast** - probes 12 VLANs simultaneously every 5 seconds

---

## 📋 Example Usage

### Scenario: Detect VLAN 300

1. Open web interface: `http://localhost:5000`
2. Select your network adapter
3. Click "Specific VLANs" mode
4. Enter: `1,300`
5. Click "▶ Scan"

**Result:**
```
VLAN 1
  IP Range: 192.168.1.0/24
  Subnet: 255.255.255.0
  Gateway: 192.168.1.1
  DHCP Server: 192.168.1.1

VLAN 300
  IP Range: 10.30.0.0/16
  Subnet: 255.255.0.0
  Gateway: 10.30.0.1
  DHCP Server: 10.30.0.10
```

---

## 🆚 Active vs Passive Probing

| Feature | Passive (Old) | **Active DHCP (New)** |
|---------|--------------|----------------------|
| Method | Listen for existing traffic | Send DHCP Discover packets |
| Requires traffic | ✅ Yes | ❌ No |
| Detects idle VLANs | ❌ No | ✅ Yes |
| Network info | ❌ No | ✅ IP, Gateway, Subnet, DHCP |
| Speed | Slow (wait for traffic) | ✅ Fast (5 sec/batch) |
| Simultaneous | N/A | ✅ 12 VLANs at once |
| VLAN 300 detection | ❌ Only if traffic exists | ✅ Always (if configured) |

---

## 🎨 Other Features

### Switch Discovery (LLDP/CDP)
- Passive listening for switch advertisements
- Displays: Switch Name, Port, Model, Management IP

### IP Refresh
- Release and renew DHCP lease (requires admin)
- `ipconfig /release && ipconfig /renew`

### Start All Tests
- Runs both LLDP/CDP discovery AND VLAN probing together
- Auto-stops after 15 seconds

---

## 🐛 Troubleshooting

### "Permission denied"
- **Fix:** Run Command Prompt as Administrator

### "Scapy not available"
- **Fix:** `pip install scapy`

### No VLANs detected
- **Check:** Is DHCP server running on the VLAN?
- **Check:** Is VLAN configured on switch trunk port?
- **Check:** Firewall blocking DHCP (UDP port 67/68)?

### VLAN shows "N/A" for IP info
- VLAN exists but no DHCP server responded
- Switch allows VLAN but no DHCP configured

---

## 📂 Project Files

```
UNT/
├── app.py                    # ← RUN THIS (Flask web server)
├── vlan_probe.py             # DHCP-based VLAN probing engine
├── lldp_cdp_discovery.py     # Switch discovery
├── network_adapter.py        # Adapter enumeration
├── logger.py                 # Logging system
├── templates/
│   └── index.html            # Web UI
├── requirements.txt          # Python dependencies
└── START_HERE.md             # This file
```

---

## 🎯 Command Summary

```bash
# Install
pip install -r requirements.txt

# Run (as Administrator!)
python app.py

# Access
http://localhost:5000
```

---

## 🔒 Security Notes

- Runs on localhost:5000 by default
- Requires Administrator privileges for raw packet capture
- Does NOT assign IPs (safe, non-disruptive)
- Only run on trusted networks

---

**Copyright © Digidots 2025**
**Powered by ExtremeCloudIQ VLAN Probing methodology**
