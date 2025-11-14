# Ultimate Network Tool - API Reference

**Version:** 1.0.0

## REST API Endpoints

### Application Status

#### `GET /api/status`
Returns application status and privilege level.

**Response:**
```json
{
  "is_admin": true,
  "version": "2.0"
}
```

### Network Adapters

#### `GET /api/adapters`
Lists all network adapters (Ethernet adapters prioritized).

**Response:**
```json
{
  "adapters": [
    {
      "name": "Ethernet",
      "ip": "192.168.1.100",
      "subnet": "255.255.255.0",
      "gateway": "192.168.1.1",
      "dns": "8.8.8.8",
      "dhcp": "192.168.1.1",
      "mac": "00:11:22:33:44:55"
    }
  ]
}
```

#### `GET /api/adapter/<index>`
Get specific adapter details by index.

**Response:**
```json
{
  "name": "Ethernet",
  "ip": "192.168.1.100",
  "subnet": "255.255.255.0",
  "gateway": "192.168.1.1",
  "dns": "8.8.8.8",
  "dhcp": "192.168.1.1",
  "mac": "00:11:22:33:44:55"
}
```

**Errors:**
- `404` - Adapter not found

#### `POST /api/refresh-ip`
Release and renew DHCP lease (requires admin).

**Response:**
```json
{
  "success": true
}
```

**Errors:**
- `403` - Admin privileges required
- `500` - Timeout or error

---

## WebSocket Events

### Connection

#### `connect`
Client connects to server.

**Emitted by server:**
```json
{
  "status": "ok"
}
```

#### `disconnect`
Client disconnects.

---

### LLDP/CDP Discovery

#### `start_discovery` (client → server)
Start passive LLDP/CDP listening.

**Payload:** `{}`

**Server emits:**
- `discovery_started` - Discovery initiated
- `discovery_result` - Each time a switch is detected
- `error` - On failure

#### `discovery_result` (server → client)
LLDP/CDP frame captured.

**Payload:**
```json
{
  "protocol": "LLDP",
  "switch_name": "switch-core-01",
  "mac_address": "00:11:22:33:44:55",
  "port_id": "Gi1/0/24",
  "model": "Cisco Catalyst 2960",
  "ip_address": "10.0.0.1",
  "timestamp": "14:32:10"
}
```

#### `stop_discovery` (client → server)
Stop LLDP/CDP discovery.

**Server emits:**
- `discovery_stopped`

---

### VLAN Probing

#### `start_vlan_probe` (client → server)
Start active VLAN probing.

**Payload:**
```json
{
  "start": 1,
  "end": 100,
  "specific": [1, 10, 20, 300]  // Optional: specific VLANs
}
```

**Server emits:**
- `vlan_probe_started` - Probe initiated
- `vlan_result` - Each VLAN discovered
- `vlan_probe_complete` - All VLANs tested
- `error` - On failure

#### `vlan_result` (server → client)
VLAN detected with network info.

**Payload:**
```json
{
  "vlan_id": 300,
  "status": "active",
  "source": "dhcp",
  "offered_ip": "10.30.0.100",
  "subnet_mask": "255.255.0.0",
  "gateway": "10.30.0.1",
  "dhcp_server": "10.30.0.10",
  "ip_range": "10.30.0.0/16",
  "lease_time": 86400,
  "domain_name": "example.com",
  "broadcast_address": "10.30.255.255",
  "vendor_specific": null,
  "vendor_class": null,
  "tftp_server": null
}
```

#### `vlan_probe_complete` (server → client)
All VLANs tested.

**Payload:**
```json
{
  "total": 5,
  "vlans": [1, 10, 20, 100, 300]
}
```

#### `stop_vlan_probe` (client → server)
Stop VLAN probing.

**Server emits:**
- `vlan_probe_stopped`

---

### Ping Monitor

#### `start_ping` (client → server)
Start ping monitoring for multiple hosts.

**Payload:**
```json
{
  "input": "8.8.8.8, google.com, 192.168.1.1-192.168.1.10",
  "ping_count": 4,
  "timeout": 2,
  "continuous": false,
  "interval": 5
}
```

**Server emits:**
- `ping_started` - Monitor initiated
- `ping_result` - Each host result
- `error` - On failure

#### `ping_result` (server → client)
Ping statistics for a host.

**Payload:**
```json
{
  "ip": "8.8.8.8",
  "hostname": "dns.google",
  "status": "reachable",
  "avg_ping_ms": 12.5,
  "min_ping_ms": 10.2,
  "max_ping_ms": 15.8,
  "packets_sent": 4,
  "packets_received": 4,
  "packet_loss_percent": 0.0,
  "ttl": 117,
  "last_update": "2025-11-14T14:30:00Z"
}
```

#### `stop_ping` (client → server)
Stop ping monitoring.

**Server emits:**
- `ping_stopped`

---

### MTU Discovery

#### `start_mtu_discovery` (client → server)
Discover path MTU to target.

**Payload:**
```json
{
  "target": "google.com",
  "protocol": "TCP",
  "maxMtu": 1500
}
```

**Server emits:**
- `mtu_discovery_status` - Progress updates
- `mtu_hops_discovered` - Path discovered
- `mtu_hop_result` - Each hop tested
- `mtu_discovery_complete` - All hops tested
- `mtu_discovery_error` - On failure

#### `mtu_discovery_status` (server → client)
Status update during discovery.

**Payload:**
```json
{
  "step": "traceroute",
  "message": "Discovering path to google.com..."
}
```

or

```json
{
  "step": "mtu-test",
  "hopNumber": 3,
  "hopIp": "172.16.0.1",
  "message": "Testing MTU for hop 3: 172.16.0.1..."
}
```

#### `mtu_hops_discovered` (server → client)
Traceroute path discovered.

**Payload:**
```json
[
  {"ip": "192.168.1.1", "hostname": "router.local", "ttl": 1, "rtt": 1.2},
  {"ip": "10.0.0.1", "hostname": "gateway", "ttl": 2, "rtt": 5.8},
  {"ip": "8.8.8.8", "hostname": "dns.google", "ttl": 3, "rtt": 12.3}
]
```

#### `mtu_hop_result` (server → client)
MTU test result for a hop.

**Payload:**
```json
{
  "hop": 1,
  "ip": "192.168.1.1",
  "hostname": "router.local",
  "rtt": 1.2,
  "pathMtu": 1500,
  "hopCapacity": 1500,
  "status": "optimal",
  "protocol": "TCP"
}
```

#### `mtu_discovery_complete` (server → client)
All hops tested.

**Payload:**
```json
[
  {
    "hop": 1,
    "ip": "192.168.1.1",
    "hostname": "router.local",
    "rtt": 1.2,
    "pathMtu": 1500,
    "hopCapacity": 1500,
    "status": "optimal",
    "protocol": "TCP"
  }
]
```

---

## Error Responses

### WebSocket Errors

**Event:** `error`

**Payload:**
```json
{
  "message": "Administrator privileges required"
}
```

Common error messages:
- `"Administrator privileges required"`
- `"No adapter selected"`
- `"Failed to start discovery"`
- `"Failed to start VLAN probe"`
- `"No valid IP addresses found"`

---

## Data Types

### DiscoveryResult
```python
@dataclass
class DiscoveryResult:
    protocol: str        # "LLDP" or "CDP"
    switch_name: str
    mac_address: str
    port_id: str
    model: str
    ip_address: str
    timestamp: datetime
```

### VLANProbeResult
```python
@dataclass
class VLANProbeResult:
    vlan_id: int
    status: str          # "active", "detected", etc.
    source: str          # "dhcp", "passive"
    offered_ip: str
    subnet_mask: str
    gateway: str
    dhcp_server: str
    ip_range: str
    lease_time: int
    domain_name: str
    broadcast_address: str
    vendor_specific: str
    vendor_class: str
    tftp_server: str
```

### PingResult
```python
@dataclass
class PingResult:
    ip: str
    hostname: str
    status: str          # "reachable", "unreachable"
    avg_ping_ms: float
    min_ping_ms: float
    max_ping_ms: float
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    ttl: int
    last_update: datetime
```

### MTUTestResult
```python
@dataclass
class MTUTestResult:
    path_mtu: int        # Maximum MTU for path
    hop_capacity: int    # Interface capacity
    status: str          # "optimal", "reduced", "unreachable"
    protocol: str        # "TCP", "UDP", "ICMP"
```

---

## Example Client Code

### JavaScript (WebSocket)

```javascript
const socket = io('http://localhost:5000');

// Start VLAN probe
socket.emit('start_vlan_probe', {
  start: 1,
  end: 100
});

// Listen for results
socket.on('vlan_result', (data) => {
  console.log(`VLAN ${data.vlan_id}: ${data.ip_range}`);
});

socket.on('vlan_probe_complete', (data) => {
  console.log(`Discovered ${data.total} VLANs`);
});
```

### Python (REST)

```python
import requests

# Get status
response = requests.get('http://localhost:5000/api/status')
print(response.json())

# Get adapters
response = requests.get('http://localhost:5000/api/adapters')
adapters = response.json()['adapters']
```

---

**See also:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [USER_GUIDE.md](USER_GUIDE.md) - End-user documentation
