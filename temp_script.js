
        // Global state
        let currentResults = [];
        let allResults = []; // Unfiltered results
        let socket = null;
        let graphCanvas, graphCtx;
        let startTime;

        // Initialize
        window.addEventListener('DOMContentLoaded', () => {
            alert('PAGE LOADED! JavaScript is running. File version: 2025-10-19-v2');
            connectWebSocket();
            checkAdminStatus();
            initializeGraph();
        });

        // Connect to WebSocket server
        function connectWebSocket() {
            socket = io();

            socket.on('connect', () => {
                console.log('WebSocket connected');
                addLog('✅', 'Connected to server');
            });

            socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                addLog('⚠️', 'Disconnected from server');
            });

            // Listen for hop results
            socket.on('mtu_hop_result', (result) => {
                console.log('[MTU] Received hop-result event:', result);
                addLog('✅', `Hop ${result.hop}: ${result.ip} - Path MTU: ${result.pathMtu}B, Capacity: ${result.hopCapacity}B`);
                addHopToTable(result.hop, result);
                drawGraph(allResults);
                updateStats(allResults);
            });

            // Listen for discovery complete
            socket.on('mtu_discovery_complete', (results) => {
                console.log('[MTU] Received discovery-complete event:', results);
                addLog('✅', `Discovery complete! Found ${results.length} hops`);
                hideTestingProgress();

                const btn = document.getElementById('startBtn');
                btn.innerHTML = '🚀 Start Discovery';
                btn.disabled = false;

                const duration = Math.round((Date.now() - startTime) / 1000);
                document.getElementById('duration').textContent = `${duration}s`;
            });

            // Listen for discovery errors
            socket.on('mtu_discovery_error', (error) => {
                console.error('[MTU] Received discovery-error event:', error);
                const errorMsg = document.getElementById('errorMsg');
                errorMsg.textContent = `❌ Error: ${error}`;
                errorMsg.classList.add('show');
                addLog('❌', `Error: ${error}`);

                hideTestingProgress();
                const btn = document.getElementById('startBtn');
                btn.innerHTML = '🚀 Start Discovery';
                btn.disabled = false;
            });

            // Listen for discovery status updates
            socket.on('mtu_discovery_status', (status) => {
                console.log('[MTU] Received discovery-status event:', status);
                if (status.step === 'mtu-test') {
                    showTestingProgress(status.hopNumber, status.hopIp, ['Testing...']);
                    addLog('🔍', status.message);
                } else if (status.step === 'traceroute') {
                    addLog('📡', status.message);
                }
            });

            // Listen for hops discovered
            socket.on('mtu_hops_discovered', (hops) => {
                console.log('[MTU] Received hops-discovered event:', hops);
                addLog('✅', `Discovered ${hops.length} hops in path`);
                drawGraph([]);  // Initialize empty graph
            });

            // Listen for direct capacity test result
            socket.on('mtu_direct_capacity_result', (result) => {
                console.log('[MTU] Received direct-capacity-result event:', result);
                addLog('🎯', `Direct capacity test (DF=0) to ${result.targetIp}: ${result.capacity} bytes`);

                // Update the Target Capacity stat card
                const targetCapEl = document.getElementById('targetCapacity');
                if (result.capacity > 0) {
                    targetCapEl.textContent = `${result.capacity} bytes`;
                    targetCapEl.className = result.capacity >= 1500 ? 'stat-value good' : 'stat-value warning';
                
                    targetCapEl.textContent = 'N/A';
                    targetCapEl.className = 'stat-value bad';
                }
            });
        }

        // Protocol info - no longer needed (TCP only)

        // Initialize graph
        function initializeGraph() {
            graphCanvas = document.getElementById('mtuGraph');
            graphCtx = graphCanvas.getContext('2d');
            
            // Set canvas size
            const rect = graphCanvas.getBoundingClientRect();
            graphCanvas.width = rect.width * window.devicePixelRatio;
            graphCanvas.height = rect.height * window.devicePixelRatio;
            graphCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
            
            drawEmptyGraph();
        }

        function drawEmptyGraph() {
            const ctx = graphCtx;
            const width = graphCanvas.width / window.devicePixelRatio;
            const height = graphCanvas.height / window.devicePixelRatio;
            
            ctx.clearRect(0, 0, width, height);
            
            // Draw placeholder text
            ctx.fillStyle = '#64748b';
            ctx.font = '14px "Segoe UI"';
            ctx.textAlign = 'center';
            ctx.fillText('Start discovery to see MTU path graph', width / 2, height / 2);
        }

        function drawGraph(hops) {
            const ctx = graphCtx;
            const width = graphCanvas.width / window.devicePixelRatio;
            const height = graphCanvas.height / window.devicePixelRatio;
            const padding = 60;
            const graphWidth = width - 2 * padding;
            const graphHeight = height - 2 * padding;
            
            ctx.clearRect(0, 0, width, height);
            
            if (hops.length === 0) {
                drawEmptyGraph();
                return;
            }
            
            // Find min/max MTU for scaling
            const mtuValues = hops.map(h => Math.min(h.pathMtu, h.hopCapacity));
            const maxMtu = Math.max(...mtuValues, 1500);
            const minMtu = Math.min(...mtuValues);
            const mtuRange = maxMtu - minMtu || 100;
            
            // Draw grid lines
            ctx.strokeStyle = '#1e293b';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 5; i++) {
                const y = padding + (graphHeight / 5) * i;
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(width - padding, y);
                ctx.stroke();
            }
            
            // Draw Y-axis labels
            ctx.fillStyle = '#64748b';
            ctx.font = '11px "Segoe UI"';
            ctx.textAlign = 'right';
            for (let i = 0; i <= 5; i++) {
                const value = maxMtu - (mtuRange / 5) * i;
                const y = padding + (graphHeight / 5) * i;
                ctx.fillText(Math.round(value), padding - 10, y + 4);
            }
            
            // Y-axis label
            ctx.save();
            ctx.translate(20, height / 2);
            ctx.rotate(-Math.PI / 2);
            ctx.textAlign = 'center';
            ctx.fillText('MTU (bytes)', 0, 0);
            ctx.restore();
            
            // Draw X-axis labels
            ctx.textAlign = 'center';
            const xSpacing = graphWidth / (hops.length - 1 || 1);
            hops.forEach((hop, i) => {
                const x = padding + xSpacing * i;
                ctx.fillText(i + 1, x, height - padding + 20);
            });
            
            // X-axis label
            ctx.fillText('Hop Number', width / 2, height - 10);
            
            // Function to get Y position for MTU value
            const getY = (mtu) => {
                const normalized = (maxMtu - mtu) / mtuRange;
                return padding + graphHeight * normalized;
            };
            
            // Draw line
            ctx.strokeStyle = '#3b82f6';
            ctx.lineWidth = 3;
            ctx.beginPath();
            hops.forEach((hop, i) => {
                const x = padding + xSpacing * i;
                const y = getY(hop.pathMtu);
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            ctx.stroke();
            
            // Draw nodes and labels
            hops.forEach((hop, i) => {
                const x = padding + xSpacing * i;
                const y = getY(hop.pathMtu || 0);  // Handle 0 MTU

                // Node circle - check for unreachable status
                const isUnreachable = hop.pathMtu === 0 || hop.status === 'unreachable';
                const isOptimal = hop.pathMtu >= 1500;

                if (isUnreachable) {
                    ctx.fillStyle = '#ef4444';  // Red for unreachable
                } else if (isOptimal) {
                    ctx.fillStyle = '#10b981';  // Green for optimal
                } else {
                    ctx.fillStyle = '#f59e0b';  // Orange for reduced
                }

                ctx.beginPath();
                ctx.arc(x, y, 8, 0, Math.PI * 2);
                ctx.fill();

                // Node border
                if (isUnreachable) {
                    ctx.strokeStyle = '#f87171';  // Light red border
                } else if (isOptimal) {
                    ctx.strokeStyle = '#34d399';  // Light green border
                } else {
                    ctx.strokeStyle = '#fbbf24';  // Light orange border
                }
                ctx.lineWidth = 2;
                ctx.stroke();

                // MTU label above node
                ctx.fillStyle = '#e2e8f0';
                ctx.font = 'bold 13px "Segoe UI"';
                ctx.textAlign = 'center';
                const label = isUnreachable ? '0' : hop.pathMtu.toString();
                ctx.fillText(label, x, y - 15);
            });
        }

        // Filter functions
        function applyFilters() {
            const pathFilter = document.getElementById('filterPathMtu').value;
            const capFilter = document.getElementById('filterHopCapacity').value;
            const statusFilter = document.getElementById('filterStatus').value;
            
            const rows = document.querySelectorAll('#hopTableBody tr');
            
            rows.forEach(row => {
                const pathMtu = parseInt(row.getAttribute('data-path-mtu'));
                const hopCap = parseInt(row.getAttribute('data-hop-capacity'));
                const status = row.getAttribute('data-status');
                
                let showRow = true;
                
                // Path MTU filter
                if (pathFilter !== 'all') {
                    if (pathFilter === '1500' && pathMtu !== 1500) showRow = false;
                    if (pathFilter === 'lt1500' && pathMtu >= 1500) showRow = false;
                    if (pathFilter === '1472' && pathMtu !== 1472) showRow = false;
                    if (pathFilter === '1400' && pathMtu !== 1400) showRow = false;
                }
                
                // Hop Capacity filter
                if (capFilter !== 'all') {
                    if (capFilter === '1500' && hopCap !== 1500) showRow = false;
                    if (capFilter === 'lt1500' && hopCap >= 1500) showRow = false;
                    if (capFilter === 'gt1500' && hopCap <= 1500) showRow = false;
                }
                
                // Status filter
                if (statusFilter !== 'all') {
                    if (statusFilter !== status) showRow = false;
                }
                
                row.style.display = showRow ? '' : 'none';
            });
        }

        function resetFilters() {
            document.getElementById('filterPathMtu').value = 'all';
            document.getElementById('filterHopCapacity').value = 'all';
            document.getElementById('filterStatus').value = 'all';
            applyFilters();
        }

        // Add log entry
        function addLog(icon, message) {
            const container = document.getElementById('logContainer');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `
                <span class="log-time">${time}</span>
                <span class="log-icon">${icon}</span>
                <span>${message}</span>
            `;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }

        function showTestingProgress(hopNum, ip, sizes) {
            const display = document.getElementById('testingDisplay');
            const info = document.getElementById('testingInfo');
            const progress = document.getElementById('testProgress');
            
            display.style.display = 'block';
            info.textContent = `Hop #${hopNum}: ${ip}`;
            progress.textContent = `Testing: ${sizes.join(' → ')}...`;
        }

        function hideTestingProgress() {
            document.getElementById('testingDisplay').style.display = 'none';
        }

        async function checkAdminStatus() {
            // Admin status check removed - no longer needed for TCP-only mode
            // Status indicator now just shows "Ready"
        }

        function showHelp() {
            document.getElementById('helpModal').classList.add('show');
        }

        function closeHelp() {
            document.getElementById('helpModal').classList.remove('show');
        }

        function startDiscovery() {
            alert('Button clicked! Checking connection...');

            const target = document.getElementById('targetHost').value.trim();
            const protocol = document.getElementById('protocol').value;
            const maxMtu = parseInt(document.getElementById('maxMtu').value);
            const errorMsg = document.getElementById('errorMsg');
            const btn = document.getElementById('startBtn');

            if (!target) {
                errorMsg.textContent = '❌ Error: Please enter a valid host or IP address';
                errorMsg.classList.add('show');
                alert('No target entered!');
                return;
            }

            // Check if socket is connected
            if (!socket) {
                alert('Socket is NULL! WebSocket not initialized.');
                errorMsg.textContent = '❌ Error: WebSocket not initialized. Please refresh the page.';
                errorMsg.classList.add('show');
                return;
            }

            if (!socket.connected) {
                alert('Socket exists but NOT CONNECTED! Connection status: ' + socket.connected);
                errorMsg.textContent = '❌ Error: Not connected to server. Please refresh the page.';
                errorMsg.classList.add('show');
                return;
            }

            alert('Socket connected! Proceeding with discovery...');

            errorMsg.classList.remove('show');
            btn.innerHTML = '<span class="spinner"></span> Discovering...';
            btn.disabled = true;

            currentResults = [];
            allResults = [];
            document.getElementById('hopTableBody').innerHTML = '';
            document.getElementById('logContainer').innerHTML = '';
            resetFilters();

            startTime = Date.now();

            addLog('🚀', `Starting MTU discovery to ${target}...`);
            addLog('📡', `Protocol: ${protocol}, Max MTU: ${maxMtu} bytes`);
            addLog('🔌', `Socket connected: ${socket.connected}, Socket ID: ${socket.id}`);

            // WebSocket backend - results come via events
            try {
                addLog('📤', 'Emitting start_mtu_discovery event...');
                socket.emit('start_mtu_discovery', {target, protocol, maxMtu});
                addLog('✅', 'Event emitted successfully - waiting for results...');
                // Note: We don't await here - results come via event listeners
            } catch (error) {
                alert('ERROR: ' + error.message);
                errorMsg.textContent = `❌ Error: ${error.message}`;
                errorMsg.classList.add('show');
                addLog('❌', `Error: ${error.message}`);
                btn.innerHTML = '🚀 Start Discovery';
                btn.disabled = false;
            }
        }

        async function simulateDiscovery(target, protocol, maxMtu) {
            const demoHops = [
                { ip: '192.168.1.1', hostname: '192.168.1.1', pathMtu: 1500, hopCapacity: 1500 },
                { ip: '10.0.0.1', hostname: '10.0.0.1', pathMtu: 1500, hopCapacity: 1500 },
                { ip: '203.0.113.1', hostname: '203.0.113.1', pathMtu: 1500, hopCapacity: 1500 },
                { ip: '198.51.100.1', hostname: '198.51.100.1', pathMtu: 1472, hopCapacity: 1500 },
                { ip: '192.0.2.1', hostname: '192.0.2.1', pathMtu: 1472, hopCapacity: 1600 },
                { ip: target, hostname: target, pathMtu: 1472, hopCapacity: 1500 }
            ];

            // Initialize empty graph
            drawGraph([]);

            for (let i = 0; i < demoHops.length; i++) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                const hop = demoHops[i];
                addLog('🔍', `Discovering hop ${i + 1}: ${hop.ip}`);
                
                // Show testing progress
                showTestingProgress(i + 1, hop.ip, ['1500B', '1472B', '1450B']);
                await new Promise(resolve => setTimeout(resolve, 500));
                
                addLog('📊', `Testing Path MTU (DF=1): ${hop.pathMtu} bytes`);
                await new Promise(resolve => setTimeout(resolve, 300));
                
                addLog('📊', `Testing Hop Capacity (DF=0): ${hop.hopCapacity} bytes`);
                await new Promise(resolve => setTimeout(resolve, 300));
                
                addHopToTable(i + 1, hop);
                drawGraph(demoHops.slice(0, i + 1));
                updateStats(demoHops.slice(0, i + 1));
            }

            addLog('✅', 'Discovery complete!');
        }

        function addHopToTable(hopNumber, hopData) {
            const tbody = document.getElementById('hopTableBody');
            const row = document.createElement('tr');

            // Check if hop is unreachable first
            const isUnreachable = hopData.pathMtu === 0 || hopData.status === 'unreachable';

            let pathClass, capClass, status, statusClass, statusIcon;

            if (isUnreachable) {
                pathClass = 'reduced';
                capClass = 'reduced';
                status = 'Unreachable';
                statusClass = 'unreachable';
                statusIcon = '❌';
            
                pathClass = hopData.pathMtu >= 1500 ? 'optimal' : 'reduced';
                capClass = hopData.hopCapacity >= 1500 ? 'optimal' : 'reduced';

                if (hopData.pathMtu === hopData.hopCapacity) {
                    if (hopData.pathMtu >= 1500) {
                        status = 'Optimal';
                        statusClass = 'optimal';
                        statusIcon = '✅';
                    } else {
                        status = 'Reduced';
                        statusClass = 'reduced';
                        statusIcon = '⚠️';
                    }
                } else {
                    status = 'Path Limited';
                    statusClass = 'reduced';
                    statusIcon = '⚠️';
                }
            }

            row.setAttribute('data-path-mtu', hopData.pathMtu);
            row.setAttribute('data-hop-capacity', hopData.hopCapacity);
            row.setAttribute('data-status', statusClass);
            
            const pathMtuDisplay = isUnreachable ? 'N/A' : `${hopData.pathMtu} bytes`;
            const hopCapDisplay = isUnreachable ? 'N/A' : `${hopData.hopCapacity} bytes`;
            const pathBadgeClass = isUnreachable ? 'unreachable' : pathClass;
            const capBadgeClass = isUnreachable ? 'unreachable' : capClass;

            row.innerHTML = `
                <td class="hop-number">#${hopNumber}</td>
                <td class="hostname">${hopData.hostname}</td>
                <td class="ip-address">${hopData.ip}</td>
                <td><span class="mtu-badge ${pathBadgeClass}">${pathMtuDisplay}</span></td>
                <td><span class="mtu-badge ${capBadgeClass}">${hopCapDisplay}</span></td>
                <td><span class="status-badge ${statusClass}">${statusIcon} ${status}</span></td>
            `;
            
            tbody.appendChild(row);
            currentResults.push({ hop: hopNumber, ...hopData });
            allResults.push({ hop: hopNumber, ...hopData });
        }

        function updateStats(hops) {
            document.getElementById('totalHops').textContent = hops.length;

            // Filter out unreachable hops for stats
            const reachableHops = hops.filter(h => h.pathMtu > 0);

            if (reachableHops.length === 0) {
                document.getElementById('lowestMtu').textContent = 'N/A';
                document.getElementById('lowestMtu').className = 'stat-value bad';
                document.getElementById('bottleneck').textContent = 'All Unreachable';
                return;
            }

            const minMtu = Math.min(...reachableHops.map(h => h.pathMtu));
            document.getElementById('lowestMtu').textContent = `${minMtu} bytes`;
            document.getElementById('lowestMtu').className = minMtu >= 1500 ? 'stat-value good' : (minMtu > 0 ? 'stat-value warning' : 'stat-value bad');

            const bottleneckIndex = hops.findIndex(h => h.pathMtu === minMtu && h.pathMtu > 0);
            document.getElementById('bottleneck').textContent = bottleneckIndex >= 0 ? `Hop #${bottleneckIndex + 1}` : 'None';
        }

        function exportCSV() {
            if (allResults.length === 0) {
                alert('No data to export. Please run a discovery first.');
                return;
            }
            const csv = 'Hop,Hostname,IP,Path MTU,Hop Capacity,Status\n' +
                allResults.map(r => `${r.hop},${r.hostname},${r.ip},${r.pathMtu},${r.hopCapacity},${r.pathMtu >= 1500 ? 'Optimal' : 'Reduced'}`).join('\n');
            downloadFile(csv, 'mtu-discovery.csv', 'text/csv');
        }

        function exportJSON() {
            if (allResults.length === 0) {
                alert('No data to export. Please run a discovery first.');
                return;
            }
            downloadFile(JSON.stringify(allResults, null, 2), 'mtu-discovery.json', 'application/json');
        }

        function printReport() {
            window.print();
        }

        function downloadFile(content, filename, mimeType) {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            link.click();
            URL.revokeObjectURL(url);
        }

        document.getElementById('helpModal').addEventListener('click', function(e) {
            if (e.target === this) closeHelp();
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            initializeGraph();
            if (allResults.length > 0) {
                drawGraph(allResults);
            }
        });

        // ===== HAMBURGER MENU =====
        function toggleMenu() {
            const menu = document.getElementById('navMenu');
            const overlay = document.getElementById('menuOverlay');
            const hamburger = document.getElementById('hamburgerBtn');

            menu.classList.toggle('active');
            overlay.classList.toggle('active');
            hamburger.classList.toggle('active');
        }

        // ===== NAVIGATION =====
        function navigateTo(page) {
            if (page === 'dashboard') {
                toggleMenu(); // Close menu
                window.location.href = '/';
            } else if (page === 'mtu-tester') {
                toggleMenu(); // Close menu
                // Already on this page, just show a message in console
                console.log('Already on MTU Tester page');
            } else {
                // Coming soon pages
                console.log('This module is coming soon');
            }
        }
    