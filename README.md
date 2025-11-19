# Ultimate Network Tool (UNT)

**Version 3.1.0**

A comprehensive network diagnostics tool with web-based interface for Windows 10/11, featuring active DHCP-based VLAN probing, LLDP/CDP discovery, and more.

## Features

- **Active VLAN Probing**: DHCP-based discovery (ExtremeCloudIQ style) - detects VLANs with full network info
- **Switch Discovery**: LLDP/CDP passive listening for switch identification
- **Network Adapter Management**: View detailed adapter information (IP, subnet, MAC, gateway, DNS, DHCP)
- **Web Interface**: Modern Flask-based web UI accessible via browser
- **Electron Desktop App**: Packaged as a native desktop application
- **Comprehensive Logging**: All actions, warnings, errors, and results are logged with timestamps
- **Modular Architecture**: Expandable design for future networking tools

## Requirements

- Windows 10 or Windows 11 (or Linux for development)
- Python 3.8 or higher
- Administrator/root privileges (for packet capture)
- Npcap (Windows) or appropriate packet capture libraries (Linux)

## Installation

1. **Install Npcap** (Windows only)
   - Download from: https://npcap.com/
   - Install with WinPcap compatibility mode enabled

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run as Administrator** (required for packet capture)
   ```bash
   python app.py
   ```

2. **Access the web interface**
   - Open your browser to: http://localhost:5000

3. **Use the Tool**
   - Select your network adapter from the dropdown
   - Start LLDP/CDP discovery to find connected switches
   - Run VLAN probing to detect available VLANs with network information
   - Use specific VLAN mode to test particular VLANs (e.g., 1,10,300)

## Project Structure

```
UNT/
├── app.py                  # Main Flask web server (RUN THIS)
├── logger.py               # Logging system
├── network_adapter.py      # Adapter management
├── lldp_cdp_discovery.py   # LLDP/CDP discovery module
├── vlan_probe.py           # Active DHCP-based VLAN probing
├── mtu_cli.py              # MTU testing CLI utility
├── list_routes.py          # Route listing utility
├── modules/
│   ├── ping_monitor.py     # Ping monitoring module
│   └── mtu_tester/         # MTU testing modules
├── templates/
│   └── index.html          # Web UI
├── requirements.txt        # Python dependencies
├── package.json            # Electron packaging config
├── app.spec                # PyInstaller spec
├── START_HERE.md           # Quick start guide
├── DEPLOYMENT.md           # Deployment instructions
└── logs/                   # Application logs (created at runtime)
```

## Archived Files

Old GUI versions and duplicate files have been moved to:
- `archive/old-gui-versions/` - Previous Tkinter GUI applications
- `archive/old-backups/` - Backup files
- `archive/old-module-duplicates/` - Duplicate module files

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
