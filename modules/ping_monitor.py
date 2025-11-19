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
import re
from typing import Callable, List, Dict, Optional
from datetime import datetime
from logger import get_logger


# MAC Vendor OUI Database (simplified - common vendors)
MAC_VENDORS = {
    '00:0C:29': 'VMware',
    '00:50:56': 'VMware',
    '00:1C:42': 'Parallels',
    '08:00:27': 'Oracle VirtualBox',
    '52:54:00': 'QEMU/KVM',
    '00:15:5D': 'Microsoft Hyper-V',
    '00:03:FF': 'Microsoft',
    'DC:A6:32': 'Raspberry Pi',
    'B8:27:EB': 'Raspberry Pi',
    'E4:5F:01': 'Raspberry Pi',
    '28:CD:C1': 'Raspberry Pi',
    '00:1B:63': 'Apple',
    '00:03:93': 'Apple',
    '00:0A:95': 'Apple',
    '00:0D:93': 'Apple',
    '00:14:51': 'Apple',
    '00:16:CB': 'Apple',
    '00:17:F2': 'Apple',
    '00:19:E3': 'Apple',
    '00:1C:B3': 'Apple',
    '00:1E:52': 'Apple',
    '00:1F:5B': 'Apple',
    '00:1F:F3': 'Apple',
    '00:21:E9': 'Apple',
    '00:22:41': 'Apple',
    '00:23:12': 'Apple',
    '00:23:32': 'Apple',
    '00:23:6C': 'Apple',
    '00:23:DF': 'Apple',
    '00:24:36': 'Apple',
    '00:25:00': 'Apple',
    '00:25:4B': 'Apple',
    '00:25:BC': 'Apple',
    '00:26:08': 'Apple',
    '00:26:4A': 'Apple',
    '00:26:B0': 'Apple',
    '00:26:BB': 'Apple',
    '04:0C:CE': 'Apple',
    '04:15:52': 'Apple',
    '04:26:65': 'Apple',
    '04:54:53': 'Apple',
    '08:66:98': 'Apple',
    '0C:3E:9F': 'Apple',
    '0C:3F:0F': 'Apple',
    '10:40:F3': 'Apple',
    '10:93:E9': 'Apple',
    '10:9A:DD': 'Apple',
    '14:10:9F': 'Apple',
    '14:8F:C6': 'Apple',
    '18:65:90': 'Apple',
    '1C:AB:A7': 'Apple',
    '20:AB:37': 'Apple',
    '20:C9:D0': 'Apple',
    '24:A0:74': 'Apple',
    '24:AB:81': 'Apple',
    '28:37:37': 'Apple',
    '28:6A:BA': 'Apple',
    '28:E1:4C': 'Apple',
    '2C:BE:08': 'Apple',
    '30:90:AB': 'Apple',
    '34:12:98': 'Apple',
    '34:36:3B': 'Apple',
    '38:C9:86': 'Apple',
    '3C:06:30': 'Apple',
    '3C:15:C2': 'Apple',
    '40:30:04': 'Apple',
    '40:3C:FC': 'Apple',
    '44:2A:60': 'Apple',
    '48:74:6E': 'Apple',
    '4C:57:CA': 'Apple',
    '4C:74:BF': 'Apple',
    '4C:8D:79': 'Apple',
    '50:EA:D6': 'Apple',
    '54:26:96': 'Apple',
    '58:55:CA': 'Apple',
    '5C:59:48': 'Apple',
    '5C:95:AE': 'Apple',
    '5C:F9:38': 'Apple',
    '60:03:08': 'Apple',
    '60:33:4B': 'Apple',
    '60:69:44': 'Apple',
    '60:C5:47': 'Apple',
    '60:F8:1D': 'Apple',
    '60:FA:CD': 'Apple',
    '60:FB:42': 'Apple',
    '64:20:0C': 'Apple',
    '64:9A:BE': 'Apple',
    '64:A3:CB': 'Apple',
    '64:B9:E8': 'Apple',
    '68:5B:35': 'Apple',
    '68:96:7B': 'Apple',
    '68:A8:6D': 'Apple',
    '68:D9:3C': 'Apple',
    '6C:3E:6D': 'Apple',
    '6C:40:08': 'Apple',
    '6C:72:E7': 'Apple',
    '6C:94:66': 'Apple',
    '6C:96:CF': 'Apple',
    '70:11:24': 'Apple',
    '70:48:0F': 'Apple',
    '70:56:81': 'Apple',
    '70:73:CB': 'Apple',
    '70:CD:60': 'Apple',
    '70:DE:E2': 'Apple',
    '70:EC:E4': 'Apple',
    '74:1B:B2': 'Apple',
    '74:E1:B6': 'Apple',
    '74:E2:F5': 'Apple',
    '78:31:C1': 'Apple',
    '78:67:D7': 'Apple',
    '78:7B:8A': 'Apple',
    '78:88:6D': 'Apple',
    '78:A3:E4': 'Apple',
    '78:CA:39': 'Apple',
    '7C:01:91': 'Apple',
    '7C:6D:62': 'Apple',
    '7C:C5:37': 'Apple',
    '7C:D1:C3': 'Apple',
    '7C:F0:5F': 'Apple',
    '80:49:71': 'Apple',
    '80:92:9F': 'Apple',
    '80:BE:05': 'Apple',
    '80:E6:50': 'Apple',
    '84:38:35': 'Apple',
    '84:85:06': 'Apple',
    '84:8E:0C': 'Apple',
    '84:FC:FE': 'Apple',
    '88:1F:A1': 'Apple',
    '88:53:95': 'Apple',
    '88:63:DF': 'Apple',
    '88:66:5A': 'Apple',
    '88:C6:63': 'Apple',
    '8C:2D:AA': 'Apple',
    '8C:58:77': 'Apple',
    '8C:7C:92': 'Apple',
    '8C:85:90': 'Apple',
    '8C:8E:F2': 'Apple',
    '90:27:E4': 'Apple',
    '90:72:40': 'Apple',
    '90:84:0D': 'Apple',
    '90:8D:6C': 'Apple',
    '90:B0:ED': 'Apple',
    '90:B9:31': 'Apple',
    '90:FD:61': 'Apple',
    '94:E9:6A': 'Apple',
    '94:F6:A3': 'Apple',
    '98:01:A7': 'Apple',
    '98:03:D8': 'Apple',
    '98:5A:EB': 'Apple',
    '98:B8:E3': 'Apple',
    '98:CA:33': 'Apple',
    '98:D6:BB': 'Apple',
    '98:E0:D9': 'Apple',
    '98:F0:AB': 'Apple',
    '98:FE:94': 'Apple',
    '9C:04:EB': 'Apple',
    '9C:20:7B': 'Apple',
    '9C:35:EB': 'Apple',
    '9C:84:BF': 'Apple',
    '9C:D2:1E': 'Apple',
    '9C:F4:8E': 'Apple',
    '9C:FC:E8': 'Apple',
    'A0:18:28': 'Apple',
    'A0:99:9B': 'Apple',
    'A0:D7:95': 'Apple',
    'A4:5E:60': 'Apple',
    'A4:67:06': 'Apple',
    'A4:B1:97': 'Apple',
    'A4:C3:61': 'Apple',
    'A8:20:66': 'Apple',
    'A8:5C:2C': 'Apple',
    'A8:60:B6': 'Apple',
    'A8:66:7F': 'Apple',
    'A8:86:DD': 'Apple',
    'A8:88:08': 'Apple',
    'A8:96:8A': 'Apple',
    'A8:BE:27': 'Apple',
    'A8:FA:D8': 'Apple',
    'AC:3C:0B': 'Apple',
    'AC:61:EA': 'Apple',
    'AC:7F:3E': 'Apple',
    'AC:87:A3': 'Apple',
    'AC:BC:32': 'Apple',
    'AC:CF:5C': 'Apple',
    'AC:DE:48': 'Apple',
    'AC:E4:B5': 'Apple',
    'AC:FD:EC': 'Apple',
    'B0:65:BD': 'Apple',
    'B0:CA:68': 'Apple',
    'B4:18:D1': 'Apple',
    'B4:8B:19': 'Apple',
    'B4:F0:AB': 'Apple',
    'B4:F6:1C': 'Apple',
    'B8:08:CF': 'Apple',
    'B8:41:A4': 'Apple',
    'B8:44:D9': 'Apple',
    'B8:5D:0A': 'Apple',
    'B8:63:4D': 'Apple',
    'B8:78:2E': 'Apple',
    'B8:8D:12': 'Apple',
    'B8:C1:11': 'Apple',
    'B8:E8:56': 'Apple',
    'B8:F6:B1': 'Apple',
    'B8:FF:61': 'Apple',
    'BC:3B:AF': 'Apple',
    'BC:52:B7': 'Apple',
    'BC:6C:21': 'Apple',
    'BC:92:6B': 'Apple',
    'BC:9F:EF': 'Apple',
    'BC:EC:5D': 'Apple',
    'C0:1A:DA': 'Apple',
    'C0:63:94': 'Apple',
    'C0:84:7D': 'Apple',
    'C0:9F:42': 'Apple',
    'C0:B6:58': 'Apple',
    'C0:CE:CD': 'Apple',
    'C0:D0:12': 'Apple',
    'C0:F2:FB': 'Apple',
    'C4:2C:03': 'Apple',
    'C4:61:8B': 'Apple',
    'C4:B3:01': 'Apple',
    'C8:2A:14': 'Apple',
    'C8:33:4B': 'Apple',
    'C8:69:CD': 'Apple',
    'C8:85:50': 'Apple',
    'C8:B5:B7': 'Apple',
    'C8:BC:C8': 'Apple',
    'C8:D0:83': 'Apple',
    'C8:E0:EB': 'Apple',
    'CC:08:E0': 'Apple',
    'CC:20:E8': 'Apple',
    'CC:25:EF': 'Apple',
    'CC:29:F5': 'Apple',
    'CC:2D:8C': 'Apple',
    'CC:44:63': 'Apple',
    'CC:78:5F': 'Apple',
    'CC:C7:60': 'Apple',
    'D0:03:4B': 'Apple',
    'D0:23:DB': 'Apple',
    'D0:25:44': 'Apple',
    'D0:33:11': 'Apple',
    'D0:4F:7E': 'Apple',
    'D0:81:7A': 'Apple',
    'D0:A6:37': 'Apple',
    'D0:C5:F3': 'Apple',
    'D0:D2:B0': 'Apple',
    'D0:E1:40': 'Apple',
    'D4:9A:20': 'Apple',
    'D4:A3:3D': 'Apple',
    'D4:DC:CD': 'Apple',
    'D4:F4:6F': 'Apple',
    'D8:00:4D': 'Apple',
    'D8:1D:72': 'Apple',
    'D8:30:62': 'Apple',
    'D8:96:95': 'Apple',
    'D8:9E:3F': 'Apple',
    'D8:A2:5E': 'Apple',
    'D8:BB:2C': 'Apple',
    'D8:CF:9C': 'Apple',
    'DC:0C:5C': 'Apple',
    'DC:2B:2A': 'Apple',
    'DC:2B:61': 'Apple',
    'DC:37:09': 'Apple',
    'DC:3A:5E': 'Apple',
    'DC:41:5F': 'Apple',
    'DC:86:D8': 'Apple',
    'DC:9B:9C': 'Apple',
    'DC:A9:04': 'Apple',
    'DC:C6:E7': 'Apple',
    'DC:E5:33': 'Apple',
    'E0:05:C5': 'Apple',
    'E0:66:78': 'Apple',
    'E0:99:71': 'Apple',
    'E0:AC:CB': 'Apple',
    'E0:B9:A5': 'Apple',
    'E0:B9:BA': 'Apple',
    'E0:C7:67': 'Apple',
    'E0:F5:C6': 'Apple',
    'E0:F8:47': 'Apple',
    'E4:25:E7': 'Apple',
    'E4:8B:7F': 'Apple',
    'E4:9A:79': 'Apple',
    'E4:C6:3D': 'Apple',
    'E4:CE:8F': 'Apple',
    'E4:E4:AB': 'Apple',
    'E8:04:0B': 'Apple',
    'E8:06:88': 'Apple',
    'E8:2A:EA': 'Apple',
    'E8:40:F2': 'Apple',
    'E8:80:2E': 'Apple',
    'E8:B2:AC': 'Apple',
    'EC:35:86': 'Apple',
    'EC:85:2F': 'Apple',
    'EC:A8:6B': 'Apple',
    'F0:18:98': 'Apple',
    'F0:1D:2D': 'Apple',
    'F0:24:75': 'Apple',
    'F0:25:B7': 'Apple',
    'F0:4F:7C': 'Apple',
    'F0:5C:19': 'Apple',
    'F0:76:1C': 'Apple',
    'F0:98:9D': 'Apple',
    'F0:99:B6': 'Apple',
    'F0:B4:79': 'Apple',
    'F0:C1:F1': 'Apple',
    'F0:CB:A1': 'Apple',
    'F0:D1:A9': 'Apple',
    'F0:D5:BF': 'Apple',
    'F0:DB:E2': 'Apple',
    'F0:DC:E2': 'Apple',
    'F0:F6:1C': 'Apple',
    'F4:0F:24': 'Apple',
    'F4:1B:A1': 'Apple',
    'F4:37:B7': 'Apple',
    'F4:5C:89': 'Apple',
    'F4:F1:5A': 'Apple',
    'F4:F9:51': 'Apple',
    'F8:1E:DF': 'Apple',
    'F8:27:93': 'Apple',
    'F8:2D:7C': 'Apple',
    'F8:95:C7': 'Apple',
    'F8:D0:BD': 'Apple',
    'F8:E9:4E': 'Apple',
    'FC:25:3F': 'Apple',
    'FC:64:BA': 'Apple',
    'FC:E9:98': 'Apple',
    'FC:FC:48': 'Apple',
    '00:50:F2': 'Microsoft',
    '00:0D:3A': 'Microsoft',
    '00:12:5A': 'Microsoft',
    '00:17:FA': 'Microsoft',
    '00:1D:D8': 'Microsoft',
    '00:22:48': 'Microsoft',
    '00:25:AE': 'Microsoft',
    '28:18:78': 'Microsoft',
    '7C:1E:52': 'Microsoft',
    'A0:CE:C8': 'Microsoft',
    '00:11:22': 'Cisco',
    '00:1B:D5': 'Cisco',
    '00:1C:58': 'Cisco',
    '00:1D:A2': 'Cisco',
    '00:1E:13': 'Cisco',
    '00:1E:BD': 'Cisco',
    '00:1E:F7': 'Cisco',
    '00:21:55': 'Cisco',
    '00:21:A0': 'Cisco',
    '00:21:BE': 'Cisco',
    '00:22:0C': 'Cisco',
    '00:22:3A': 'Cisco',
    '00:22:55': 'Cisco',
    '00:22:90': 'Cisco',
    '00:22:BD': 'Cisco',
    '00:22:CE': 'Cisco',
    '00:23:04': 'Cisco',
    '00:23:33': 'Cisco',
    '00:23:5D': 'Cisco',
    '00:23:AC': 'Cisco',
    '00:23:BE': 'Cisco',
    '00:23:EA': 'Cisco',
    '00:24:13': 'Cisco',
    '00:24:14': 'Cisco',
    '00:24:50': 'Cisco',
    '00:24:97': 'Cisco',
    '00:24:C3': 'Cisco',
    '00:24:F7': 'Cisco',
    '00:25:45': 'Cisco',
    '00:25:46': 'Cisco',
    '00:25:83': 'Cisco',
    '00:25:84': 'Cisco',
    '00:25:B4': 'Cisco',
    '00:26:0A': 'Cisco',
    '00:26:51': 'Cisco',
    '00:26:52': 'Cisco',
    '00:26:98': 'Cisco',
    '00:26:99': 'Cisco',
    '00:26:CA': 'Cisco',
    '00:26:CB': 'Cisco',
    '04:62:73': 'Cisco',
    '04:C5:A4': 'Cisco',
    '04:DA:D2': 'Cisco',
    '04:FE:7F': 'Cisco',
    '08:17:35': 'Cisco',
    '08:7C:03': 'Cisco',
    '08:96:AD': 'Cisco',
    '08:CC:68': 'Cisco',
    '0C:27:24': 'Cisco',
    '0C:68:03': 'Cisco',
    '0C:75:BD': 'Cisco',
    '0C:85:25': 'Cisco',
    '0C:8D:DB': 'Cisco',
    '0C:D9:96': 'Cisco',
    '0C:F5:A4': 'Cisco',
    '10:05:CA': 'Cisco',
    '10:8C:CF': 'Cisco',
    '10:BD:18': 'Cisco',
    '14:D6:4D': 'Cisco',
    '18:8B:45': 'Cisco',
    '18:9C:5D': 'Cisco',
    '18:E7:28': 'Cisco',
    '18:EF:63': 'Cisco',
    '1C:1D:86': 'Cisco',
    '1C:DE:A7': 'Cisco',
    '20:37:06': 'Cisco',
    '20:3A:07': 'Cisco',
    '20:4C:9E': 'Cisco',
    '20:BB:C0': 'Cisco',
    '24:01:C7': 'Cisco',
    '24:76:7D': 'Cisco',
    '24:7F:3F': 'Cisco',
    '24:B6:FD': 'Cisco',
    '28:94:0F': 'Cisco',
    '28:C7:CE': 'Cisco',
    '2C:36:F8': 'Cisco',
    '2C:54:2D': 'Cisco',
    '2C:5A:0F': 'Cisco',
    '2C:D0:2D': 'Cisco',
    '30:37:A6': 'Cisco',
    '30:E4:DB': 'Cisco',
    '34:62:88': 'Cisco',
    '34:A8:4E': 'Cisco',
    '34:BD:FA': 'Cisco',
    '38:20:56': 'Cisco',
    '38:ED:18': 'Cisco',
    '3C:08:F6': 'Cisco',
    '3C:0E:23': 'Cisco',
    '3C:DF:1E': 'Cisco',
    '40:55:39': 'Cisco',
    '44:03:A7': 'Cisco',
    '44:E0:8E': 'Cisco',
    '44:E4:D9': 'Cisco',
    '48:44:F7': 'Cisco',
    '48:F8:B3': 'Cisco',
    '4C:00:82': 'Cisco',
    '4C:4E:35': 'Cisco',
    '50:06:04': 'Cisco',
    '50:0F:80': 'Cisco',
    '50:57:A8': 'Cisco',
    '50:87:89': 'Cisco',
    '54:78:1A': 'Cisco',
    '54:A2:74': 'Cisco',
    '58:0A:20': 'Cisco',
    '58:6D:8F': 'Cisco',
    '58:8D:09': 'Cisco',
    '58:97:BD': 'Cisco',
    '58:AC:78': 'Cisco',
    '58:BF:EA': 'Cisco',
    '58:F3:9C': 'Cisco',
    '5C:50:15': 'Cisco',
    '5C:83:8E': 'Cisco',
    '5C:A4:8A': 'Cisco',
    '60:5C:AC': 'Cisco',
    '60:73:BC': 'Cisco',
    '64:00:F1': 'Cisco',
    '64:16:8D': 'Cisco',
    '64:9E:F3': 'Cisco',
    '64:A0:E7': 'Cisco',
    '64:AE:0C': 'Cisco',
    '64:D4:DA': 'Cisco',
    '64:D9:89': 'Cisco',
    '64:E9:50': 'Cisco',
    '64:F6:9D': 'Cisco',
    '68:7F:74': 'Cisco',
    '68:BC:0C': 'Cisco',
    '68:BD:AB': 'Cisco',
    '68:EF:BD': 'Cisco',
    '6C:20:56': 'Cisco',
    '6C:41:6A': 'Cisco',
    '6C:50:4D': 'Cisco',
    '6C:99:89': 'Cisco',
    '6C:9C:ED': 'Cisco',
    '6C:C7:EC': 'Cisco',
    '6C:FA:89': 'Cisco',
    '70:10:5C': 'Cisco',
    '70:38:EE': 'Cisco',
    '70:6D:15': 'Cisco',
    '70:81:EB': 'Cisco',
    '70:CA:9B': 'Cisco',
    '70:D3:79': 'Cisco',
    '70:DB:98': 'Cisco',
    '70:E4:22': 'Cisco',
    '70:EA:1A': 'Cisco',
    '70:F3:95': 'Cisco',
    '74:26:AC': 'Cisco',
    '74:A0:2F': 'Cisco',
    '74:A2:E6': 'Cisco',
    '78:72:5D': 'Cisco',
    '78:BA:F9': 'Cisco',
    '78:DA:6E': 'Cisco',
    '7C:0E:CE': 'Cisco',
    '7C:69:F6': 'Cisco',
    '7C:95:F3': 'Cisco',
    '7C:AD:74': 'Cisco',
    '80:1F:02': 'Cisco',
    '84:78:AC': 'Cisco',
    '84:80:2D': 'Cisco',
    '84:B5:17': 'Cisco',
    '84:B8:02': 'Cisco',
    '88:43:E1': 'Cisco',
    '88:75:56': 'Cisco',
    '88:90:8D': 'Cisco',
    '88:F0:31': 'Cisco',
    '8C:60:4F': 'Cisco',
    '8C:B6:4F': 'Cisco',
    '90:6C:AC': 'Cisco',
    '90:E9:5E': 'Cisco',
    '94:60:59': 'Cisco',
    '94:D4:69': 'Cisco',
    '98:FC:11': 'Cisco',
    '9C:4E:20': 'Cisco',
    '9C:AF:CA': 'Cisco',
    'A0:3D:6F': 'Cisco',
    'A0:55:4F': 'Cisco',
    'A0:CE:F6': 'Cisco',
    'A0:F8:49': 'Cisco',
    'A4:18:75': 'Cisco',
    'A4:4C:11': 'Cisco',
    'A4:6C:2A': 'Cisco',
    'A4:93:4C': 'Cisco',
    'A8:0C:0D': 'Cisco',
    'A8:9D:21': 'Cisco',
    'A8:B1:D4': 'Cisco',
    'AC:7E:8A': 'Cisco',
    'AC:A0:16': 'Cisco',
    'AC:F2:C5': 'Cisco',
    'B0:00:B4': 'Cisco',
    'B0:7D:47': 'Cisco',
    'B0:7F:B9': 'Cisco',
    'B0:C5:CA': 'Cisco',
    'B0:FA:EB': 'Cisco',
    'B4:14:89': 'Cisco',
    'B4:A4:E3': 'Cisco',
    'B4:E9:B0': 'Cisco',
    'B8:38:61': 'Cisco',
    'B8:62:1F': 'Cisco',
    'B8:A3:86': 'Cisco',
    'B8:BE:BF': 'Cisco',
    'BC:16:F5': 'Cisco',
    'BC:67:1C': 'Cisco',
    'BC:C4:93': 'Cisco',
    'BC:F1:F2': 'Cisco',
    'C0:00:4D': 'Cisco',
    'C0:25:5C': 'Cisco',
    'C0:3F:0E': 'Cisco',
    'C0:62:6B': 'Cisco',
    'C0:7B:BC': 'Cisco',
    'C4:0A:CB': 'Cisco',
    'C4:64:13': 'Cisco',
    'C4:71:54': 'Cisco',
    'C4:7D:4F': 'Cisco',
    'C8:00:84': 'Cisco',
    'C8:3A:35': 'Cisco',
    'C8:4C:75': 'Cisco',
    'C8:9C:1D': 'Cisco',
    'C8:F9:F9': 'Cisco',
    'CC:16:7E': 'Cisco',
    'CC:3A:61': 'Cisco',
    'CC:46:D6': 'Cisco',
    'CC:D5:39': 'Cisco',
    'CC:D8:C1': 'Cisco',
    'CC:EF:48': 'Cisco',
    'D0:57:4C': 'Cisco',
    'D0:72:DC': 'Cisco',
    'D0:C2:82': 'Cisco',
    'D0:D3:E0': 'Cisco',
    'D4:6D:50': 'Cisco',
    'D4:A0:2A': 'Cisco',
    'D4:E8:80': 'Cisco',
    'D8:24:BD': 'Cisco',
    'D8:67:D9': 'Cisco',
    'D8:B1:90': 'Cisco',
    'DC:7B:94': 'Cisco',
    'DC:8C:37': 'Cisco',
    'E0:2F:6D': 'Cisco',
    'E0:5F:B9': 'Cisco',
    'E0:89:9D': 'Cisco',
    'E0:D1:73': 'Cisco',
    'E4:48:C7': 'Cisco',
    'E4:AA:5D': 'Cisco',
    'E4:C7:22': 'Cisco',
    'E8:04:62': 'Cisco',
    'E8:40:40': 'Cisco',
    'E8:65:49': 'Cisco',
    'E8:9A:8F': 'Cisco',
    'E8:B7:48': 'Cisco',
    'E8:BA:70': 'Cisco',
    'E8:ED:F3': 'Cisco',
    'EC:1D:8B': 'Cisco',
    'EC:30:91': 'Cisco',
    'EC:44:76': 'Cisco',
    'EC:BD:1D': 'Cisco',
    'EC:C8:82': 'Cisco',
    'EC:E1:A9': 'Cisco',
    'F0:25:72': 'Cisco',
    'F0:29:29': 'Cisco',
    'F0:7D:68': 'Cisco',
    'F0:F7:55': 'Cisco',
    'F4:0F:1B': 'Cisco',
    'F4:4E:05': 'Cisco',
    'F4:AC:C1': 'Cisco',
    'F4:CF:E2': 'Cisco',
    'F4:DB:E6': 'Cisco',
    'F8:0B:CB': 'Cisco',
    'F8:66:D3': 'Cisco',
    'F8:72:EA': 'Cisco',
    'F8:7B:20': 'Cisco',
    'F8:A5:C5': 'Cisco',
    'F8:B7:E2': 'Cisco',
    'FC:5B:39': 'Cisco',
    'FC:99:47': 'Cisco',
    'FC:FB:FB': 'Cisco',
    '00:04:96': 'Dell',
    '00:06:5B': 'Dell',
    '00:08:74': 'Dell',
    '00:0B:DB': 'Dell',
    '00:0D:56': 'Dell',
    '00:0F:1F': 'Dell',
    '00:11:43': 'Dell',
    '00:12:3F': 'Dell',
    '00:13:72': 'Dell',
    '00:14:22': 'Dell',
    '00:15:C5': 'Dell',
    '00:16:F0': 'Dell',
    '00:18:8B': 'Dell',
    '00:19:B9': 'Dell',
    '00:1A:A0': 'Dell',
    '00:1C:23': 'Dell',
    '00:1D:09': 'Dell',
    '00:1E:4F': 'Dell',
    '00:1E:C9': 'Dell',
    '00:21:70': 'Dell',
    '00:21:9B': 'Dell',
    '00:22:19': 'Dell',
    '00:23:AE': 'Dell',
    '00:24:E8': 'Dell',
    '00:25:64': 'Dell',
    '00:26:B9': 'Dell',
    '00:B0:D0': 'Dell',
    '00:C0:4F': 'Dell',
    '00:D0:B7': 'Dell',
    '10:98:36': 'Dell',
    '14:18:77': 'Dell',
    '14:9E:CF': 'Dell',
    '14:B3:1F': 'Dell',
    '14:FE:B5': 'Dell',
    '18:03:73': 'Dell',
    '18:A9:9B': 'Dell',
    '18:DB:F2': 'Dell',
    '18:FB:7B': 'Dell',
    '1C:40:24': 'Dell',
    '20:47:47': 'Dell',
    '24:6E:96': 'Dell',
    '24:B6:FD': 'Dell',
    '28:F1:0E': 'Dell',
    '2C:27:D7': 'Dell',
    '2C:41:38': 'Dell',
    '2C:59:E5': 'Dell',
    '2C:76:8A': 'Dell',
    '34:17:EB': 'Dell',
    '34:E6:AD': 'Dell',
    '38:63:BB': 'Dell',
    '3C:D9:2B': 'Dell',
    '44:A8:42': 'Dell',
    '44:A8:42': 'Dell',
    '50:9A:4C': 'Dell',
    '54:48:E7': 'Dell',
    '54:9F:35': 'Dell',
    '5C:26:0A': 'Dell',
    '5C:F9:DD': 'Dell',
    '64:00:6A': 'Dell',
    '74:86:7A': 'Dell',
    '74:E6:E2': 'Dell',
    '78:2B:CB': 'Dell',
    '78:45:C4': 'Dell',
    '84:2B:2B': 'Dell',
    '84:7B:EB': 'Dell',
    '90:1C:C0': 'Dell',
    '90:B1:1C': 'Dell',
    '98:90:96': 'Dell',
    '9C:B6:54': 'Dell',
    'A0:36:9F': 'Dell',
    'A0:8C:FD': 'Dell',
    'A4:1F:72': 'Dell',
    'A4:BA:DB': 'Dell',
    'B0:83:FE': 'Dell',
    'B8:2A:72': 'Dell',
    'B8:AC:6F': 'Dell',
    'B8:CA:3A': 'Dell',
    'BC:30:5B': 'Dell',
    'C8:1F:66': 'Dell',
    'D0:43:1E': 'Dell',
    'D0:67:26': 'Dell',
    'D4:81:D7': 'Dell',
    'D4:AE:52': 'Dell',
    'D4:BE:D9': 'Dell',
    'E0:DB:55': 'Dell',
    'E4:11:5B': 'Dell',
    'E4:43:4B': 'Dell',
    'E4:F0:04': 'Dell',
    'EC:F4:BB': 'Dell',
    'F0:1F:AF': 'Dell',
    'F0:4D:A2': 'Dell',
    'F4:8E:38': 'Dell',
    'F8:BC:12': 'Dell',
    'F8:CA:B8': 'Dell',
    'F8:DB:88': 'Dell',
    '00:0E:0C': 'HP',
    '00:13:21': 'HP',
    '00:14:38': 'HP',
    '00:14:C2': 'HP',
    '00:15:60': 'HP',
    '00:16:35': 'HP',
    '00:17:08': 'HP',
    '00:17:A4': 'HP',
    '00:18:74': 'HP',
    '00:18:FE': 'HP',
    '00:19:BB': 'HP',
    '00:1A:4B': 'HP',
    '00:1B:78': 'HP',
    '00:1C:2E': 'HP',
    '00:1C:C4': 'HP',
    '00:1E:0B': 'HP',
    '00:1F:29': 'HP',
    '00:21:5A': 'HP',
    '00:22:64': 'HP',
    '00:23:7D': 'HP',
    '00:24:81': 'HP',
    '00:25:B3': 'HP',
    '00:26:55': 'HP',
    '08:00:09': 'HP',
    '08:2E:5F': 'HP',
    '10:00:90': 'HP',
    '10:1F:74': 'HP',
    '10:60:4B': 'HP',
    '10:78:D2': 'HP',
    '14:02:EC': 'HP',
    '14:58:D0': 'HP',
    '18:A9:05': 'HP',
    '1C:98:EC': 'HP',
    '1C:C1:DE': 'HP',
    '20:89:84': 'HP',
    '24:BE:05': 'HP',
    '28:80:23': 'HP',
    '28:92:4A': 'HP',
    '2C:23:3A': 'HP',
    '2C:27:D7': 'HP',
    '2C:41:38': 'HP',
    '2C:44:FD': 'HP',
    '2C:59:E5': 'HP',
    '2C:76:8A': 'HP',
    '30:8D:99': 'HP',
    '30:E1:71': 'HP',
    '34:64:A9': 'HP',
    '38:2C:4A': 'HP',
    '38:63:BB': 'HP',
    '38:EA:A7': 'HP',
    '3C:4A:92': 'HP',
    '3C:D9:2B': 'HP',
    '3C:DF:BD': 'HP',
    '40:A8:F0': 'HP',
    '44:1E:A1': 'HP',
    '44:31:92': 'HP',
    '48:0F:CF': 'HP',
    '4C:39:09': 'HP',
    '50:65:F3': 'HP',
    '54:42:49': 'HP',
    '54:80:28': 'HP',
    '54:EE:75': 'HP',
    '5C:8A:38': 'HP',
    '5C:B9:01': 'HP',
    '60:45:BD': 'HP',
    '60:EB:69': 'HP',
    '64:31:50': 'HP',
    '64:51:06': 'HP',
    '64:80:99': 'HP',
    '68:B5:99': 'HP',
    '6C:3B:E5': 'HP',
    '6C:C2:17': 'HP',
    '70:5A:0F': 'HP',
    '70:B3:17': 'HP',
    '74:DE:2B': 'HP',
    '74:F6:20': 'HP',
    '78:24:AF': 'HP',
    '78:48:59': 'HP',
    '78:AC:C0': 'HP',
    '78:E3:B5': 'HP',
    '78:E7:D1': 'HP',
    '80:C1:6E': 'HP',
    '84:34:97': 'HP',
    '88:51:FB': 'HP',
    '88:9F:FA': 'HP',
    '8C:DC:D4': 'HP',
    '90:B1:1C': 'HP',
    '94:18:82': 'HP',
    '94:57:A5': 'HP',
    '98:4B:E1': 'HP',
    '98:E7:F4': 'HP',
    '9C:2A:70': 'HP',
    '9C:4E:36': 'HP',
    '9C:8E:99': 'HP',
    'A0:1D:48': 'HP',
    'A0:2B:B8': 'HP',
    'A0:48:1C': 'HP',
    'A0:4A:5E': 'HP',
    'A0:8C:FD': 'HP',
    'A0:B3:CC': 'HP',
    'A0:D3:C1': 'HP',
    'A4:4F:29': 'HP',
    'A4:5D:36': 'HP',
    'A4:93:4C': 'HP',
    'A4:BA:DB': 'HP',
    'A8:5E:45': 'HP',
    'AC:16:2D': 'HP',
    'AC:E2:D3': 'HP',
    'B0:5A:DA': 'HP',
    'B0:5C:DA': 'HP',
    'B4:39:D6': 'HP',
    'B4:B5:2F': 'HP',
    'B4:99:BA': 'HP',
    'B8:AC:6F': 'HP',
    'C0:91:34': 'HP',
    'C8:02:10': 'HP',
    'C8:0A:A9': 'HP',
    'C8:CB:B8': 'HP',
    'C8:D3:FF': 'HP',
    'CC:3E:5F': 'HP',
    'D0:7E:28': 'HP',
    'D0:BF:9C': 'HP',
    'D4:85:64': 'HP',
    'D8:9D:67': 'HP',
    'D8:CB:8A': 'HP',
    'D8:D3:85': 'HP',
    'DC:4A:3E': 'HP',
    'E0:3F:49': 'HP',
    'E4:11:5B': 'HP',
    'E4:54:E8': 'HP',
    'EC:8E:B5': 'HP',
    'EC:9A:74': 'HP',
    'F0:1F:AF': 'HP',
    'F0:92:1C': 'HP',
    'F4:30:B9': 'HP',
    'F4:CE:46': 'HP',
    'FC:15:B4': 'HP',
    '00:14:A5': 'Intel',
    '00:15:00': 'Intel',
    '00:15:17': 'Intel',
    '00:15:F2': 'Intel',
    '00:16:6F': 'Intel',
    '00:16:76': 'Intel',
    '00:16:EA': 'Intel',
    '00:16:EB': 'Intel',
    '00:18:DE': 'Intel',
    '00:19:D1': 'Intel',
    '00:19:D2': 'Intel',
    '00:1B:21': 'Intel',
    '00:1B:77': 'Intel',
    '00:1C:BF': 'Intel',
    '00:1D:E0': 'Intel',
    '00:1D:E1': 'Intel',
    '00:1E:64': 'Intel',
    '00:1E:65': 'Intel',
    '00:1E:67': 'Intel',
    '00:1F:3A': 'Intel',
    '00:1F:3B': 'Intel',
    '00:1F:3C': 'Intel',
    '00:21:5C': 'Intel',
    '00:21:5D': 'Intel',
    '00:21:6A': 'Intel',
    '00:22:FA': 'Intel',
    '00:22:FB': 'Intel',
    '00:23:14': 'Intel',
    '00:23:15': 'Intel',
    '00:24:D6': 'Intel',
    '00:24:D7': 'Intel',
    '00:25:D3': 'Intel',
    '00:26:C6': 'Intel',
    '00:26:C7': 'Intel',
    '00:27:0E': 'Intel',
    '00:27:10': 'Intel',
    '00:27:19': 'Intel',
    '00:A0:C9': 'Intel',
    '00:AA:00': 'Intel',
    '00:AA:01': 'Intel',
    '00:AA:02': 'Intel',
    '00:D0:B7': 'Intel',
    '00:E0:18': 'Intel',
    '04:0E:3C': 'Intel',
    '04:7D:7B': 'Intel',
    '08:11:96': 'Intel',
    '08:ED:B9': 'Intel',
    '0C:8B:FD': 'Intel',
    '10:0E:7E': 'Intel',
    '10:3D:1C': 'Intel',
    '10:4A:7D': 'Intel',
    '14:0C:76': 'Intel',
    '18:5E:0F': 'Intel',
    '18:59:33': 'Intel',
    '1C:3A:DE': 'Intel',
    '1C:4B:D6': 'Intel',
    '1C:6F:65': 'Intel',
    '1C:87:2C': 'Intel',
    '20:16:B9': 'Intel',
    '20:2B:20': 'Intel',
    '20:7C:8F': 'Intel',
    '24:4B:81': 'Intel',
    '28:80:88': 'Intel',
    '28:B2:BD': 'Intel',
    '28:C6:8E': 'Intel',
    '2C:27:D7': 'Intel',
    '2C:41:38': 'Intel',
    '2C:44:FD': 'Intel',
    '2C:59:E5': 'Intel',
    '2C:6E:85': 'Intel',
    '2C:8A:72': 'Intel',
    '30:3A:64': 'Intel',
    '34:02:86': 'Intel',
    '34:13:E8': 'Intel',
    '34:DE:1A': 'Intel',
    '34:E6:AD': 'Intel',
    '38:63:BB': 'Intel',
    '3C:A9:F4': 'Intel',
    '3C:D9:2B': 'Intel',
    '40:5B:D8': 'Intel',
    '40:A8:F0': 'Intel',
    '44:37:E6': 'Intel',
    '44:85:00': 'Intel',
    '48:45:20': 'Intel',
    '48:51:B7': 'Intel',
    '4C:60:DE': 'Intel',
    '4C:79:BA': 'Intel',
    '50:3E:AA': 'Intel',
    '54:53:ED': 'Intel',
    '58:91:CF': 'Intel',
    '5C:51:4F': 'Intel',
    '5C:E0:C5': 'Intel',
    '5C:F3:70': 'Intel',
    '5C:F9:DD': 'Intel',
    '60:36:DD': 'Intel',
    '60:57:18': 'Intel',
    '60:67:20': 'Intel',
    '60:6C:66': 'Intel',
    '64:00:6A': 'Intel',
    '64:27:37': 'Intel',
    '64:5A:04': 'Intel',
    '68:05:CA': 'Intel',
    '68:17:29': 'Intel',
    '68:5D:43': 'Intel',
    '6C:29:95': 'Intel',
    '6C:88:14': 'Intel',
    '70:1C:E7': 'Intel',
    '70:54:D2': 'Intel',
    '70:77:81': 'Intel',
    '74:D0:2B': 'Intel',
    '74:E5:0B': 'Intel',
    '74:E6:E2': 'Intel',
    '78:0C:B8': 'Intel',
    '78:24:AF': 'Intel',
    '78:92:9C': 'Intel',
    '7C:7A:91': 'Intel',
    '7C:B0:C2': 'Intel',
    '80:00:0B': 'Intel',
    '80:19:34': 'Intel',
    '80:86:F2': 'Intel',
    '84:3A:4B': 'Intel',
    '88:28:B3': 'Intel',
    '88:53:2E': 'Intel',
    '88:75:98': 'Intel',
    '8C:A9:82': 'Intel',
    '90:48:9A': 'Intel',
    '94:65:9C': 'Intel',
    '94:C6:91': 'Intel',
    '98:40:BB': 'Intel',
    '98:4F:EE': 'Intel',
    '9C:4E:36': 'Intel',
    '9C:B6:54': 'Intel',
    '9C:D2:1E': 'Intel',
    'A0:36:9F': 'Intel',
    'A0:88:B4': 'Intel',
    'A0:A8:CD': 'Intel',
    'A0:C5:89': 'Intel',
    'A4:34:D9': 'Intel',
    'A4:4C:C8': 'Intel',
    'A4:4E:31': 'Intel',
    'A4:BF:01': 'Intel',
    'A4:C4:94': 'Intel',
    'A8:1E:84': 'Intel',
    'AC:7B:A1': 'Intel',
    'AC:E0:10': 'Intel',
    'B0:0C:D1': 'Intel',
    'B4:96:91': 'Intel',
    'B4:B6:86': 'Intel',
    'B8:6B:23': 'Intel',
    'B8:AE:6E': 'Intel',
    'BC:77:37': 'Intel',
    'C4:85:08': 'Intel',
    'C8:0A:A9': 'Intel',
    'C8:CB:B8': 'Intel',
    'CC:0E:7E': 'Intel',
    'CC:3D:82': 'Intel',
    'D0:50:99': 'Intel',
    'D4:3D:7E': 'Intel',
    'D4:81:D7': 'Intel',
    'D4:AE:52': 'Intel',
    'D4:BE:D9': 'Intel',
    'D8:6C:E9': 'Intel',
    'DC:A9:71': 'Intel',
    'E0:9D:31': 'Intel',
    'E0:DB:55': 'Intel',
    'E4:02:9B': 'Intel',
    'E8:6A:64': 'Intel',
    'E8:94:3E': 'Intel',
    'EC:A8:6B': 'Intel',
    'EC:F4:BB': 'Intel',
    'F0:19:AF': 'Intel',
    'F0:1F:AF': 'Intel',
    'F0:4D:A2': 'Intel',
    'F0:76:1C': 'Intel',
    'F0:92:1C': 'Intel',
    'F0:D5:BF': 'Intel',
    'F4:06:16': 'Intel',
    'F4:6D:04': 'Intel',
    'F8:63:3F': 'Intel',
    'F8:BC:12': 'Intel',
    'F8:CA:B8': 'Intel',
    'F8:DB:88': 'Intel',
    '00:05:5D': 'Ubiquiti Networks',
    '00:15:6D': 'Ubiquiti Networks',
    '00:27:22': 'Ubiquiti Networks',
    '04:18:D6': 'Ubiquiti Networks',
    '18:E8:29': 'Ubiquiti Networks',
    '24:A4:3C': 'Ubiquiti Networks',
    '44:D9:E7': 'Ubiquiti Networks',
    '68:72:51': 'Ubiquiti Networks',
    '68:D7:9A': 'Ubiquiti Networks',
    '70:A7:41': 'Ubiquiti Networks',
    '74:83:C2': 'Ubiquiti Networks',
    '74:AC:B9': 'Ubiquiti Networks',
    '78:8A:20': 'Ubiquiti Networks',
    '78:D2:94': 'Ubiquiti Networks',
    '80:2A:A8': 'Ubiquiti Networks',
    '84:D4:7E': 'Ubiquiti Networks',
    'AC:8B:A9': 'Ubiquiti Networks',
    'B4:FB:E4': 'Ubiquiti Networks',
    'D0:21:F9': 'Ubiquiti Networks',
    'DC:9F:DB': 'Ubiquiti Networks',
    'E0:63:DA': 'Ubiquiti Networks',
    'F0:9F:C2': 'Ubiquiti Networks',
    'F4:92:BF': 'Ubiquiti Networks',
    'FC:EC:DA': 'Ubiquiti Networks',
}


def get_mac_from_arp(ip: str) -> Optional[str]:
    """Get MAC address from ARP table for given IP"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                # Parse Windows ARP output
                # Expected format: "  192.168.1.1           aa-bb-cc-dd-ee-ff     dynamic"
                for line in result.stdout.splitlines():
                    if ip in line:
                        # Extract MAC address pattern
                        mac_match = re.search(r'([0-9a-f]{2}[-:]){5}[0-9a-f]{2}', line, re.IGNORECASE)
                        if mac_match:
                            mac = mac_match.group(0).replace('-', ':').upper()
                            return mac
        else:
            # Linux/Unix
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if ip in line:
                        mac_match = re.search(r'([0-9a-f]{2}:){5}[0-9a-f]{2}', line, re.IGNORECASE)
                        if mac_match:
                            return mac_match.group(0).upper()
    except Exception:
        pass
    return None


def get_vendor_from_mac(mac: str) -> str:
    """Get vendor name from MAC address using OUI lookup"""
    if not mac:
        return 'Unknown'

    # Extract first 3 octets (OUI)
    mac_prefix = ':'.join(mac.split(':')[:3]).upper()

    # Look up vendor
    return MAC_VENDORS.get(mac_prefix, 'Unknown')


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
        self.mac_address = None
        self.vendor = None


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

                # Get MAC address and vendor for reachable hosts
                if not result.mac_address:  # Only lookup once
                    result.mac_address = get_mac_from_arp(ip)
                    if result.mac_address:
                        result.vendor = get_vendor_from_mac(result.mac_address)
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

                # Preserve MAC and vendor from previous results if available
                if ip in self.results:
                    if self.results[ip].mac_address and not result.mac_address:
                        result.mac_address = self.results[ip].mac_address
                        result.vendor = self.results[ip].vendor

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
