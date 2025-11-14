# Ultimate Network Tool (UNT)

**Version:** 1.0.0

A professional network diagnostics tool for Windows 10/11 with LLDP/CDP discovery, VLAN probing, MTU testing, and ping monitoring.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run as Administrator
python app.py

# 3. Open browser
http://localhost:5000
```

## ✨ Key Features

- **🔍 LLDP/CDP Discovery** - Identify connected switches and ports
- **📡 Active VLAN Probing** - Detect VLANs using DHCP discovery (ExtremeCloudIQ style)
- **🧪 MTU Path Testing** - Discover maximum MTU for each hop
- **📶 Ping Monitor** - Monitor availability and latency for multiple hosts
- **🔄 IP Refresh** - Quick DHCP release/renew
- **🖥️ Web + Desktop UI** - Modern web interface with optional Electron wrapper

## 📋 Requirements

- **Windows 10/11**
- **Python 3.8+**
- **Administrator privileges** (for packet capture)
- **Npcap** - Download from https://npcap.com/

## 📚 Documentation

**New to UNT?** → [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

| Document | Description |
|----------|-------------|
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Complete user guide with examples |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and architecture |
| [API.md](docs/API.md) | REST and WebSocket API reference |
| [OPTIMIZATION.md](docs/OPTIMIZATION.md) | Performance optimization guide |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Build and deployment instructions |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

## 🎯 Common Use Cases

### Detect VLAN 300 on Your Port
```
1. Open http://localhost:5000
2. Select adapter → Specific VLANs → Enter "1,300"
3. Click "Scan"
```

### Identify Connected Switch
```
1. Select adapter → Start Discovery
2. Wait 15-60 seconds
3. View switch name, port, model, IP
```

### Diagnose MTU Issues
```
1. Navigate to MTU Test
2. Enter target (e.g., vpn.company.com)
3. View MTU for each hop
```

**More examples in [docs/USER_GUIDE.md](docs/USER_GUIDE.md)**

## 🏗️ Project Structure

```
ultimate-network-tool/
├── app.py                    # Flask web server (run this!)
├── modules/                  # Core modules
│   ├── discovery/           # LLDP/CDP and VLAN probing
│   ├── mtu_tester/          # MTU discovery
│   └── ping_monitor.py      # Ping monitoring
├── templates/               # Web UI
├── electron/                # Desktop wrapper
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

## 🔒 Security & Safety

- **Non-disruptive VLAN probing** - Sends DHCP Discover only (no lease consumption)
- **Rate-limited** - 12 VLANs simultaneously, 5s timeout
- **Localhost by default** - Binds to `0.0.0.0:5000` (configurable)
- **Admin required** - For raw packet capture only

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Permission denied" | Run Command Prompt as Administrator |
| "Scapy not available" | `pip install scapy` |
| No VLANs detected | Ensure DHCP server exists on VLAN |
| Discovery not working | Check switch supports LLDP/CDP |

**Full troubleshooting guide:** [docs/USER_GUIDE.md#troubleshooting](docs/USER_GUIDE.md#troubleshooting)

## 🚢 Building for Distribution

```bash
# Build standalone executable
npm run build

# Output: release/Ultimate Network Tool Setup 1.0.0.exe
```

**See [DEPLOYMENT.md](DEPLOYMENT.md) for details**

## 📄 License

Copyright © Digidots 2025

## 🤝 Contributing

1. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) to understand the design
2. Check [docs/OPTIMIZATION.md](docs/OPTIMIZATION.md) for improvement opportunities
3. Follow existing code style
4. Test thoroughly before submitting

---

**Need help? Check [docs/USER_GUIDE.md](docs/USER_GUIDE.md) or create an issue!**
