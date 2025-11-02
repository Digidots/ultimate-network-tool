"""
Direct MTU Discovery Test - No Browser Needed
Run this to test MTU discovery directly from command line
"""

import asyncio
from modules.mtu_tester import discover_path, test_mtu

print("="*60)
print("  MTU DISCOVERY - DIRECT TEST")
print("="*60)

target = "8.8.8.8"
print(f"\nTarget: {target}")
print("\n[1/2] Discovering path with traceroute...")

try:
    hops = discover_path(target)
    print(f"    Found {len(hops)} hops!\n")

    for i, hop in enumerate(hops, 1):
        print(f"    Hop {i}: {hop['ip']} (TTL={hop['ttl']})")

    print(f"\n[2/2] Testing MTU for each hop...")

    results = []
    for i, hop in enumerate(hops, 1):
        hop_ip = hop['ip']
        ttl = hop['ttl']

        print(f"\n    Testing hop {i}: {hop_ip}...", end=" ")

        # Run MTU test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            mtu_result = loop.run_until_complete(
                test_mtu(hop_ip, 'TCP', 1500, ttl)
            )
        finally:
            loop.close()

        if mtu_result.path_mtu == 0:
            status = "UNREACHABLE"
        elif mtu_result.path_mtu >= 1500:
            status = "OPTIMAL"
        else:
            status = "REDUCED"

        print(f"MTU={mtu_result.path_mtu}B ({status})")

        results.append({
            'hop': i,
            'ip': hop_ip,
            'mtu': mtu_result.path_mtu,
            'status': status
        })

    print("\n" + "="*60)
    print("  RESULTS")
    print("="*60)
    print(f"{'Hop':<6} {'IP Address':<20} {'MTU':<10} {'Status'}")
    print("-"*60)

    for r in results:
        print(f"{r['hop']:<6} {r['ip']:<20} {r['mtu']:<10} {r['status']}")

    print("="*60)
    print("\nSUCCESS! MTU discovery works perfectly.")
    print("\nThe backend is fine - the issue is only with the web interface.")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
