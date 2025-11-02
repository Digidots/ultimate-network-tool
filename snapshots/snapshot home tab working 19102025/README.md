# Ultimate Network Tool (UNT)

A modular portable Windows networking tool for Windows 10/11 with LLDP/CDP discovery and VLAN probing capabilities.

## Features

- **Admin Detection**: Visual indicator showing current privilege status (green/red)
- **Network Adapter Management**: Select and view detailed adapter information (IP, subnet, MAC, gateway, DNS, DHCP)
- **LLDP/CDP Discovery**: Passively listen for switch discovery frames to identify connected switches and ports
- **VLAN Probing**: Detect tagged VLANs on network ports with safe, rate-limited probing
- **Comprehensive Logging**: All actions, warnings, errors, and results are logged with timestamps
- **Expandable Design**: Modular architecture ready for adding future networking tools

## Requirements

- Windows 10 or Windows 11
- Python 3.8 or higher
- Administrator privileges (for packet capture and sending)
- Npcap (Windows packet capture driver)

## Installation

1. **Install Npcap**
   - Download from: https://npcap.com/
   - Install with WinPcap compatibility mode enabled

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run as Administrator** (required for packet capture)
   ```bash
   python unt_gui.py
   ```

2. **Select Network Adapter**
   - Choose your network adapter from the dropdown (Ethernet is default)
   - View adapter details in the information panel

3. **Start Discovery**
   - Click "Start Discovery" to passively listen for LLDP/CDP frames
   - Switch information will appear in the results panel
   - Click again to stop

4. **Start VLAN Probe**
   - Set VLAN range (default 1-100, max 1-4094)
   - Click "Start VLAN Probe" to detect tagged VLANs
   - Results show discovered VLANs from both passive discovery and active probing
   - Click again to stop

## Project Structure

```
UNT/
├── unt_gui.py              # Main GUI application
├── logger.py               # Logging system
├── network_adapter.py      # Adapter management
├── lldp_cdp_discovery.py   # LLDP/CDP discovery module
├── vlan_probe.py           # VLAN probing module
├── requirements.txt        # Python dependencies
├── skills.md               # Technical skills documentation
├── development_log.md      # Development progress log
└── logs/                   # Application logs (created at runtime)
```

## Safety Features

- **Rate Limiting**: VLAN probes are rate-limited (50ms delay between probes)
- **Timeouts**: Each probe has a 200ms timeout
- **Graceful Error Handling**: All exceptions are caught and logged
- **Non-intrusive Probing**: Uses lightweight 802.1Q tagged frames

## Logging

All operations are logged to timestamped files in the `logs/` directory:
- User actions
- Network events (LLDP/CDP captures, VLAN probes)
- Errors and warnings
- Results with confidence levels

## Future Expansion

The modular architecture allows easy addition of:
- Port scanning modules
- Bandwidth testing
- Network diagnostics
- Protocol analyzers
- Additional discovery protocols

## Copyright

Copyright Digidots 2025

## Troubleshooting

**"Permission denied" errors**
- Run as Administrator
- Ensure Npcap is installed

**"Scapy not available"**
- Install scapy: `pip install scapy`

**No adapters found**
- Check network adapter is enabled
- Run `ipconfig /all` to verify adapters

**Discovery not working**
- Ensure switch supports LLDP or CDP
- Verify admin privileges
- Check that Npcap is installed correctly
