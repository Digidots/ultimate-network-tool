"""
Ping Monitor Module
Advanced ping monitoring with range support, statistics, and real-time updates
"""

import threading
import time
import ipaddress
import socket
import platform
import subprocess
from typing import Callable, List, Dict, Optional
from datetime import datetime
from logger import get_logger


class PingResult:
    """Container for ping result data"""

    def __init__(self, ip: str):
        self.ip = ip
        self.hostname = None
        self.status = "Unknown"  # "Reachable", "Unreachable", "Testing"
        self.avg_ping_ms = None
        self.min_ping_ms = None
        self.max_ping_ms = None
        self.packets_sent = 0
        self.packets_received = 0
        self.packet_loss_percent = 0
        self.last_ping_time = None
        self.last_update = datetime.now()
        self.ttl = None
        self.consecutive_failures = 0
        self.consecutive_successes = 0


class PingMonitor:
    """Advanced ping monitoring tool"""

    def __init__(self):
        self.logger = get_logger()
        self.running = False
        self.monitor_thread = None
        self.ping_threads = []
        self.results: Dict[str, PingResult] = {}
        self.callback: Optional[Callable[[PingResult], None]] = None
        self.status_callback: Optional[Callable[[str, dict], None]] = None

        # Configuration
        self.ping_count = 4  # Number of pings per host
        self.timeout = 2  # Timeout in seconds (Windows default: 2s, uses OS defaults for TTL=128 and 32-byte packets)
        self.continuous = False  # Continuous monitoring
        self.interval = 5  # Interval between ping rounds (if continuous)
        self.max_concurrent_pings = 50  # Limit concurrent pings
        self.resolve_hostnames = True

    def parse_input(self, input_text: str) -> List[str]:
        """
        Parse input text and return list of IP addresses
        Supports:
        - Single IPs (one per line)
        - IP ranges: 192.168.1.1-192.168.1.100 or 192.168.1.10-20 (short form)
        - Comma-separated octets: 192.168.1,10,100,101 (expands to .1, .10, .100, .101)
        - CIDR notation: 192.168.1.0/24
        """
        ips = []
        lines = input_text.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            try:
                # Check if it's comma-separated octets (192.168.1,10,100,101)
                if ',' in line and '/' not in line and '-' not in line:
                    parts = line.split(',')
                    # First part should be base IP (e.g., "192.168.1")
                    base_parts = parts[0].strip().split('.')
                    if len(base_parts) >= 3:
                        base_ip = '.'.join(base_parts[:3])  # 192.168.1

                        # If first part has 4 octets, add it as is
                        if len(base_parts) == 4:
                            ips.append(parts[0].strip())

                        # Add remaining octets
                        for octet in parts[1:]:
                            octet = octet.strip()
                            full_ip = f"{base_ip}.{octet}"
                            ipaddress.IPv4Address(full_ip)  # Validate
                            ips.append(full_ip)
                    else:
                        raise ValueError(f"Invalid IP format: {line}")

                # Check if it's a range (192.168.1.1-192.168.1.100 or 192.168.1.10-20)
                elif '-' in line and '/' not in line:
                    start_ip, end_part = line.split('-', 1)
                    start_ip = start_ip.strip()
                    end_part = end_part.strip()

                    # Check if end_part is a short form (just the last octet)
                    if '.' not in end_part:
                        # Short form: 192.168.1.10-20
                        # Extract the base IP (192.168.1.) from start_ip
                        ip_parts = start_ip.split('.')
                        if len(ip_parts) == 4:
                            base_ip = '.'.join(ip_parts[:3])  # 192.168.1
                            end_ip = f"{base_ip}.{end_part}"  # 192.168.1.20
                        else:
                            raise ValueError(f"Invalid IP format: {start_ip}")
                    else:
                        # Full form: 192.168.1.1-192.168.1.100
                        end_ip = end_part

                    # Convert to integers
                    start = int(ipaddress.IPv4Address(start_ip))
                    end = int(ipaddress.IPv4Address(end_ip))

                    # Generate all IPs in range
                    for ip_int in range(start, end + 1):
                        ips.append(str(ipaddress.IPv4Address(ip_int)))

                # Check if it's CIDR notation (192.168.1.0/24)
                elif '/' in line:
                    network = ipaddress.IPv4Network(line, strict=False)
                    for ip in network.hosts():
                        ips.append(str(ip))

                # Single IP or hostname
                else:
                    # Validate it's a valid IP or hostname
                    try:
                        ipaddress.IPv4Address(line)
                        ips.append(line)
                    except:
                        # Might be a hostname
                        ips.append(line)

            except Exception as e:
                self.logger.error(f"Error parsing line '{line}': {e}")
                continue

        self.logger.info(f"Parsed {len(ips)} IP addresses from input")
        return ips

    def resolve_hostname(self, ip: str) -> Optional[str]:
        """Resolve IP to hostname"""
        if not self.resolve_hostnames:
            return None

        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except:
            return None

    def ping_host(self, ip: str) -> PingResult:
        """
        Ping a single host with ONE ping for fast updates (ping -t behavior)
        Uses system ping command for reliability
        """
        result = PingResult(ip)

        # Resolve hostname only once (cache it)
        if self.resolve_hostnames and not result.hostname:
            if ip in self.results and self.results[ip].hostname:
                result.hostname = self.results[ip].hostname
            else:
                result.hostname = self.resolve_hostname(ip)

        # FORCE single ping for fast updates (ping -t behavior)
        ping_count = 1

        # Determine ping command based on OS
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        timeout_param = '-w' if platform.system().lower() == 'windows' else '-W'

        # Use shorter timeout for faster responses (1 second default)
        timeout_ms = 1000 if platform.system().lower() == 'windows' else 1

        command = ['ping', param, '1', timeout_param, str(timeout_ms), ip]

        try:
            output = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=2  # Max 2 seconds total
            )

            # Parse output - SIMPLIFIED for single ping
            output_text = output.stdout + output.stderr

            # Always 1 packet sent
            result.packets_sent = 1

            if platform.system().lower() == 'windows':
                # Windows: Look for "Reply from" line
                # Example: Reply from 192.168.1.1: bytes=32 time=2ms TTL=64
                if 'Reply from' in output_text:
                    result.status = "Reachable"
                    result.packets_received = 1
                    result.packet_loss_percent = 0

                    # Extract time and TTL from the Reply line
                    for line in output_text.split('\n'):
                        if 'Reply from' in line:
                            # Extract time
                            if 'time=' in line or 'time<' in line:
                                time_part = [p for p in line.split() if 'time' in p.lower()][0]
                                time_str = time_part.split('=')[1] if '=' in time_part else time_part.split('<')[1]
                                time_val = float(time_str.replace('ms', '').strip())
                                result.avg_ping_ms = time_val
                                result.min_ping_ms = time_val
                                result.max_ping_ms = time_val
                                result.last_ping_time = time_val

                            # Extract TTL
                            if 'TTL=' in line or 'ttl=' in line:
                                ttl_part = [p for p in line.split() if 'TTL=' in p or 'ttl=' in p][0]
                                result.ttl = int(ttl_part.split('=')[1])
                            break
                else:
                    result.status = "Unreachable"
                    result.packets_received = 0
                    result.packet_loss_percent = 100

            else:
                # Linux/Unix: Look for "bytes from" line
                # Example: 64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=2.1 ms
                if 'bytes from' in output_text:
                    result.status = "Reachable"
                    result.packets_received = 1
                    result.packet_loss_percent = 0

                    # Extract time and TTL
                    for line in output_text.split('\n'):
                        if 'bytes from' in line:
                            # Extract time
                            if 'time=' in line:
                                time_part = [p for p in line.split() if 'time=' in p][0]
                                time_val = float(time_part.split('=')[1].replace('ms', '').strip())
                                result.avg_ping_ms = time_val
                                result.min_ping_ms = time_val
                                result.max_ping_ms = time_val
                                result.last_ping_time = time_val

                            # Extract TTL
                            if 'ttl=' in line.lower():
                                ttl_part = [p for p in line.split() if 'ttl=' in p.lower()][0]
                                result.ttl = int(ttl_part.split('=')[1])
                            break
                else:
                    result.status = "Unreachable"
                    result.packets_received = 0
                    result.packet_loss_percent = 100

            result.last_ping_time = result.avg_ping_ms
            result.last_update = datetime.now()

            # Update consecutive counters
            if result.status == "Reachable":
                result.consecutive_successes += 1
                result.consecutive_failures = 0
            else:
                result.consecutive_failures += 1
                result.consecutive_successes = 0

        except subprocess.TimeoutExpired:
            result.status = "Unreachable"
            result.packets_sent = self.ping_count
            result.packet_loss_percent = 100
            self.logger.warning(f"Ping timeout for {ip}")
        except Exception as e:
            result.status = "Error"
            self.logger.error(f"Error pinging {ip}: {e}")

        return result

    def start_monitoring(self, ips: List[str], callback: Optional[Callable[[PingResult], None]] = None):
        """Start monitoring hosts - each host gets its own continuous ping thread"""
        self.callback = callback
        self.running = True
        self.results.clear()
        self.ping_threads.clear()

        # Start one thread per host for continuous pinging
        for ip in ips:
            thread = threading.Thread(
                target=self._continuous_ping_loop,
                args=(ip,),
                daemon=True
            )
            thread.start()
            self.ping_threads.append(thread)

        self.logger.log_action("Ping Monitor Started (Web)", f"{len(ips)} hosts")
        return True

    def _continuous_ping_loop(self, ip: str):
        """Continuously ping a single host at interval rate (like ping -t)"""
        try:
            while self.running:
                ping_start = time.time()

                # Perform a single ping (ping_count should be 1 for ping -t behavior)
                result = self.ping_host(ip)
                self.results[ip] = result

                # Send callback immediately (live update)
                if self.callback:
                    self.callback(result)

                # If not continuous, stop after first ping
                if not self.continuous:
                    break

                # Calculate how long to wait before next ping
                ping_duration = time.time() - ping_start
                remaining_wait = max(0, self.interval - ping_duration)

                # Wait for the interval (or remaining time)
                for _ in range(int(remaining_wait * 10)):
                    if not self.running:
                        break
                    time.sleep(0.1)

        except Exception as e:
            self.logger.log_exception(f"continuous_ping_loop_{ip}", e)

    def stop_monitoring(self):
        """Stop monitoring"""
        self.logger.log_action("Ping Monitor Stopped", f"{len(self.results)} hosts monitored")
        self.running = False

        # Wait for all ping threads to stop
        for thread in self.ping_threads:
            thread.join(timeout=0.5)

    def get_statistics(self) -> dict:
        """Get overall statistics"""
        total = len(self.results)
        reachable = len([r for r in self.results.values() if r.status == "Reachable"])
        unreachable = len([r for r in self.results.values() if r.status == "Unreachable"])

        # Calculate average response time for reachable hosts
        avg_times = [r.avg_ping_ms for r in self.results.values() if r.avg_ping_ms is not None]
        avg_response_time = sum(avg_times) / len(avg_times) if avg_times else 0

        return {
            'total': total,
            'reachable': reachable,
            'unreachable': unreachable,
            'reachable_percent': (reachable / total * 100) if total > 0 else 0,
            'avg_response_time': round(avg_response_time, 2)
        }
