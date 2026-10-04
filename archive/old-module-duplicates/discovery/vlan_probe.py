"""
VLAN Probing Module
Detects tagged VLANs using HYBRID detection:
1. Native VLAN detection (untagged traffic)
2. ACTIVE DHCP Discovery probing
3. Passive traffic monitoring
Based on ExtremeCloudIQ VLAN Probing methodology
"""

import threading
import time
import struct
import random
from datetime import datetime
from typing import Callable, List, Set, Optional, Dict
from logger import get_logger

try:
    from scapy.all import (Ether, Dot1Q, IP, UDP, BOOTP, DHCP, ARP,
                          sendp, sniff, srp, conf, get_if_hwaddr)
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class VLANProbeResult:
    """Container for VLAN probe results with DHCP information"""

    def __init__(self, vlan_id: int):
        self.vlan_id = vlan_id
        self.timestamp = datetime.now()
        self.status = "Unknown"  # "Active", "Inactive", "Timeout"
        self.response_time_ms = 0
        self.source = "DHCP Probe"  # "DHCP Probe", "LLDP", "CDP", "Native/Untagged", "Passive Traffic"

        # LLDP/CDP information (NEW - Fluke-style!)
        self.vlan_name = None  # VLAN name from LLDP TLV Type 127

        # DHCP Offer information
        self.offered_ip = None
        self.subnet_mask = None
        self.gateway = None
        self.dhcp_server = None
        self.dns_servers = []
        self.ip_range = None  # Calculated from subnet

        # Additional DHCP options
        self.lease_time = None  # Option 51 - Lease duration in seconds
        self.domain_name = None  # Option 15 - Domain name
        self.broadcast_address = None  # Option 28 - Broadcast address
        self.vendor_specific = None  # Option 43 - Vendor-specific information
        self.vendor_class = None  # Option 60 - Vendor class identifier
        self.tftp_server = None  # Option 66 - TFTP server name

    def __str__(self):
        if self.offered_ip:
            return (f"VLAN {self.vlan_id}: {self.status} - IP: {self.offered_ip}, "
                   f"Gateway: {self.gateway}, Subnet: {self.subnet_mask}")
        return f"VLAN {self.vlan_id}: {self.status} ({self.response_time_ms:.1f}ms)"


class VLANProber:
    """VLAN detection and probing"""

    def __init__(self, interface: str):
        self.interface = interface
        self.logger = get_logger()
        self.running = False
        self.probe_thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable[[VLANProbeResult], None]] = None

        # Probing parameters (ExtremeCloudIQ style)
        self.vlan_range_start = 1
        self.vlan_range_end = 4094
        self.vlan_list: Optional[List[int]] = None  # Specific VLANs to probe
        self.probe_timeout_sec = 5  # Per-VLAN timeout (default 5 sec)
        self.max_retries = 2  # Retries per VLAN
        self.simultaneous_vlans = 12  # Probe up to 12 VLANs simultaneously
        self.discovered_vlans: Dict[int, VLANProbeResult] = {}  # Store full results

        # Get MAC address for DHCP probes
        try:
            self.src_mac = get_if_hwaddr(interface)
        except:
            self.src_mac = "00:00:00:00:00:00"

    def set_vlan_range(self, start: int, end: int):
        """Set VLAN range to probe"""
        self.vlan_range_start = max(1, min(start, 4094))
        self.vlan_range_end = max(1, min(end, 4094))
        self.vlan_list = None  # Clear specific list
        self.logger.info(f"VLAN range set: {self.vlan_range_start}-{self.vlan_range_end}")

    def set_vlan_list(self, vlan_list: List[int]):
        """Set specific VLANs to probe"""
        self.vlan_list = [v for v in vlan_list if 1 <= v <= 4094]
        self.logger.info(f"Specific VLANs set: {self.vlan_list}")

    def start_probe(self, callback: Callable[[VLANProbeResult], None],
                    passive_vlans: Optional[List[int]] = None):
        """Start VLAN probing"""
        if not SCAPY_AVAILABLE:
            self.logger.error("Scapy not available. Install: pip install scapy")
            return False

        if self.running:
            self.logger.warning("VLAN probe already running")
            return False

        self.callback = callback
        self.running = True
        self.discovered_vlans.clear()

        # Add passive VLAN discoveries
        if passive_vlans:
            for vlan_id in passive_vlans:
                result = VLANProbeResult(vlan_id)
                result.status = "Detected"
                result.source = "LLDP/CDP"
                self.discovered_vlans[vlan_id] = result  # Fixed: use dict assignment
                self.logger.log_network_event("VLAN from Discovery", f"VLAN {vlan_id}")
                if self.callback:
                    self.callback(result)

        self.logger.log_action("Start VLAN Probe",
                              f"Range: {self.vlan_range_start}-{self.vlan_range_end}")

        # Start probe thread
        self.probe_thread = threading.Thread(
            target=self._probe_loop,
            daemon=True
        )
        self.probe_thread.start()
        return True

    def stop_probe(self):
        """Stop VLAN probing"""
        self.logger.log_action("Stop VLAN Probe", f"Discovered: {len(self.discovered_vlans)} VLANs")
        self.running = False
        if self.probe_thread:
            self.probe_thread.join(timeout=2)

    def _probe_loop(self):
        """HYBRID probing: LLDP detection + Active DHCP probing + Passive listening"""
        try:
            # Disable Scapy verbosity
            conf.verb = 0

            # Determine VLANs to probe
            if self.vlan_list:
                vlans_to_probe = self.vlan_list
                self.logger.info(f"Hybrid VLAN probing: {len(vlans_to_probe)} specific VLANs")
            else:
                vlans_to_probe = list(range(self.vlan_range_start, self.vlan_range_end + 1))
                self.logger.info(f"Hybrid VLAN probing: range {self.vlan_range_start}-{self.vlan_range_end}")

            # PHASE 1: Check native VLAN (untagged)
            self.logger.info("PHASE 1: Probing native/untagged VLAN...")
            native_result = self._probe_native_vlan()
            if native_result and self.callback:
                self.callback(native_result)

            # Start passive listener in background
            self.logger.info("PHASE 2: Starting passive VLAN traffic listener...")
            passive_thread = threading.Thread(target=self._passive_listen_vlans, daemon=True)
            passive_thread.start()

            # Active DHCP probe
            self.logger.info(f"PHASE 3: Sending DHCP Discover to {len(vlans_to_probe)} VLANs...")
            self._active_probe_vlans(vlans_to_probe)

            # Wait for passive detection to complete (60 seconds + 2 second buffer)
            self.logger.info("Waiting for passive VLAN detection to complete (60 seconds)...")
            passive_thread.join(timeout=62)  # Wait for passive thread to finish

            self.logger.log_result("VLAN Probe Complete",
                                  f"Found {len([v for v, r in self.discovered_vlans.items() if r.status == 'Active'])} active VLANs")

        except PermissionError:
            self.logger.error("Permission denied. Run as Administrator to send packets.")
        except Exception as e:
            self.logger.log_exception("probe_loop", e)
        finally:
            self.running = False

    def _probe_native_vlan(self) -> Optional[VLANProbeResult]:
        """Detect native/untagged VLAN by listening for untagged traffic"""
        try:
            self.logger.info("Listening for untagged traffic (native VLAN)...")

            # Listen for any untagged Ethernet frames (no VLAN tag)
            # Filter: not vlan (captures frames without 802.1Q tag)
            packets = sniff(
                iface=self.interface,
                timeout=self.probe_timeout_sec,
                count=5,
                filter="not vlan",
                store=True
            )

            if len(packets) > 0:
                # Found untagged traffic - this is native VLAN (usually VLAN 1)
                result = VLANProbeResult(1)  # Native VLAN is typically VLAN 1
                result.status = "Active"
                result.source = "Native/Untagged"
                result.response_time_ms = 0
                self.discovered_vlans[1] = result  # Fixed: use dict assignment
                self.logger.log_network_event("Native VLAN Detected",
                                              f"VLAN 1 (untagged): {len(packets)} frames")
                return result
            else:
                self.logger.info("No untagged traffic detected")
                return None

        except Exception as e:
            self.logger.log_exception("probe_native_vlan", e)
            return None

    def _active_probe_vlans(self, vlan_list: List[int]):
        """ACTIVE VLAN probing using DHCP Discover (ExtremeCloudIQ methodology)"""
        try:
            total_vlans = len(vlan_list)
            self.logger.info(f"Sending DHCP Discover to {total_vlans} VLANs (batches of {self.simultaneous_vlans})...")

            # Start global DHCP response listener
            sniffer_running = threading.Event()
            sniffer_running.set()
            pending_xids: Dict[int, int] = {}  # xid -> vlan_id mapping

            def dhcp_response_handler(pkt):
                """Capture DHCP Offer responses"""
                try:
                    if BOOTP in pkt and DHCP in pkt:
                        # Check if it's a DHCP Offer
                        for opt in pkt[DHCP].options:
                            if opt[0] == 'message-type' and opt[1] == 2:  # DHCP Offer
                                xid = pkt[BOOTP].xid
                                if xid in pending_xids:
                                    vlan_id = pending_xids[xid]
                                    self._process_dhcp_offer(vlan_id, pkt)
                                break
                except Exception as e:
                    pass  # Ignore packet processing errors

            # Start sniffer thread
            def sniffer_thread():
                try:
                    sniff(
                        iface=self.interface,
                        filter="udp and port 68",  # DHCP client port
                        prn=dhcp_response_handler,
                        store=False,
                        stop_filter=lambda x: not sniffer_running.is_set()
                    )
                except:
                    pass

            sniffer = threading.Thread(target=sniffer_thread, daemon=True)
            sniffer.start()
            time.sleep(0.5)  # Let sniffer start

            # Probe VLANs in batches
            for i in range(0, total_vlans, self.simultaneous_vlans):
                if not self.running:
                    break

                batch = vlan_list[i:i + self.simultaneous_vlans]
                self.logger.info(f"Probing batch {i//self.simultaneous_vlans + 1}: VLANs {batch}")

                # Send DHCP Discover to batch
                batch_xids = {}
                for vlan_id in batch:
                    xid = random.randint(1, 0xFFFFFFFF)
                    batch_xids[xid] = vlan_id
                    pending_xids[xid] = vlan_id
                    self._send_dhcp_discover(vlan_id, xid)
                    time.sleep(0.05)  # Small delay between sends

                # Wait for responses
                time.sleep(self.probe_timeout_sec)

                # DON'T track timeout VLANs at all - they're not active and shouldn't be displayed
                # Only Active VLANs (from DHCP Offer or passive detection) are tracked

                # Clean up pending XIDs
                for xid in batch_xids:
                    pending_xids.pop(xid, None)

                self.logger.info(f"Batch complete: {len(self.discovered_vlans)} VLANs responded so far")

            # Stop sniffer
            sniffer_running.clear()
            time.sleep(0.5)

            # Report results
            active_vlans = [v for v, r in self.discovered_vlans.items() if r.status == "Active"]
            self.logger.info(f"DHCP probing complete: {len(active_vlans)}/{total_vlans} VLANs active")
            self.logger.info(f"Active VLANs: {sorted(active_vlans)}")

        except Exception as e:
            self.logger.log_exception("active_probe_vlans", e)

    def _layer2_probe_vlans(self, vlan_list: List[int]):
        """Layer-2 VLAN probing using 802.1Q tag injection
        Professional method used by Fluke devices
        Sends tagged frames and observes switch behavior
        """
        try:
            self.logger.info(f"Starting Layer-2 VLAN probing for {len(vlan_list)} VLANs...")

            for vlan_id in vlan_list:
                if not self.running:
                    break

                # Skip if already discovered via DHCP
                if vlan_id in self.discovered_vlans:
                    continue

                # Method 1: Send a tagged Ethernet frame to a multicast address
                # Use LLDP multicast address (01:80:c2:00:00:0e) - switches understand this
                # This is safe - it's a standard protocol address
                probe_frame = (
                    Ether(
                        dst="01:80:c2:00:00:0e",  # LLDP multicast (safe, understood by switches)
                        src=self.src_mac,
                        type=0x8100  # 802.1Q tag
                    ) /
                    Dot1Q(vlan=vlan_id) /
                    # Send a minimal payload (just enough to be valid)
                    b'\x00\x00'  # Null payload
                )

                # Send frame and listen for ANY tagged response on this VLAN
                # We're looking for:
                # 1. LLDP/CDP responses tagged with this VLAN
                # 2. Any frame echoed back with this VLAN tag
                # 3. Switch accepting the frame (not dropping it)

                # Set up a quick sniffer for this VLAN
                vlan_detected = False

                def response_handler(pkt):
                    nonlocal vlan_detected
                    # Check if we got ANY frame with our VLAN tag
                    # BUT ignore our own probe frame (filter by source MAC)
                    if Dot1Q in pkt and pkt[Dot1Q].vlan == vlan_id:
                        # Ignore if it's our own packet (same source MAC)
                        if pkt[Ether].src != self.src_mac:
                            vlan_detected = True
                            return True  # Stop sniffing

                # Start sniffer in background
                sniffer = threading.Thread(
                    target=lambda: sniff(
                        iface=self.interface,
                        filter=f"vlan {vlan_id}",
                        prn=response_handler,
                        timeout=1,
                        store=False
                    ),
                    daemon=True
                )
                sniffer.start()

                # Small delay to let sniffer start
                time.sleep(0.1)

                # Send the probe frame
                sendp(probe_frame, iface=self.interface, verbose=False)

                # Wait for sniffer to complete
                sniffer.join(timeout=1.2)

                # If we detected traffic on this VLAN, it exists
                if vlan_detected:
                    result = VLANProbeResult(vlan_id)
                    result.status = "Active"
                    result.source = "Layer-2 Probe"
                    self.discovered_vlans[vlan_id] = result

                    self.logger.log_network_event("VLAN Detected",
                                                  f"VLAN {vlan_id} (Layer-2: switch accepted tag)")

                    if self.callback:
                        self.callback(result)

            # Report Layer-2 results
            l2_vlans = [v for v, r in self.discovered_vlans.items() if r.source == "Layer-2 Probe"]
            self.logger.info(f"Layer-2 probing complete: {len(l2_vlans)} additional VLANs detected")
            if l2_vlans:
                self.logger.info(f"Layer-2 detected VLANs: {sorted(l2_vlans)}")

        except Exception as e:
            self.logger.log_exception("layer2_probe_vlans", e)

    def _send_dhcp_discover(self, vlan_id: int, xid: int):
        """Send DHCP Discover packet on specific VLAN"""
        try:
            # Craft VLAN-tagged DHCP Discover
            # Protocol: Ethernet → 802.1Q → IP → UDP → BOOTP → DHCP
            packet = (
                Ether(dst="ff:ff:ff:ff:ff:ff", src=self.src_mac) /
                Dot1Q(vlan=vlan_id) /
                IP(src="0.0.0.0", dst="255.255.255.255") /
                UDP(sport=68, dport=67) /
                BOOTP(
                    op=1,  # Request
                    chaddr=self.src_mac,
                    xid=xid
                ) /
                DHCP(options=[
                    ('message-type', 'discover'),
                    ('param_req_list', [1, 3, 6, 15, 28, 43, 51, 60, 66]),  # Subnet, Router, DNS, Domain, Broadcast, Vendor-Specific, Lease Time, Vendor Class, TFTP
                    'end'
                ])
            )

            # Send packet
            sendp(packet, iface=self.interface, verbose=False)

        except Exception as e:
            self.logger.debug(f"Error sending DHCP Discover to VLAN {vlan_id}: {e}")

    def _process_dhcp_offer(self, vlan_id: int, pkt):
        """Process DHCP Offer and extract network configuration"""
        try:
            # Check if we already have a result for this VLAN (e.g., native VLAN)
            if vlan_id in self.discovered_vlans:
                result = self.discovered_vlans[vlan_id]
                # Update source to indicate both native and DHCP
                if result.source == "Native/Untagged":
                    result.source = "Native/Untagged + DHCP"
                else:
                    result.source = "DHCP Probe"
            else:
                result = VLANProbeResult(vlan_id)
                result.status = "Active"
                result.source = "DHCP Probe"

            # Extract offered IP
            result.offered_ip = pkt[BOOTP].yiaddr

            # Extract DHCP server
            result.dhcp_server = pkt[BOOTP].siaddr

            # Parse DHCP options
            for opt in pkt[DHCP].options:
                if opt == 'end':
                    break
                if isinstance(opt, tuple) and len(opt) == 2:
                    opt_name, opt_value = opt
                    if opt_name == 'subnet_mask':
                        result.subnet_mask = opt_value
                    elif opt_name == 'router':
                        result.gateway = opt_value if isinstance(opt_value, str) else opt_value[0]
                    elif opt_name == 'name_server':
                        result.dns_servers = opt_value if isinstance(opt_value, list) else [opt_value]
                    elif opt_name == 'server_id':
                        result.dhcp_server = opt_value
                    elif opt_name == 'lease_time':
                        result.lease_time = opt_value  # In seconds
                    elif opt_name == 'domain':
                        result.domain_name = opt_value.decode('utf-8') if isinstance(opt_value, bytes) else opt_value
                    elif opt_name == 'broadcast_address':
                        result.broadcast_address = opt_value
                    elif opt_name == 'vendor_specific':
                        # Option 43 - Vendor-specific (can be binary or text)
                        if isinstance(opt_value, bytes):
                            # Try to decode as text, otherwise show hex
                            try:
                                result.vendor_specific = opt_value.decode('utf-8', errors='ignore').strip()
                            except:
                                result.vendor_specific = opt_value.hex()[:50]  # Truncate hex
                        else:
                            result.vendor_specific = str(opt_value)[:50]
                    elif opt_name == 'vendor_class_id':
                        # Option 60 - Vendor class identifier
                        if isinstance(opt_value, bytes):
                            result.vendor_class = opt_value.decode('utf-8', errors='ignore').strip()
                        else:
                            result.vendor_class = str(opt_value)
                    elif opt_name == 'tftp_server_name':
                        # Option 66 - TFTP server
                        if isinstance(opt_value, bytes):
                            result.tftp_server = opt_value.decode('utf-8', errors='ignore').strip()
                        else:
                            result.tftp_server = str(opt_value)

            # Calculate IP range from subnet
            if result.offered_ip and result.subnet_mask:
                result.ip_range = self._calculate_ip_range(result.offered_ip, result.subnet_mask)

            # Store result
            self.discovered_vlans[vlan_id] = result

            # Log and callback
            self.logger.log_network_event("VLAN Detected",
                                         f"VLAN {vlan_id}: IP={result.offered_ip}, "
                                         f"Gateway={result.gateway}, Subnet={result.subnet_mask}")

            if self.callback:
                self.callback(result)

        except Exception as e:
            self.logger.debug(f"Error processing DHCP Offer for VLAN {vlan_id}: {e}")

    def _calculate_ip_range(self, ip: str, subnet: str) -> str:
        """Calculate network range from IP and subnet mask"""
        try:
            import ipaddress
            network = ipaddress.IPv4Network(f"{ip}/{subnet}", strict=False)
            return f"{network.network_address}/{network.prefixlen}"
        except:
            return f"{ip}/{subnet}"

    def _passive_listen_vlans(self):
        """Passive listening for VLAN traffic (runs in background)
        Uses packet counting to filter out spurious VLANs
        """
        try:
            self.logger.info("Passive VLAN listener active (enhanced mode)...")
            vlan_packet_counts = {}  # Track packet count per VLAN
            vlan_first_seen = {}  # Track when VLAN was first seen
            MIN_PACKETS = 3  # Require at least 3 packets to confirm VLAN
            MIN_TIME_SPAN = 3  # Packets must be spread across at least 3 seconds

            def packet_handler(pkt):
                """Process packets for VLAN tags"""
                try:
                    if not self.running:
                        return True  # Stop sniffing

                    if Dot1Q in pkt:
                        vlan_id = pkt[Dot1Q].vlan

                        # Check if in range
                        if self.vlan_list:
                            in_range = vlan_id in self.vlan_list
                        else:
                            in_range = self.vlan_range_start <= vlan_id <= self.vlan_range_end

                        if in_range:
                            current_time = time.time()

                            # Track first time we see this VLAN
                            if vlan_id not in vlan_packet_counts:
                                vlan_packet_counts[vlan_id] = 0
                                vlan_first_seen[vlan_id] = current_time

                            vlan_packet_counts[vlan_id] += 1

                            # Only report VLAN if:
                            # 1. We've seen enough packets (MIN_PACKETS)
                            # 2. Packets are spread over time (MIN_TIME_SPAN seconds)
                            # 3. Not already discovered via DHCP
                            if vlan_id not in self.discovered_vlans:
                                time_span = current_time - vlan_first_seen[vlan_id]
                                packet_count = vlan_packet_counts[vlan_id]

                                if packet_count >= MIN_PACKETS and time_span >= MIN_TIME_SPAN:
                                    result = VLANProbeResult(vlan_id)
                                    result.status = "Active"
                                    result.source = "Passive Traffic"
                                    # Note: Passive VLANs won't have DHCP info (ip_range, subnet, etc.)
                                    self.discovered_vlans[vlan_id] = result

                                    self.logger.log_network_event("VLAN Detected",
                                                                  f"VLAN {vlan_id} (passive: {packet_count} packets over {time_span:.1f}s)")

                                    if self.callback:
                                        self.callback(result)
                except Exception as e:
                    pass

            # Sniff for VLAN tagged packets
            sniff(
                iface=self.interface,
                filter="vlan",
                prn=packet_handler,
                timeout=60,  # Listen for 60 seconds (increased from 30 for low-traffic VLANs)
                store=False,
                stop_filter=lambda x: not self.running
            )

            # Log final passive detection statistics
            self.logger.info(f"Passive listening complete. Packet counts: {vlan_packet_counts}")
            self.logger.info(f"VLANs detected via passive listening: {[v for v in vlan_packet_counts.keys() if vlan_packet_counts[v] >= MIN_PACKETS]}")

        except Exception as e:
            self.logger.log_exception("passive_listen_vlans", e)

    def get_discovered_vlans(self) -> List[int]:
        """Get list of discovered VLAN IDs"""
        return sorted([v for v, r in self.discovered_vlans.items() if r.status == "Active"])

    def get_vlan_results(self) -> List[VLANProbeResult]:
        """Get full VLAN probe results with DHCP info"""
        return [self.discovered_vlans[v] for v in sorted(self.discovered_vlans.keys())]
