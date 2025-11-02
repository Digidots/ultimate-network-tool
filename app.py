"""
Ultimate Network Tool - Web Application Backend
Flask server with WebSocket support for real-time updates
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import ctypes
import threading
import time
import asyncio
from logger import get_logger
from network_adapter import NetworkAdapterManager, AdapterInfo
from lldp_cdp_discovery import LLDPCDPDiscovery, DiscoveryResult
from vlan_probe import VLANProber, VLANProbeResult
from modules.mtu_tester import discover_path, test_mtu, MTUTestResult
from modules.ping_monitor import PingMonitor, PingResult

app = Flask(__name__)
app.config['SECRET_KEY'] = 'unt-secret-key-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
logger = get_logger()
adapter_manager = NetworkAdapterManager()
discovery = None
vlan_prober = None
selected_adapter = None
ping_monitor = None


def check_admin():
    """Check admin privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/mtu')
def mtu_simple():
    """Serve working MTU form (copied from MTU_Flask_Simple)"""
    return render_template('mtu_simple_form.html')


@app.route('/mtu-form')
def mtu_form():
    """Serve MTU form page"""
    print("=" * 60)
    print("[ROUTE] /mtu-form accessed")
    print("=" * 60)
    return render_template('mtu_form.html')


@app.route('/mtu-test-minimal')
def mtu_test_minimal():
    """Serve minimal test form"""
    print("=" * 60)
    print("[ROUTE] /mtu-test-minimal accessed")
    print("=" * 60)
    return render_template('mtu_form_minimal.html')


@app.route('/mtu-discover', methods=['POST'])
def mtu_discover():
    """Run MTU discovery and return results"""
    print("="*60)
    print("[MTU-TEST] Route called!")
    print(f"[MTU-TEST] Form data: {request.form}")
    print("="*60)

    target = request.form.get('target', '').strip()

    print(f"[MTU-TEST] Target: '{target}'")

    if not target:
        print("[MTU-TEST] No target provided, returning error")
        return render_template('mtu_simple_form.html', error='Please enter a valid host or IP address')

    try:
        # Phase 1: Discover path
        logger.info(f"Starting MTU discovery to {target}")
        hops = discover_path(target)
        logger.info(f"Discovered {len(hops)} hops")

        # Phase 2: Test MTU for each hop
        results = []
        for i, hop in enumerate(hops, 1):
            hop_ip = hop['ip']
            ttl = hop['ttl']

            logger.info(f"Testing MTU for hop {i}: {hop_ip}")

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
                status = 'Unreachable'
                status_class = 'unreachable'
                status_icon = '❌'
            elif mtu_result.path_mtu >= 1500:
                status = 'Optimal'
                status_class = 'optimal'
                status_icon = '✅'
            else:
                status = 'Reduced'
                status_class = 'reduced'
                status_icon = '⚠️'

            result = {
                'hop': i,
                'ip': hop_ip,
                'hostname': hop.get('hostname', hop_ip),
                'mtu': mtu_result.path_mtu,
                'capacity': mtu_result.hop_capacity,
                'status': status,
                'status_class': status_class
            }

            results.append(result)
            logger.info(f"Hop {i} ({hop_ip}): Path MTU = {mtu_result.path_mtu}B")

        logger.log_action("MTU Discovery Complete", f"Target: {target}, Hops: {len(results)}")
        return render_template('mtu_simple_results.html', results=results, target=target)

    except Exception as e:
        logger.log_exception("MTU Discovery", e)
        return render_template('mtu_simple_form.html', error=str(e))


@app.route('/api/status')
def get_status():
    """Get application status"""
    return jsonify({
        'is_admin': check_admin(),
        'version': '2.0'
    })


@app.route('/api/adapters')
def get_adapters():
    """Get list of network adapters"""
    try:
        adapters = adapter_manager.enumerate_adapters()
        ethernet_adapters = adapter_manager.get_ethernet_adapters()
        display_adapters = ethernet_adapters if ethernet_adapters else adapters

        adapter_list = []
        for adapter in display_adapters:
            adapter_list.append({
                'name': adapter.description,
                'ip': adapter.ip_address or 'N/A',
                'subnet': adapter.subnet_mask or 'N/A',
                'gateway': adapter.gateway or 'N/A',
                'dns': adapter.dns_servers[0] if adapter.dns_servers else 'N/A',
                'dhcp': adapter.dhcp_server or 'N/A',
                'mac': adapter.mac_address or 'N/A'
            })

        return jsonify({'adapters': adapter_list})
    except Exception as e:
        logger.log_exception("get_adapters", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/adapter/<int:index>')
def get_adapter_info(index):
    """Get specific adapter information"""
    try:
        adapters = adapter_manager.enumerate_adapters()
        ethernet_adapters = adapter_manager.get_ethernet_adapters()
        display_adapters = ethernet_adapters if ethernet_adapters else adapters

        if index < len(display_adapters):
            adapter = display_adapters[index]
            global selected_adapter
            selected_adapter = adapter

            return jsonify({
                'name': adapter.description,
                'ip': adapter.ip_address or 'N/A',
                'subnet': adapter.subnet_mask or 'N/A',
                'gateway': adapter.gateway or 'N/A',
                'dns': adapter.dns_servers[0] if adapter.dns_servers else 'N/A',
                'dhcp': adapter.dhcp_server or 'N/A',
                'mac': adapter.mac_address or 'N/A'
            })
        else:
            return jsonify({'error': 'Adapter not found'}), 404
    except Exception as e:
        logger.log_exception("get_adapter_info", e)
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh-ip', methods=['POST'])
def refresh_ip():
    """Refresh IP address using ipconfig /release and /renew"""
    try:
        import subprocess

        if not check_admin():
            return jsonify({'success': False, 'error': 'Administrator privileges required'}), 403

        # Run ipconfig /release
        logger.log_action("IP Refresh", "Running ipconfig /release")
        subprocess.run(['ipconfig', '/release'], capture_output=True, text=True)

        time.sleep(1)

        # Run ipconfig /renew
        logger.log_action("IP Refresh", "Running ipconfig /renew")
        result = subprocess.run(['ipconfig', '/renew'], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            logger.log_action("IP Refresh", "Success")
            return jsonify({'success': True})
        else:
            logger.log_action("IP Refresh", f"Failed: {result.stderr}")
            return jsonify({'success': False, 'error': result.stderr})

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout waiting for DHCP response'})
    except Exception as e:
        logger.log_exception("refresh_ip", e)
        return jsonify({'success': False, 'error': str(e)}), 500


@socketio.on('start_discovery')
def handle_start_discovery(data):
    """Start LLDP/CDP discovery"""
    global discovery, selected_adapter

    if not check_admin():
        emit('error', {'message': 'Administrator privileges required'})
        return

    if not selected_adapter:
        emit('error', {'message': 'No adapter selected'})
        return

    def discovery_callback(result: DiscoveryResult):
        """Send discovery results to frontend"""
        socketio.emit('discovery_result', {
            'protocol': result.protocol,
            'switch_name': result.switch_name or 'N/A',
            'mac_address': result.mac_address or 'N/A',
            'port_id': result.port_id or 'N/A',
            'model': result.model or 'N/A',
            'ip_address': result.ip_address or 'N/A',
            'timestamp': result.timestamp.strftime('%H:%M:%S')
        })

    try:
        discovery = LLDPCDPDiscovery(selected_adapter.description)
        if discovery.start_discovery(discovery_callback):
            emit('discovery_started', {'adapter': selected_adapter.description})
            logger.log_action("Discovery Started (Web)", selected_adapter.description)
        else:
            emit('error', {'message': 'Failed to start discovery'})
    except Exception as e:
        logger.log_exception("start_discovery", e)
        emit('error', {'message': str(e)})


@socketio.on('stop_discovery')
def handle_stop_discovery():
    """Stop LLDP/CDP discovery"""
    global discovery

    if discovery:
        discovery.stop_discovery()
        emit('discovery_stopped')
        logger.log_action("Discovery Stopped (Web)", "")


@socketio.on('start_vlan_probe')
def handle_start_vlan_probe(data):
    """Start VLAN probing"""
    global vlan_prober, selected_adapter

    if not check_admin():
        emit('error', {'message': 'Administrator privileges required'})
        return

    if not selected_adapter:
        emit('error', {'message': 'No adapter selected'})
        return

    vlan_start = data.get('start', 1)
    vlan_end = data.get('end', 100)
    specific_vlans = data.get('specific', None)  # List of specific VLANs

    def vlan_callback(result: VLANProbeResult):
        """Send VLAN results to frontend with DHCP info"""
        socketio.emit('vlan_result', {
            'vlan_id': result.vlan_id,
            'status': result.status,
            'source': result.source,
            'offered_ip': result.offered_ip or 'N/A',
            'subnet_mask': result.subnet_mask or 'N/A',
            'gateway': result.gateway or 'N/A',
            'dhcp_server': result.dhcp_server or 'N/A',
            'ip_range': result.ip_range or 'N/A',
            # Additional DHCP options
            'lease_time': result.lease_time,
            'domain_name': result.domain_name,
            'broadcast_address': result.broadcast_address,
            'vendor_specific': result.vendor_specific,
            'vendor_class': result.vendor_class,
            'tftp_server': result.tftp_server
        })

    def completion_check():
        """Check if VLAN probe is complete"""
        while vlan_prober and vlan_prober.running:
            time.sleep(1)

        # Send completion
        discovered = vlan_prober.get_discovered_vlans() if vlan_prober else []
        socketio.emit('vlan_probe_complete', {
            'total': len(discovered),
            'vlans': discovered
        })

    try:
        vlan_prober = VLANProber(selected_adapter.description)

        # Set specific VLANs or range
        if specific_vlans and isinstance(specific_vlans, list):
            vlan_prober.set_vlan_list(specific_vlans)
            logger.log_action("VLAN Probe Started (Web)", f"Specific: {specific_vlans}")
        else:
            vlan_prober.set_vlan_range(vlan_start, vlan_end)
            logger.log_action("VLAN Probe Started (Web)", f"Range: {vlan_start}-{vlan_end}")

        if vlan_prober.start_probe(vlan_callback):
            emit('vlan_probe_started', {'start': vlan_start, 'end': vlan_end})

            # Start completion checker in background
            threading.Thread(target=completion_check, daemon=True).start()
        else:
            emit('error', {'message': 'Failed to start VLAN probe'})
    except Exception as e:
        logger.log_exception("start_vlan_probe", e)
        emit('error', {'message': str(e)})


@socketio.on('stop_vlan_probe')
def handle_stop_vlan_probe():
    """Stop VLAN probing"""
    global vlan_prober

    if vlan_prober:
        vlan_prober.stop_probe()
        emit('vlan_probe_stopped')
        logger.log_action("VLAN Probe Stopped (Web)", "")


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Web client connected")
    emit('connected', {'status': 'ok'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Web client disconnected")


@app.route('/ping')
def ping():
    """Serve ping monitor page"""
    return render_template('ping.html')


@socketio.on('start_ping')
def handle_start_ping(data):
    """Start ping monitoring"""
    global ping_monitor

    if not check_admin():
        emit('error', {'message': 'Administrator privileges required'})
        return

    def ping_callback(result: PingResult):
        """Send ping results to frontend"""
        socketio.emit('ping_result', {
            'ip': result.ip,
            'hostname': result.hostname,
            'status': result.status,
            'avg_ping_ms': result.avg_ping_ms,
            'min_ping_ms': result.min_ping_ms,
            'max_ping_ms': result.max_ping_ms,
            'packets_sent': result.packets_sent,
            'packets_received': result.packets_received,
            'packet_loss_percent': result.packet_loss_percent,
            'ttl': result.ttl,
            'last_update': result.last_update.isoformat()
        })

    try:
        ping_monitor = PingMonitor()
        ping_monitor.ping_count = data.get('ping_count', 4)
        ping_monitor.timeout = data.get('timeout', 2)
        ping_monitor.continuous = data.get('continuous', False)
        ping_monitor.interval = data.get('interval', 5)

        ips = ping_monitor.parse_input(data.get('input', ''))

        if not ips:
            emit('error', {'message': 'No valid IP addresses found'})
            return

        ping_monitor.start_monitoring(ips, ping_callback)
        emit('ping_started', {'total': len(ips)})
        logger.log_action("Ping Monitor Started (Web)", f"{len(ips)} hosts")

    except Exception as e:
        logger.log_exception("start_ping", e)
        emit('error', {'message': str(e)})


@socketio.on('stop_ping')
def handle_stop_ping():
    """Stop ping monitoring"""
    global ping_monitor

    if ping_monitor:
        ping_monitor.stop_monitoring()
        emit('ping_stopped')
        logger.log_action("Ping Monitor Stopped (Web)", "")


@socketio.on('start_mtu_discovery')
def handle_start_mtu_discovery(data):
    """Start MTU path discovery"""
    target = data.get('target', '')
    protocol = data.get('protocol', 'TCP')
    max_mtu = data.get('maxMtu', 1500)

    if not target:
        emit('mtu_discovery_error', 'Please enter a valid host or IP address')
        return

    def run_mtu_discovery():
        """Run MTU discovery in background thread"""
        try:
            logger.log_action("MTU Discovery Started", f"Target: {target}")

            # Phase 1: Discover path
            socketio.emit('mtu_discovery_status', {
                'step': 'traceroute',
                'message': f'Discovering path to {target}...'
            })

            hops = discover_path(target)

            socketio.emit('mtu_hops_discovered', hops)
            logger.info(f"Discovered {len(hops)} hops to {target}")

            # Phase 2: Test MTU for each hop
            results = []
            for i, hop in enumerate(hops, 1):
                hop_ip = hop['ip']
                ttl = hop['ttl']

                socketio.emit('mtu_discovery_status', {
                    'step': 'mtu-test',
                    'hopNumber': i,
                    'hopIp': hop_ip,
                    'message': f'Testing MTU for hop {i}: {hop_ip}...'
                })

                # Run async MTU test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    mtu_result = loop.run_until_complete(
                        test_mtu(hop_ip, protocol, max_mtu, ttl)
                    )
                finally:
                    loop.close()

                result = {
                    'hop': i,
                    'ip': hop_ip,
                    'hostname': hop.get('hostname', hop_ip),
                    'rtt': hop.get('rtt'),
                    'pathMtu': mtu_result.path_mtu,
                    'hopCapacity': mtu_result.hop_capacity,
                    'status': mtu_result.status,
                    'protocol': mtu_result.protocol
                }

                results.append(result)
                socketio.emit('mtu_hop_result', result)
                logger.info(f"Hop {i} ({hop_ip}): Path MTU = {mtu_result.path_mtu}B")

            # Send completion
            socketio.emit('mtu_discovery_complete', results)
            logger.log_action("MTU Discovery Complete", f"Found {len(results)} hops")

        except Exception as e:
            logger.log_exception("MTU Discovery", e)
            socketio.emit('mtu_discovery_error', str(e))

    # Start discovery in background thread
    threading.Thread(target=run_mtu_discovery, daemon=True).start()


if __name__ == '__main__':
    logger.log_action("Web Application Started", f"Admin: {check_admin()}")
    print("=" * 60)
    print("  Ultimate Network Tool - Web Interface")
    print("=" * 60)
    print(f"  Admin Mode: {'YES' if check_admin() else 'NO (Run as Administrator!)'}")
    print(f"  Server: http://localhost:5000")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server\n")

    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
