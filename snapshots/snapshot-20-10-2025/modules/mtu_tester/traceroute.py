"""
Traceroute Module - Discover network path to destination
Converted from traceroute.js (Electron MTU Checker)
"""

import subprocess
import re
from typing import List, Dict, Optional
from logger import get_logger

logger = get_logger()


def discover_path(target: str) -> List[Dict]:
    """
    Discover the network path to a target using Windows tracert command

    Args:
        target: Target hostname or IP address

    Returns:
        List of hop dictionaries containing: ttl, ip, hostname, rtt

    Raises:
        Exception: If path discovery fails
    """
    logger.info(f"Discovering path to {target}...")

    try:
        # Use Windows tracert command
        # -d: Do not resolve addresses to hostnames
        # -h 30: Maximum 30 hops
        # -w 3000: Timeout 3000ms per reply
        result = subprocess.run(
            ['tracert', '-d', '-h', '30', '-w', '3000', target],
            capture_output=True,
            text=True,
            timeout=60  # 60 seconds timeout
        )

        if result.returncode != 0 and not result.stdout:
            raise Exception(f"Traceroute failed: {result.stderr}")

        # Parse tracert output
        hops = _parse_tracert_output(result.stdout)

        if len(hops) == 0:
            raise Exception('No route found to destination')

        logger.info(f"Discovered {len(hops)} hops")
        return hops

    except subprocess.TimeoutExpired:
        logger.error('Path discovery timeout')
        # Try to get at least the target IP
        target_hop = get_target_info(target)
        if target_hop:
            return [target_hop]
        raise Exception('Path discovery timeout')

    except Exception as error:
        logger.error(f'Path discovery error: {str(error)}')

        # If tracert fails, try to at least get the target IP
        try:
            target_hop = get_target_info(target)
            if target_hop:
                return [target_hop]
        except:
            pass

        raise Exception(f'Unable to discover path: {str(error)}')


def _parse_tracert_output(output: str) -> List[Dict]:
    """
    Parse Windows tracert output

    Args:
        output: Raw tracert command output

    Returns:
        List of hop dictionaries
    """
    hops = []
    lines = output.split('\n')

    # Skip header lines
    start_parsing = False

    for line in lines:
        # Start parsing after the header
        if 'Tracing route to' in line:
            start_parsing = True
            continue

        if not start_parsing or line.strip() == '':
            continue

        # Stop at "Trace complete"
        if 'Trace complete' in line:
            break

        # Parse hop line
        # Format: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
        # Or:     "  2     *        *        *     Request timed out."
        match = re.match(r'^\s*(\d+)\s+(?:<?\d+\s*ms\s+)?(?:<?\d+\s*ms\s+)?(?:<?\d+\s*ms\s+)?([\d.]+)', line)

        if match:
            ttl = int(match.group(1))
            ip = match.group(2)

            # Extract RTT if available
            rtt_match = re.search(r'(\d+)\s*ms', line)
            rtt = int(rtt_match.group(1)) if rtt_match else None

            hops.append({
                'ttl': ttl,
                'ip': ip,
                'hostname': ip,  # tracert -d gives IPs directly
                'rtt': rtt
            })
        elif '*' in line and 'Request timed out' not in line:
            # Hop with no response
            ttl_match = re.match(r'^\s*(\d+)', line)
            if ttl_match:
                ttl = int(ttl_match.group(1))
                hops.append({
                    'ttl': ttl,
                    'ip': None,
                    'hostname': None,
                    'rtt': None
                })

    # Filter out hops with no IP (timeout hops)
    return [hop for hop in hops if hop['ip'] is not None]


def get_target_info(target: str) -> Optional[Dict]:
    """
    Get target IP using ping command (fallback method)

    Args:
        target: Target hostname or IP address

    Returns:
        Hop dictionary for the target, or None if failed
    """
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '1000', target],
            capture_output=True,
            text=True,
            timeout=5
        )

        # Extract IP from ping output
        # Windows format: "Pinging 8.8.8.8 with 32 bytes of data:"
        # or "Pinging example.com [192.168.1.1] with 32 bytes of data:"
        # or "Reply from 192.168.1.1:"
        match = re.search(r'Pinging\s+[\w.-]+\s+\[([\d.]+)\]', result.stdout, re.IGNORECASE)
        if not match:
            # Try direct IP format: "Pinging 8.8.8.8 with"
            match = re.search(r'Pinging\s+([\d.]+)\s+with', result.stdout, re.IGNORECASE)
        if not match:
            # Try reply format: "Reply from 192.168.1.1:"
            match = re.search(r'Reply from ([\d.]+):', result.stdout)

        if match:
            return {
                'ttl': 1,
                'ip': match.group(1),
                'hostname': target,
                'rtt': None
            }
    except:
        pass

    return None
