"""
MTU Checker - Command Line Interface
Simple terminal-based MTU path discovery tool
"""

import asyncio
import sys
from modules.mtu_tester import discover_path, test_mtu

def print_banner():
    print("\n" + "="*70)
    print("  MTU PATH DISCOVERY TOOL - Command Line Interface")
    print("  Digidots Network Tools")
    print("="*70 + "\n")

def run_mtu_discovery(target):
    """Run complete MTU discovery for a target"""

    print(f"Target: {target}")
    print("\n" + "-"*70)
    print("PHASE 1: Discovering network path...")
    print("-"*70)

    try:
        hops = discover_path(target)
        print(f"\nFound {len(hops)} hops to {target}:\n")

        for i, hop in enumerate(hops, 1):
            rtt_str = f"{hop.get('rtt')}ms" if hop.get('rtt') else "N/A"
            print(f"  Hop {i:2d}: {hop['ip']:<18} (TTL={hop['ttl']}, RTT={rtt_str})")

        print("\n" + "-"*70)
        print("PHASE 2: Testing MTU for each hop...")
        print("-"*70 + "\n")

        results = []
        for i, hop in enumerate(hops, 1):
            hop_ip = hop['ip']
            ttl = hop['ttl']

            print(f"  Hop {i}/{len(hops)}: {hop_ip:<18} ", end="", flush=True)

            # Run MTU test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                mtu_result = loop.run_until_complete(
                    test_mtu(hop_ip, 'TCP', 1500, ttl)
                )
            finally:
                loop.close()

            # Determine status
            if mtu_result.path_mtu == 0:
                status = "UNREACHABLE"
                icon = "X"
            elif mtu_result.path_mtu >= 1500:
                status = "OPTIMAL"
                icon = "OK"
            else:
                status = "REDUCED"
                icon = "!"

            print(f"[{icon}] MTU={mtu_result.path_mtu:4d}B  ({status})")

            results.append({
                'hop': i,
                'ip': hop_ip,
                'mtu': mtu_result.path_mtu,
                'capacity': mtu_result.hop_capacity,
                'status': status
            })

        # Print summary
        print("\n" + "="*70)
        print("  RESULTS SUMMARY")
        print("="*70)
        print(f"{'Hop':<6} {'IP Address':<20} {'Path MTU':<12} {'Capacity':<12} {'Status'}")
        print("-"*70)

        for r in results:
            mtu_str = f"{r['mtu']}B" if r['mtu'] > 0 else "N/A"
            cap_str = f"{r['capacity']}B" if r['capacity'] > 0 else "N/A"
            print(f"{r['hop']:<6} {r['ip']:<20} {mtu_str:<12} {cap_str:<12} {r['status']}")

        # Find bottleneck
        reachable = [r for r in results if r['mtu'] > 0]
        if reachable:
            min_mtu = min(r['mtu'] for r in reachable)
            bottleneck = next(r for r in reachable if r['mtu'] == min_mtu)

            print("\n" + "-"*70)
            print(f"  Lowest MTU: {min_mtu}B at Hop #{bottleneck['hop']} ({bottleneck['ip']})")

            if min_mtu >= 1500:
                print(f"  Status: OPTIMAL - Full 1500B MTU throughout the path")
            else:
                print(f"  Status: REDUCED - Maximum usable MTU is {min_mtu}B")

        print("="*70 + "\n")
        print("Discovery complete!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

def main():
    """Main CLI entry point"""
    print_banner()

    if len(sys.argv) > 1:
        # Target provided as argument
        target = sys.argv[1]
    else:
        # Interactive mode
        target = input("Enter target host or IP address (e.g., 8.8.8.8): ").strip()

    if not target:
        print("ERROR: No target specified")
        return

    run_mtu_discovery(target)

if __name__ == '__main__':
    main()
