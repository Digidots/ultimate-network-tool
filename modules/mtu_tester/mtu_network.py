"""
MTU Network Module - MTU Testing with Don't Fragment bit
Converted from network.js (Electron MTU Checker)
Uses Windows ping command with -f flag (Don't Fragment)
"""

import subprocess
import re
from typing import Dict
from dataclasses import dataclass
from logger import get_logger

logger = get_logger()

# Protocol overhead constants
OVERHEAD = {
    'ICMP': 28,  # 20 IP + 8 ICMP
    'UDP': 28,
    'TCP': 40
}


@dataclass
class MTUTestResult:
    """MTU test result"""
    path_mtu: int
    hop_capacity: int
    status: str
    protocol: str
    error: str = None


async def test_mtu(target_ip: str, protocol: str = 'TCP', max_mtu: int = 1500, ttl: int = 64) -> MTUTestResult:
    """
    Test MTU to a specific hop with dual testing (DF=1 and DF=0)

    Args:
        target_ip: Target IP address
        protocol: Protocol to use (TCP uses Windows ping)
        max_mtu: Maximum MTU to test
        ttl: Time to live (for specific hop testing)

    Returns:
        MTUTestResult with pathMtu and hopCapacity
    """
    logger.info(f"Testing MTU for {target_ip} using {protocol}, TTL={ttl}")

    try:
        # TCP only - uses Windows ping with DF flag
        path_mtu = await _test_tcp_mtu(target_ip, max_mtu, ttl)
        hop_capacity = path_mtu  # Note: DF=0 testing not implemented for ping

        # Determine status
        if path_mtu == 0:
            status = 'unreachable'
        elif path_mtu >= 1500 and hop_capacity >= 1500:
            status = 'optimal'
        else:
            status = 'reduced'

        return MTUTestResult(
            path_mtu=path_mtu,
            hop_capacity=hop_capacity,
            status=status,
            protocol='TCP'
        )

    except Exception as error:
        logger.error(f"MTU test failed for {target_ip}: {str(error)}")
        return MTUTestResult(
            path_mtu=0,
            hop_capacity=0,
            status='unreachable',
            protocol='TCP',
            error=str(error)
        )


async def _test_tcp_mtu(target_ip: str, max_mtu: int, ttl: int) -> int:
    """
    Test MTU using Windows ping command with Don't Fragment flag
    Uses 4-phase algorithm: common sizes → exponential growth → binary search → linear search

    Args:
        target_ip: Target IP address
        max_mtu: Maximum MTU to test
        ttl: Time to live

    Returns:
        Maximum working MTU size
    """

    async def test_packet_size(size: int) -> bool:
        """
        Test a specific packet size using Windows ping with -f flag

        Args:
            size: Total packet size (including headers)

        Returns:
            True if packet succeeded, False otherwise
        """
        try:
            # Windows ping with Don't Fragment flag
            # -f = Don't Fragment, -l = buffer size, -n 1 = 1 packet, -w 2000 = 2 sec timeout, -i = TTL
            payload_size = size - OVERHEAD['ICMP']  # ping uses ICMP overhead

            # Windows ping max payload is 65500
            if payload_size > 65500 or payload_size < 0:
                return False

            command = ['ping', '-f', '-l', str(payload_size), '-n', '1', '-w', '2000', '-i', str(ttl), target_ip]

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                stdout = result.stdout
                stderr = result.stderr
            except subprocess.TimeoutExpired:
                logger.debug(f"[MTU] Size {size}B - Timeout")
                return False
            except Exception as e:
                # Ping command returned non-zero exit code
                # This is NORMAL for fragmentation errors - capture the output anyway
                stdout = getattr(e, 'stdout', '') or ''
                stderr = getattr(e, 'stderr', '') or ''

                # Only treat as fatal error if we got no output at all
                if not stdout and not stderr:
                    logger.debug(f"[MTU] Size {size}B - FATAL ERROR: {str(e)}")
                    return False

            # Check for response indicators
            has_reply = 'Reply from' in stdout or 'bytes=' in stdout
            needs_fragment = 'Packet needs to be fragmented' in stdout or 'packet needs to be fragmented' in stdout
            timed_out = 'Request timed out' in stdout or 'timed out' in stdout
            ttl_exceeded = 'TTL expired' in stdout or 'Time to live exceeded' in stdout

            # Debug logging
            logger.debug(f"[MTU] Size {size}B (payload {payload_size}B), TTL {ttl}")
            logger.debug(f"[MTU] Reply={has_reply}, Fragment={needs_fragment}, Timeout={timed_out}, TTLExpired={ttl_exceeded}")

            # SUCCESS cases:
            if has_reply:
                # Final destination replied - MTU is OK for entire path
                logger.debug(f"[MTU] → SUCCESS (Reply received)")
                return True

            if ttl_exceeded and not needs_fragment:
                # Intermediate hop replied with TTL expired (and no fragmentation error)
                # This means the packet REACHED that hop without needing fragmentation
                logger.debug(f"[MTU] → SUCCESS (TTL expired, packet reached hop)")
                return True

            # FAILURE cases:
            if needs_fragment:
                logger.debug(f"[MTU] → FAILED (Fragmentation needed)")
                return False

            if timed_out:
                logger.debug(f"[MTU] → FAILED (Timeout)")
                return False

            # Unknown response - treat as failure
            logger.debug(f"[MTU] → FAILED (Unknown response)")
            return False

        except Exception as error:
            logger.debug(f"[MTU] Size {size}B - Exception: {str(error)}")
            return False

    logger.info(f"[MTU] Starting MTU discovery for {target_ip} using 4-phase algorithm...")

    # PHASE 1: Test common sizes to establish baseline
    common_sizes = [576, 1024, 1280, 1400, 1450, 1472, 1492, 1500]
    low = 0  # Last known working MTU
    high = None  # First known failing MTU

    logger.info("[MTU] Phase 1: Testing common MTU sizes...")
    for size in common_sizes:
        success = await test_packet_size(size)
        logger.info(f"[MTU] Test {size}B: {'OK' if success else 'FAILED'}")

        if success:
            low = size
        else:
            # Found first failure - set upper bound
            high = size
            break

    if low == 0:
        logger.info("[MTU] All common sizes failed - network unreachable")
        return 0

    logger.info(f"[MTU] Phase 1 complete: Baseline = {low}B works")

    # PHASE 2: Find upper bound (if not already found)
    if high is None:
        logger.info("[MTU] Phase 2: Exponential growth to find upper bound...")
        test_size = low * 2

        while high is None and test_size <= 65528:  # Max possible: 65500 + 28
            success = await test_packet_size(test_size)
            logger.info(f"[MTU] Test {test_size}B: {'OK' if success else 'FAILED'}")

            if success:
                low = test_size
                test_size = test_size * 2
            else:
                high = test_size

        # If we hit the ceiling without failure, cap it
        if high is None:
            high = 65528
            logger.info("[MTU] Reached maximum possible MTU (65528B)")

    logger.info(f"[MTU] Phase 2 complete: Range = {low}B (works) to {high}B (fails)")

    # PHASE 3: Binary search (halving) until gap < 10 bytes
    logger.info(f"[MTU] Phase 3: Binary search between {low}B and {high}B...")
    while high - low >= 10:
        mid = (low + high) // 2
        success = await test_packet_size(mid)
        logger.info(f"[MTU] Test {mid}B: {'OK' if success else 'FAILED'}")

        if success:
            low = mid  # We can go higher
        else:
            high = mid  # Must go lower

    logger.info(f"[MTU] Phase 3 complete: Narrowed to {low}B (works) to {high}B (fails)")

    # PHASE 4: Linear search (+1 at a time) to find exact boundary
    logger.info("[MTU] Phase 4: Linear search to find exact maximum...")
    exact_mtu = low

    for test_size in range(low + 1, high):
        success = await test_packet_size(test_size)
        logger.info(f"[MTU] Test {test_size}B: {'OK' if success else 'FAILED'}")

        if success:
            exact_mtu = test_size
        else:
            # First failure - we found the exact boundary
            break

    logger.info(f"[MTU] Phase 4 complete: Exact MTU = {exact_mtu}B")
    logger.info(f"[MTU] *** FINAL RESULT: Path MTU = {exact_mtu}B ***")

    return exact_mtu


# For synchronous compatibility
def test_mtu_sync(target_ip: str, protocol: str = 'TCP', max_mtu: int = 1500, ttl: int = 64) -> MTUTestResult:
    """
    Synchronous version of test_mtu for use in non-async contexts

    Args:
        target_ip: Target IP address
        protocol: Protocol to use
        max_mtu: Maximum MTU to test
        ttl: Time to live

    Returns:
        MTUTestResult
    """
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_mtu(target_ip, protocol, max_mtu, ttl))
    finally:
        loop.close()
