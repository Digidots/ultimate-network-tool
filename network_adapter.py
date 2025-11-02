"""
Network Adapter Management Module
Handles adapter enumeration and information retrieval
"""

import socket
import subprocess
import re
from typing import List, Dict, Optional
from logger import get_logger


class AdapterInfo:
    """Container for network adapter information"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.mac_address = ""
        self.ip_address = ""
        self.subnet_mask = ""
        self.gateway = ""
        self.dns_servers = []
        self.dhcp_enabled = False
        self.dhcp_server = ""
        self.link_status = "Unknown"
        self.adapter_type = ""

    def __str__(self):
        return f"{self.description} ({self.name})"


class NetworkAdapterManager:
    """Manages network adapter operations"""

    def __init__(self):
        self.logger = get_logger()
        self.adapters: List[AdapterInfo] = []

    def enumerate_adapters(self) -> List[AdapterInfo]:
        """Enumerate all network adapters using ipconfig"""
        self.logger.log_action("Enumerate Adapters", "Starting adapter enumeration")
        self.adapters = []

        try:
            # Run ipconfig /all
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True,
                text=True,
                encoding='cp437',  # Windows console encoding
                timeout=10
            )

            if result.returncode != 0:
                self.logger.error(f"ipconfig failed: {result.stderr}")
                return []

            # Parse the output
            self._parse_ipconfig_output(result.stdout)
            self.logger.info(f"Found {len(self.adapters)} network adapters")

            return self.adapters

        except subprocess.TimeoutExpired:
            self.logger.error("ipconfig command timed out")
            return []
        except Exception as e:
            self.logger.log_exception("enumerate_adapters", e)
            return []

    def _parse_ipconfig_output(self, output: str):
        """Parse ipconfig /all output"""
        current_adapter = None
        lines = output.split('\n')

        for line in lines:
            line = line.rstrip()

            # Detect adapter header (not indented, ends with :)
            if line and not line[0].isspace() and line.endswith(':'):
                # Save previous adapter
                if current_adapter and self._is_valid_adapter(current_adapter):
                    self.adapters.append(current_adapter)

                # Start new adapter
                adapter_name = line[:-1].strip()
                current_adapter = AdapterInfo(adapter_name, adapter_name)

            elif current_adapter and line.strip():
                # Parse adapter properties
                self._parse_adapter_line(current_adapter, line)

        # Add last adapter
        if current_adapter and self._is_valid_adapter(current_adapter):
            self.adapters.append(current_adapter)

    def _parse_adapter_line(self, adapter: AdapterInfo, line: str):
        """Parse individual line of adapter info"""
        line = line.strip()

        # Description
        if "Description" in line:
            match = re.search(r'Description.*?:\s*(.+)', line)
            if match:
                adapter.description = match.group(1).strip()

        # Physical Address (MAC)
        elif "Physical Address" in line:
            match = re.search(r'Physical Address.*?:\s*(.+)', line)
            if match:
                adapter.mac_address = match.group(1).strip()

        # DHCP Enabled
        elif "DHCP Enabled" in line:
            adapter.dhcp_enabled = "Yes" in line

        # DHCP Server
        elif "DHCP Server" in line:
            match = re.search(r'DHCP Server.*?:\s*(.+)', line)
            if match:
                adapter.dhcp_server = match.group(1).strip()

        # IPv4 Address
        elif "IPv4 Address" in line:
            match = re.search(r'IPv4 Address.*?:\s*([0-9.]+)', line)
            if match:
                adapter.ip_address = match.group(1).strip()

        # Subnet Mask
        elif "Subnet Mask" in line:
            match = re.search(r'Subnet Mask.*?:\s*([0-9.]+)', line)
            if match:
                adapter.subnet_mask = match.group(1).strip()

        # Default Gateway
        elif "Default Gateway" in line:
            match = re.search(r'Default Gateway.*?:\s*(.+)', line)
            if match:
                gateway = match.group(1).strip()
                if gateway and gateway != "":
                    adapter.gateway = gateway

        # DNS Servers
        elif "DNS Servers" in line:
            match = re.search(r'DNS Servers.*?:\s*(.+)', line)
            if match:
                adapter.dns_servers = [match.group(1).strip()]
        elif line and adapter.dns_servers and re.match(r'^\s*[0-9a-fA-F.:]+\s*$', line):
            # Additional DNS server on next line
            adapter.dns_servers.append(line.strip())

        # Media State (for link status)
        elif "Media State" in line:
            if "disconnected" in line.lower():
                adapter.link_status = "Disconnected"
            else:
                adapter.link_status = "Connected"

    def _is_valid_adapter(self, adapter: AdapterInfo) -> bool:
        """Check if adapter has meaningful information"""
        # Must have at least a MAC address or IP address
        return bool(adapter.mac_address or adapter.ip_address)

    def get_adapter_by_description(self, description: str) -> Optional[AdapterInfo]:
        """Get adapter by description"""
        for adapter in self.adapters:
            if adapter.description == description:
                return adapter
        return None

    def get_ethernet_adapters(self) -> List[AdapterInfo]:
        """Get only Ethernet adapters (exclude WiFi, Bluetooth, virtual)"""
        ethernet = []
        exclude_keywords = ['wireless', 'wifi', 'wi-fi', 'bluetooth', 'virtual',
                           'vmware', 'virtualbox', 'hyper-v', 'loopback']

        for adapter in self.adapters:
            desc_lower = adapter.description.lower()
            if not any(keyword in desc_lower for keyword in exclude_keywords):
                if adapter.ip_address or adapter.mac_address:
                    ethernet.append(adapter)

        return ethernet

    def format_adapter_info(self, adapter: AdapterInfo) -> str:
        """Format adapter information for display"""
        info_lines = [
            f"Adapter: {adapter.description}",
            f"MAC Address: {adapter.mac_address or 'N/A'}",
            f"IP Address: {adapter.ip_address or 'N/A'}",
            f"Subnet Mask: {adapter.subnet_mask or 'N/A'}",
            f"Default Gateway: {adapter.gateway or 'N/A'}",
            f"DNS Servers: {', '.join(adapter.dns_servers) if adapter.dns_servers else 'N/A'}",
            f"DHCP Enabled: {'Yes' if adapter.dhcp_enabled else 'No'}",
            f"DHCP Server: {adapter.dhcp_server or 'N/A'}",
            f"Link Status: {adapter.link_status}"
        ]
        return '\n'.join(info_lines)
