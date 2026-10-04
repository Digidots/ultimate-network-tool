"""
LLDP/CDP Discovery Module
Passively listens for LLDP and CDP frames to discover switch information
"""

import threading
import struct
from datetime import datetime
from typing import Callable, Optional, Dict
from logger import get_logger

try:
    from scapy.all import sniff, Ether, Raw
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class DiscoveryResult:
    """Container for discovery results"""

    def __init__(self, protocol: str):
        self.protocol = protocol  # "LLDP" or "CDP"
        self.timestamp = datetime.now()
        self.switch_name = ""
        self.port_id = ""
        self.model = ""
        self.version = ""  # Separate version field
        self.ip_address = ""  # Management IP address
        self.mac_address = ""  # Chassis MAC address
        self.vendor = ""
        self.capabilities = []
        self.raw_data = {}
        # VLAN information (NEW - Fluke-style detection)
        self.native_vlan = None  # TLV Type 7: Port VLAN ID
        self.vlans = []  # List of (vlan_id, vlan_name) tuples from TLV Type 127

    def __str__(self):
        return (f"[{self.protocol}] Switch: {self.switch_name}, "
                f"Port: {self.port_id}, Model: {self.model}")


class LLDPCDPDiscovery:
    """LLDP and CDP passive discovery"""

    # Protocol identifiers
    LLDP_ETHER_TYPE = 0x88CC
    CDP_SNAP = b'\xAA\xAA\x03\x00\x00\x0C\x20\x00'

    # LLDP TLV Types
    LLDP_TLV_CHASSIS_ID = 1
    LLDP_TLV_PORT_ID = 2
    LLDP_TLV_TTL = 3
    LLDP_TLV_SYSTEM_NAME = 5
    LLDP_TLV_SYSTEM_DESC = 6
    LLDP_TLV_PORT_VLAN_ID = 7  # NEW - Native VLAN (Fluke method!)
    LLDP_TLV_MANAGEMENT_ADDR = 8
    LLDP_TLV_ORG_SPECIFIC = 127  # NEW - VLAN Names (Fluke method!)

    # CDP TLV Types
    CDP_DEVICE_ID = 0x0001
    CDP_PORT_ID = 0x0003
    CDP_CAPABILITIES = 0x0004
    CDP_VERSION = 0x0005
    CDP_PLATFORM = 0x0006

    def __init__(self, interface: str):
        self.interface = interface
        self.logger = get_logger()
        self.running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable[[DiscoveryResult], None]] = None

    def start_discovery(self, callback: Callable[[DiscoveryResult], None]):
        """Start passive discovery"""
        if not SCAPY_AVAILABLE:
            self.logger.error("Scapy not available. Install: pip install scapy")
            return False

        if self.running:
            self.logger.warning("Discovery already running")
            return False

        self.callback = callback
        self.running = True

        self.logger.log_action("Start Discovery", f"Interface: {self.interface}")

        # Start capture thread
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )
        self.capture_thread.start()
        return True

    def stop_discovery(self):
        """Stop passive discovery"""
        self.logger.log_action("Stop Discovery", f"Interface: {self.interface}")
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)

    def _capture_loop(self):
        """Main capture loop"""
        try:
            # Filter for LLDP (ethertype 0x88CC) and CDP (LLC SNAP)
            # CDP uses destination MAC 01:00:0C:CC:CC:CC
            filter_expr = "ether proto 0x88cc or ether dst 01:00:0c:cc:cc:cc"

            self.logger.info(f"Starting packet capture on {self.interface}")

            sniff(
                iface=self.interface,
                filter=filter_expr,
                prn=self._process_packet,
                store=False,
                stop_filter=lambda x: not self.running
            )

        except PermissionError:
            self.logger.error("Permission denied. Run as Administrator to capture packets.")
        except Exception as e:
            self.logger.log_exception("capture_loop", e)
        finally:
            self.running = False

    def _process_packet(self, packet):
        """Process captured packet"""
        try:
            if Ether in packet:
                ether = packet[Ether]

                # Check for LLDP
                if ether.type == self.LLDP_ETHER_TYPE:
                    result = self._parse_lldp(packet)
                    if result and self.callback:
                        self.logger.log_network_event("LLDP Frame Received", str(result))
                        self.callback(result)

                # Check for CDP
                elif Raw in packet:
                    raw_data = bytes(packet[Raw])
                    if raw_data[:8] == self.CDP_SNAP:
                        result = self._parse_cdp(raw_data)
                        if result and self.callback:
                            self.logger.log_network_event("CDP Frame Received", str(result))
                            self.callback(result)

        except Exception as e:
            self.logger.log_exception("process_packet", e)

    def _parse_lldp(self, packet) -> Optional[DiscoveryResult]:
        """Parse LLDP frame"""
        try:
            result = DiscoveryResult("LLDP")

            if Raw in packet:
                data = bytes(packet[Raw])
                offset = 0

                while offset < len(data) - 2:
                    # Parse TLV
                    tlv_header = struct.unpack('!H', data[offset:offset+2])[0]
                    tlv_type = (tlv_header >> 9) & 0x7F
                    tlv_length = tlv_header & 0x01FF

                    offset += 2

                    if offset + tlv_length > len(data):
                        break

                    tlv_value = data[offset:offset+tlv_length]

                    # Parse specific TLVs
                    if tlv_type == self.LLDP_TLV_CHASSIS_ID and tlv_length > 1:
                        # First byte is subtype
                        # Subtypes: 1=chassis component, 2=interface alias, 3=port component,
                        #           4=MAC address, 5=network address, 6=interface name, 7=locally assigned
                        chassis_subtype = tlv_value[0]

                        # Subtype 4: MAC address (most common)
                        if chassis_subtype == 4 and tlv_length >= 7:  # MAC address (6 bytes + 1 subtype)
                            mac_bytes = tlv_value[1:7]
                            result.mac_address = ':'.join(f'{b:02x}' for b in mac_bytes)

                        # Subtype 5: Network address (some switches send MAC as network address)
                        elif chassis_subtype == 5 and tlv_length >= 8:
                            # Next byte is address family (1 = IPv4, 2 = IPv6, 6 = MAC)
                            addr_family = tlv_value[1]
                            if addr_family == 6 and tlv_length >= 8:  # MAC address in network format
                                mac_bytes = tlv_value[2:8]
                                result.mac_address = ':'.join(f'{b:02x}' for b in mac_bytes)

                        # Subtype 7: Locally assigned (text string, store as vendor)
                        elif chassis_subtype == 7:
                            result.vendor = tlv_value[1:].decode('utf-8', errors='ignore')

                        # Other subtypes: try to decode as text
                        else:
                            try:
                                result.vendor = tlv_value[1:].decode('utf-8', errors='ignore')
                            except:
                                pass  # Ignore if can't decode

                    elif tlv_type == self.LLDP_TLV_PORT_ID and tlv_length > 1:
                        result.port_id = tlv_value[1:].decode('utf-8', errors='ignore')

                    elif tlv_type == self.LLDP_TLV_SYSTEM_NAME:
                        result.switch_name = tlv_value.decode('utf-8', errors='ignore')

                    elif tlv_type == self.LLDP_TLV_SYSTEM_DESC:
                        # Parse system description - try to extract model and version
                        sys_desc = tlv_value.decode('utf-8', errors='ignore')
                        result.model, result.version = self._parse_system_description(sys_desc)

                    elif tlv_type == self.LLDP_TLV_MANAGEMENT_ADDR and tlv_length > 2:
                        # Parse Management Address TLV
                        result.ip_address = self._parse_management_address(tlv_value)

                    elif tlv_type == self.LLDP_TLV_PORT_VLAN_ID:
                        # TLV Type 7: Port VLAN ID (Native VLAN) - FLUKE METHOD!
                        if tlv_length >= 2 and len(tlv_value) >= 2:
                            result.native_vlan = struct.unpack('!H', tlv_value[:2])[0]
                            self.logger.info(f"LLDP: Native VLAN detected = {result.native_vlan}")

                    elif tlv_type == self.LLDP_TLV_ORG_SPECIFIC:
                        # TLV Type 127: Organizationally Specific - FLUKE METHOD!
                        # Format: OUI (3 bytes) + Subtype (1 byte) + Data
                        if tlv_length >= 4 and len(tlv_value) >= 4:
                            oui = tlv_value[0:3]

                            # Check if it's IEEE 802.1 (OUI: 00-80-c2)
                            if oui == b'\x00\x80\xc2' and tlv_length > 4:
                                subtype = tlv_value[3]

                                # Subtype 3: VLAN Name
                                if subtype == 3 and tlv_length >= 7 and len(tlv_value) >= 7:
                                    vlan_id = struct.unpack('!H', tlv_value[4:6])[0]
                                    vlan_name_len = tlv_value[6]
                                    if tlv_length >= 7 + vlan_name_len and len(tlv_value) >= 7 + vlan_name_len:
                                        vlan_name = tlv_value[7:7+vlan_name_len].decode('utf-8', errors='ignore')
                                        result.vlans.append((vlan_id, vlan_name))
                                        self.logger.info(f"LLDP: VLAN {vlan_id} = '{vlan_name}'")

                    elif tlv_type == 0:  # End of LLDPDU
                        break

                    offset += tlv_length

                return result if result.switch_name or result.port_id else None

        except Exception as e:
            self.logger.log_exception("parse_lldp", e)
            return None

    def _parse_cdp(self, data: bytes) -> Optional[DiscoveryResult]:
        """Parse CDP frame"""
        try:
            result = DiscoveryResult("CDP")

            # Skip LLC SNAP header (8 bytes), CDP version (1 byte), TTL (1 byte), checksum (2 bytes)
            offset = 12

            while offset < len(data) - 4:
                # Parse TLV
                tlv_type = struct.unpack('!H', data[offset:offset+2])[0]
                tlv_length = struct.unpack('!H', data[offset+2:offset+4])[0]

                if tlv_length < 4 or offset + tlv_length > len(data):
                    break

                tlv_value = data[offset+4:offset+tlv_length]

                # Parse specific TLVs
                if tlv_type == self.CDP_DEVICE_ID:
                    result.switch_name = tlv_value.decode('utf-8', errors='ignore')

                elif tlv_type == self.CDP_PORT_ID:
                    result.port_id = tlv_value.decode('utf-8', errors='ignore')

                elif tlv_type == self.CDP_PLATFORM:
                    result.model = tlv_value.decode('utf-8', errors='ignore')

                elif tlv_type == self.CDP_VERSION:
                    result.vendor = tlv_value.decode('utf-8', errors='ignore')[:50]  # Truncate

                offset += tlv_length

            return result if result.switch_name or result.port_id else None

        except Exception as e:
            self.logger.log_exception("parse_cdp", e)
            return None

    def _parse_management_address(self, tlv_value: bytes) -> str:
        """Parse LLDP Management Address TLV to extract IP address"""
        try:
            if len(tlv_value) < 2:
                return "N/A"

            # First byte: address string length (including subtype)
            addr_len = tlv_value[0]

            if len(tlv_value) < 1 + addr_len:
                return "N/A"

            # Second byte: address subtype (1 = IPv4, 2 = IPv6)
            addr_subtype = tlv_value[1]

            if addr_subtype == 1 and addr_len == 5:  # IPv4 (1 byte subtype + 4 bytes address)
                # Extract IPv4 address (bytes 2-5)
                ip_bytes = tlv_value[2:6]
                return f"{ip_bytes[0]}.{ip_bytes[1]}.{ip_bytes[2]}.{ip_bytes[3]}"

            elif addr_subtype == 2 and addr_len == 17:  # IPv6 (1 byte subtype + 16 bytes address)
                # Extract IPv6 address (bytes 2-17)
                ip_bytes = tlv_value[2:18]
                # Format as IPv6
                ipv6_parts = []
                for i in range(0, 16, 2):
                    part = (ip_bytes[i] << 8) | ip_bytes[i+1]
                    ipv6_parts.append(f"{part:x}")
                return ":".join(ipv6_parts)

            else:
                return "N/A"

        except Exception as e:
            self.logger.debug(f"Error parsing management address: {e}")
            return "N/A"

    def _parse_system_description(self, sys_desc: str) -> tuple:
        """
        Parse system description to extract model and version separately.
        Different vendors format this differently, so we do our best.

        Common formats:
        - Cisco: "Cisco IOS Software, [model] Software ([version])"
        - HP: "[model] [version]"
        - Generic: "[manufacturer] [model] [version]"

        Returns: (model, version) tuple
        """
        try:
            # Default: use first 50 chars as model, rest as version
            if len(sys_desc) <= 50:
                return (sys_desc.strip(), "")

            # Try to detect Cisco format
            if "Cisco IOS" in sys_desc:
                # Extract model from brackets
                import re
                model_match = re.search(r'Cisco IOS Software,\s*([^,\(]+)', sys_desc)
                version_match = re.search(r'\(([^\)]+)\)', sys_desc)

                model = model_match.group(1).strip() if model_match else sys_desc[:50]
                version = version_match.group(1) if version_match else ""

                return (model, version)

            # Try to detect version patterns (Version, Ver, v)
            import re
            version_match = re.search(r'(?:Version|Ver|v\.?)\s*([0-9\.]+[^\s]*)', sys_desc, re.IGNORECASE)

            if version_match:
                version_start = version_match.start()
                model = sys_desc[:version_start].strip()[:50]
                version = version_match.group(1)
                return (model, version)

            # Fallback: split at first number sequence that looks like a version
            parts = re.split(r'(\d+\.\d+)', sys_desc, 1)
            if len(parts) >= 3:
                model = parts[0].strip()[:50]
                version = parts[1] + parts[2].strip()
                return (model, version)

            # Last resort: first 50 chars as model
            return (sys_desc[:50].strip(), sys_desc[50:100].strip() if len(sys_desc) > 50 else "")

        except Exception as e:
            self.logger.debug(f"Error parsing system description: {e}")
            return (sys_desc[:50].strip() if sys_desc else "Unknown", "")
