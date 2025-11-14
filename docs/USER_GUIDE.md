# Ultimate Network Tool - User Guide

**Version:** 1.0.0

## Quick Start

### 1. Prerequisites

- **Windows 10/11**
- **Python 3.8+**
- **Npcap** - Download from https://npcap.com/
  - Install with WinPcap compatibility mode enabled
- **Administrator privileges** (required for packet capture)

### 2. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Application

#### Web Interface (Recommended)
```bash
# Run as Administrator
python app.py
```

Then open: **http://localhost:5000**

#### Electron Desktop App
```bash
npm install
npm start
```

---

## Features Overview

### 🔍 LLDP/CDP Discovery
Passively detect connected switches and ports.

**How to use:**
1. Select your network adapter
2. Click "Start Discovery"
3. Wait for switch advertisements (15-60 seconds)
4. View switch name, port, model, and IP

**Protocols detected:**
- LLDP (Link Layer Discovery Protocol)
- CDP (Cisco Discovery Protocol)

---

### 📡 VLAN Probing
Actively detect VLANs using DHCP discovery.

**How to use:**
1. Select adapter
2. Choose mode:
   - **Range Mode:** Scan VLAN 1-100, 1-4094, etc.
   - **Specific VLANs:** Enter comma-separated (e.g., `1,10,20,300`)
3. Click "Start VLAN Probe"
4. View results in real-time

**Information captured per VLAN:**
- ✅ VLAN ID
- ✅ IP Range (CIDR notation)
- ✅ Subnet Mask
- ✅ Default Gateway
- ✅ DHCP Server IP
- ✅ Lease time, domain name, broadcast address (if available)

**Technical details:**
- Sends DHCP Discover packets with 802.1Q VLAN tags
- Captures DHCP Offer responses
- **Safe:** Does NOT complete DHCP handshake (no IP lease consumed)
- **Fast:** Tests 12 VLANs simultaneously with 5-second timeout

---

### 🧪 MTU Discovery
Test Maximum Transmission Unit (MTU) for path to destination.

**How to use:**
1. Navigate to MTU Test page
2. Enter target (hostname or IP)
3. Select protocol (TCP/UDP/ICMP)
4. Click "Discover MTU"

**Results show:**
- Each hop in the path
- Maximum MTU supported
- Status: Optimal (≥1500), Reduced (<1500), or Unreachable
- RTT (Round-Trip Time)

**Use cases:**
- Diagnose fragmentation issues
- Verify jumbo frames
- Troubleshoot VPN MTU problems

---

### 📶 Ping Monitor
Monitor availability and latency for multiple hosts.

**How to use:**
1. Navigate to Ping Monitor
2. Enter targets (supports ranges):
   - Single IP: `8.8.8.8`
   - Hostname: `google.com`
   - Range: `192.168.1.1-192.168.1.10`
   - Mixed: `8.8.8.8, google.com, 192.168.1.1-10`
3. Configure:
   - Ping count (default: 4)
   - Timeout (default: 2 seconds)
   - Continuous mode (optional)
   - Interval (for continuous)
4. Click "Start Ping"

**Metrics displayed:**
- Status (Reachable/Unreachable)
- Average/Min/Max latency
- Packet loss percentage
- TTL (Time To Live)

---

### 🔄 IP Refresh
Quickly release and renew DHCP lease.

**How to use:**
1. Select adapter
2. Click "Refresh IP"
3. Wait for DHCP renewal

**Equivalent to:**
```cmd
ipconfig /release
ipconfig /renew
```

**Requires:** Administrator privileges

---

## Common Use Cases

### Detecting VLAN 300 on Your Port

**Scenario:** Your switch port has VLAN 300 configured, and you need to verify it.

**Steps:**
1. Open web interface: `http://localhost:5000`
2. Select your network adapter (e.g., Ethernet)
3. Click "Specific VLANs" mode
4. Enter: `1,300`
5. Click "▶ Scan"

**Expected result:**
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

### Identifying Connected Switch Port

**Scenario:** You need to know which switch and port you're connected to.

**Steps:**
1. Select your adapter
2. Click "Start Discovery"
3. Wait 15-60 seconds for switch advertisement
4. View results

**Expected result:**
```
Protocol: LLDP
Switch: switch-core-01
Port: Gi1/0/24
Model: Cisco Catalyst 2960
IP: 10.0.0.1
```

---

### Diagnosing MTU Issues

**Scenario:** Your VPN has slow performance, possibly due to MTU.

**Steps:**
1. Navigate to MTU Test
2. Enter VPN gateway IP or hostname
3. Click "Discover MTU"
4. Check each hop's MTU

**Example result:**
```
Hop 1: 192.168.1.1    MTU: 1500  ✅ Optimal
Hop 2: 10.0.0.1       MTU: 1500  ✅ Optimal
Hop 3: vpn.company    MTU: 1400  ⚠️ Reduced
```

**Solution:** Set your interface MTU to 1400 or less to avoid fragmentation.

---

### Monitoring Multiple Hosts

**Scenario:** Monitor uptime and latency for your network infrastructure.

**Steps:**
1. Navigate to Ping Monitor
2. Enter hosts:
   ```
   8.8.8.8, router.local, switch1, 192.168.10.1-192.168.10.10
   ```
3. Enable continuous mode
4. Set interval to 60 seconds
5. Click "Start Ping"

**Result:** Real-time dashboard showing status and latency for all hosts.

---

## Troubleshooting

### "Permission denied" or "Access is denied"

**Problem:** Not running as Administrator.

**Solution:**
1. Close the application
2. Right-click Command Prompt → "Run as Administrator"
3. Navigate to project folder
4. Run `python app.py`

---

### "Scapy not available"

**Problem:** Scapy library not installed.

**Solution:**
```bash
pip install scapy
```

---

### No VLANs detected

**Possible causes:**
1. **No DHCP server on VLAN**
   - VLAN exists but no DHCP configured
   - Tool cannot detect without DHCP response

2. **VLAN not allowed on switch port**
   - Contact network admin to configure VLAN on port

3. **Firewall blocking DHCP**
   - Check Windows Firewall settings
   - Allow UDP ports 67/68

4. **Not running as Administrator**
   - See "Permission denied" solution above

---

### Discovery not working

**Possible causes:**
1. **Switch doesn't support LLDP/CDP**
   - Check switch documentation
   - Some unmanaged switches don't support discovery protocols

2. **LLDP/CDP disabled on switch**
   - Contact network admin to enable

3. **Npcap not installed**
   - Download from https://npcap.com/
   - Install with WinPcap compatibility mode

4. **Wrong adapter selected**
   - Ensure you selected the correct Ethernet adapter
   - Try different adapters if multiple are available

---

### MTU test fails or shows "Unreachable"

**Possible causes:**
1. **Firewall blocking ICMP/TCP**
   - Some networks block ping/traceroute
   - Try different protocol (TCP instead of ICMP)

2. **Destination unreachable**
   - Verify host is online
   - Check network connectivity

3. **VPN or tunnel interference**
   - MTU discovery may not work through VPN
   - Test from outside VPN

---

### Web interface not loading

**Possible causes:**
1. **Port 5000 already in use**
   - Another application using port 5000
   - Kill other process or edit app.py to use different port

2. **Flask not installed**
   ```bash
   pip install flask flask-socketio
   ```

3. **Browser cache**
   - Hard refresh: Ctrl+Shift+R (Chrome/Firefox)
   - Clear browser cache

---

## Advanced Configuration

### Changing Web Server Port

Edit `app.py` line 537:
```python
socketio.run(app, host='0.0.0.0', port=5000, debug=False)
#                                      ^^^^
#                                Change this
```

### Adjusting VLAN Probe Performance

Edit `vlan_probe.py`:
```python
self.BATCH_SIZE = 12  # Number of simultaneous VLANs
self.TIMEOUT = 5      # Timeout in seconds
```

**Warning:** Increasing batch size may overwhelm DHCP servers.

### Changing Log Location

Edit `logger.py`:
```python
log_dir = 'logs'  # Change to your preferred directory
```

---

## Keyboard Shortcuts (Web UI)

| Key | Action |
|-----|--------|
| Ctrl+R | Refresh page |
| Esc | Stop current operation (where applicable) |

---

## Tips & Best Practices

### 1. Use Specific VLAN Mode
Instead of scanning 1-4094 (which takes 28+ minutes), scan specific VLANs:
```
1,10,20,30,40,50,100,200,300
```

### 2. Monitor Logs
Check `logs/` directory for detailed information and errors.

### 3. Test in Safe Environment
Before using in production, test on isolated network or lab.

### 4. Document Your Network
Export VLAN probe results to document your network topology.

### 5. Combine Features
Use Discovery + VLAN Probe together to get complete picture:
- Discovery shows switch/port
- VLAN Probe shows available VLANs

---

## FAQ

**Q: Does VLAN probing consume DHCP leases?**
A: No. The tool sends DHCP Discover and receives Offer, but does NOT complete the handshake (no Request/Ack). No IP is assigned.

**Q: Is VLAN probing safe for production networks?**
A: Yes, it's designed to be non-disruptive. However, always test in a lab first and comply with your organization's security policies.

**Q: Can I use this remotely?**
A: The web interface binds to `0.0.0.0`, making it accessible on your LAN. For security, consider changing to `127.0.0.1` (localhost only) in production.

**Q: Does this work on Linux/Mac?**
A: Currently designed for Windows. Linux/Mac support requires modifications to adapter enumeration and privilege checking.

**Q: What's the difference between active and passive VLAN detection?**
A: Passive listens for existing traffic (slow, unreliable). Active sends DHCP Discover packets (fast, reliable, detects idle VLANs).

---

## Getting Help

1. **Check logs:** `logs/unt_YYYYMMDD.log`
2. **Enable debug mode:** Edit `app.py` and set `debug=True`
3. **GitHub Issues:** Report bugs at repository issues page
4. **Documentation:** See other docs in `docs/` folder

---

## Next Steps

- [ARCHITECTURE.md](ARCHITECTURE.md) - Understand system design
- [API.md](API.md) - Integrate with other tools
- [OPTIMIZATION.md](OPTIMIZATION.md) - Performance tuning
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Build executable

---

**Copyright © Digidots 2025**
