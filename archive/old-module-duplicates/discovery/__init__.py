"""
Discovery Module - LLDP/CDP and VLAN Detection
"""
from .lldp_cdp_discovery import LLDPCDPDiscovery, DiscoveryResult
from .vlan_probe import VLANProber, VLANProbeResult

__all__ = ['LLDPCDPDiscovery', 'DiscoveryResult', 'VLANProber', 'VLANProbeResult']
