# Ultimate Network Tool - Architecture

**Version:** 1.0.0
**Last Updated:** 2025-11-14

## Overview

Ultimate Network Tool (UNT) is a modular network diagnostics tool with web and desktop interfaces.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│              User Interface Layer                    │
│  ┌──────────────┐  ┌──────────────┐                │
│  │  Web UI      │  │  Electron    │                │
│  │  (Flask)     │  │  Desktop     │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────────┐
│           Application Server (Flask)                 │
│  ┌──────────────────────────────────────────┐      │
│  │  WebSocket Layer (SocketIO)               │      │
│  │  - Real-time event streaming              │      │
│  │  - Bidirectional communication            │      │
│  └──────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────────┐
│              Core Modules                            │
│  ┌──────────────┐  ┌──────────────┐                │
│  │  Discovery   │  │  MTU Tester  │                │
│  │  - LLDP/CDP  │  │  - Traceroute│                │
│  │  - VLAN      │  │  - Path MTU  │                │
│  └──────────────┘  └──────────────┘                │
│  ┌──────────────┐  ┌──────────────┐                │
│  │  Ping        │  │  Network     │                │
│  │  Monitor     │  │  Adapter Mgr │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘
                       │
┌─────────────────────────────────────────────────────┐
│           Network Layer (Scapy)                      │
│  - Raw packet capture and injection                 │
│  - 802.1Q VLAN tagging                              │
│  - ICMP/TCP/UDP packet crafting                     │
└─────────────────────────────────────────────────────┘
```

## Core Components

### 1. Application Server (`app.py`)
- **Framework:** Flask + Flask-SocketIO
- **Port:** 5000
- **Features:** REST API + WebSocket endpoints
- **Admin Check:** Windows privilege validation

### 2. Discovery Module (`modules/discovery/`)
- **LLDP/CDP Discovery** - Passive switch detection
- **VLAN Probing** - Active DHCP-based VLAN detection

### 3. MTU Tester (`modules/mtu_tester/`)
- **Traceroute** - Path discovery using TTL
- **MTU Testing** - Binary search for maximum MTU per hop

### 4. Ping Monitor (`modules/ping_monitor.py`)
- Continuous or one-time ping testing
- Statistics tracking (min/max/avg latency, packet loss)

### 5. Network Adapter Manager (`network_adapter.py`)
- Windows adapter enumeration
- IP/MAC/DNS/DHCP information extraction

## Data Flow

### VLAN Probing Example
```
1. User clicks "Start VLAN Probe" in UI
   ↓
2. WebSocket event: start_vlan_probe({start:1, end:100})
   ↓
3. Backend creates VLANProber instance
   ↓
4. For each VLAN (1-100):
   - Send DHCP Discover with 802.1Q tag
   - Capture DHCP Offer response
   - Extract network info (IP, subnet, gateway, DHCP server)
   ↓
5. Callback sends results via WebSocket: vlan_result event
   ↓
6. Frontend displays VLAN info in real-time
   ↓
7. Completion event: vlan_probe_complete
```

## File Structure

```
ultimate-network-tool/
├── app.py                          # Main Flask application
├── logger.py                       # Centralized logging
├── network_adapter.py              # Adapter management
├── lldp_cdp_discovery.py          # LLDP/CDP (legacy location)
├── vlan_probe.py                  # VLAN probing (legacy location)
│
├── modules/                        # Modular components
│   ├── discovery/                  # Discovery modules
│   │   ├── lldp_cdp_discovery.py  # Switch discovery
│   │   └── vlan_probe.py          # VLAN detection
│   ├── mtu_tester/                # MTU testing
│   │   ├── mtu_network.py         # MTU test engine
│   │   └── traceroute.py          # Path discovery
│   └── ping_monitor.py            # Ping monitoring
│
├── templates/                      # HTML templates
│   ├── index.html                 # Main dashboard
│   ├── ping.html                  # Ping monitor UI
│   └── mtu_simple_form.html       # MTU test form
│
├── electron/                       # Desktop wrapper
│   ├── main.js                    # Electron main process
│   └── preload.js                 # Preload scripts
│
└── docs/                          # Documentation
    ├── ARCHITECTURE.md            # This file
    ├── API.md                     # API reference
    ├── OPTIMIZATION.md            # Performance tips
    └── USER_GUIDE.md              # End-user guide
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Flask | Latest |
| Real-time | Flask-SocketIO | Latest |
| Packet Capture | Scapy | Latest |
| Desktop UI | Electron | 28.0.0 |
| Updater | electron-updater | 6.1.7 |
| Build | electron-builder | 24.9.1 |

## Security Considerations

1. **Admin Privileges Required**
   - Raw packet capture needs elevated permissions
   - Windows UAC prompt on startup

2. **Localhost Binding**
   - Default: `0.0.0.0:5000` (accessible on LAN)
   - Production: Bind to `127.0.0.1` only

3. **DHCP Safety**
   - VLAN probing sends DISCOVER only
   - Does NOT complete DHCP handshake
   - No IP lease consumption

4. **Rate Limiting**
   - VLAN probes: 12 simultaneous, 5s timeout
   - Prevents network flooding

## Extension Points

### Adding a New Module

1. Create module in `modules/your_module/`
2. Define result dataclass
3. Implement async or threaded execution
4. Add WebSocket event handlers in `app.py`
5. Create frontend UI in `templates/`
6. Update documentation

### Example: Adding a New Tool

```python
# modules/your_tool.py
from dataclasses import dataclass

@dataclass
class YourResult:
    status: str
    data: dict

class YourTool:
    def __init__(self, adapter_name: str):
        self.adapter = adapter_name
        self.running = False

    def start(self, callback):
        # Your implementation
        pass

    def stop(self):
        self.running = False
```

```python
# app.py
@socketio.on('start_your_tool')
def handle_start_your_tool(data):
    tool = YourTool(selected_adapter.description)
    def callback(result):
        socketio.emit('your_tool_result', result.__dict__)
    tool.start(callback)
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| LLDP/CDP Discovery | 15-60s | Passive listening, depends on switch advertisement interval |
| VLAN Probe (100 VLANs) | ~42s | 12 parallel probes, 5s timeout per batch |
| MTU Discovery | 5-30s | Depends on path length and hop count |
| Ping Monitor | Continuous | Real-time updates every interval |

## Logging

All operations logged to `logs/unt_YYYYMMDD.log`:
- User actions
- Network events
- Errors with stack traces
- Performance metrics

## Build & Deployment

See [DEPLOYMENT.md](../DEPLOYMENT.md) for:
- PyInstaller configuration
- Electron Builder settings
- Release process
- Auto-update configuration

---

**For API details, see [API.md](API.md)**
**For optimization guide, see [OPTIMIZATION.md](OPTIMIZATION.md)**
**For user guide, see [USER_GUIDE.md](USER_GUIDE.md)**
