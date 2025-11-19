"""
Ultimate Network Tool (UNT) - Final Production Version
Modern web-app style network discovery tool
"""

import tkinter as tk
from tkinter import ttk
import ctypes
import subprocess
import threading
from datetime import datetime
from logger import get_logger
from network_adapter import NetworkAdapterManager, AdapterInfo
from lldp_cdp_discovery import LLDPCDPDiscovery, DiscoveryResult
from vlan_probe import VLANProber, VLANProbeResult


class Notification(tk.Frame):
    """In-app notification banner"""
    def __init__(self, parent, message, type="info"):
        super().__init__(parent, bg='#10b981' if type == 'success' else '#3b82f6', height=40)

        colors = {
            'success': '#10b981',
            'error': '#ef4444',
            'info': '#3b82f6',
            'warning': '#f59e0b'
        }

        self.configure(bg=colors.get(type, '#3b82f6'))

        tk.Label(
            self,
            text=message,
            font=('Segoe UI', 10),
            bg=colors.get(type, '#3b82f6'),
            fg='white'
        ).pack(pady=10)

        # Auto-hide after 3 seconds
        self.after(3000, self.destroy)


class InfoCard(tk.Frame):
    """Modern info card with label and value"""
    def __init__(self, parent, label, value="", **kwargs):
        super().__init__(parent, bg='#1e293b', **kwargs)
        self.configure(highlightbackground='#334155', highlightthickness=1, bd=0)

        inner = tk.Frame(self, bg='#1e293b')
        inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        tk.Label(
            inner,
            text=label,
            font=('Segoe UI', 9, 'bold'),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(anchor=tk.W)

        self.value_label = tk.Label(
            inner,
            text=value or 'N/A',
            font=('Segoe UI', 14, 'bold'),
            bg='#1e293b',
            fg='#60a5fa',
            wraplength=250
        )
        self.value_label.pack(anchor=tk.W, pady=(5, 0))

    def set_value(self, value):
        """Update the value"""
        self.value_label.config(text=value or 'N/A')


class UNTApp:
    """Modern production-ready application"""

    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Network Tool")
        self.root.geometry("1600x900")
        self.root.resizable(True, True)
        self.root.configure(bg='#0f172a')

        # Initialize
        self.logger = get_logger()
        self.adapter_manager = NetworkAdapterManager()
        self.discovery = None
        self.vlan_prober = None
        self.selected_adapter = None

        # VLAN tracking
        self.native_vlan = None
        self.tagged_vlans = set()

        # Discovery cards
        self.switch_cards = {}

        # Check admin
        self.is_admin = self._check_admin()

        # Build GUI
        self._build_gui()

        # Load adapters
        self._load_adapters()

        self.logger.log_action("Application Started", f"Admin: {self.is_admin}")

    def _check_admin(self) -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _show_notification(self, message, type="info"):
        """Show in-app notification"""
        notif = Notification(self.notification_area, message, type)
        notif.pack(fill=tk.X, pady=2)

    def _build_gui(self):
        """Build modern web-app style GUI"""

        # Header
        header = tk.Frame(self.root, bg='#1e293b', height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg='#1e293b')
        header_inner.pack(fill=tk.BOTH, padx=30, pady=20)

        # Title
        tk.Label(
            header_inner,
            text="🔍 Ultimate Network Tool",
            font=('Segoe UI', 22, 'bold'),
            bg='#1e293b',
            fg='#60a5fa'
        ).pack(side=tk.LEFT)

        # Admin badge
        admin_color = '#10b981' if self.is_admin else '#ef4444'
        admin_bg = tk.Frame(header_inner, bg=admin_color, padx=12, pady=6)
        admin_bg.pack(side=tk.RIGHT)

        tk.Label(
            admin_bg,
            text="● ADMINISTRATOR" if self.is_admin else "● USER MODE",
            font=('Segoe UI', 9, 'bold'),
            bg=admin_color,
            fg='white'
        ).pack()

        # Notification area
        self.notification_area = tk.Frame(self.root, bg='#0f172a')
        self.notification_area.pack(fill=tk.X, padx=20)

        # Main container
        main = tk.Frame(self.root, bg='#0f172a')
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Adapter bar
        adapter_bar = tk.Frame(main, bg='#1e293b', height=60)
        adapter_bar.pack(fill=tk.X, pady=(0, 20))
        adapter_bar.pack_propagate(False)

        adapter_inner = tk.Frame(adapter_bar, bg='#1e293b')
        adapter_inner.pack(fill=tk.X, padx=20, pady=12)

        tk.Label(
            adapter_inner,
            text="Network Adapter",
            font=('Segoe UI', 10, 'bold'),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.adapter_combo = ttk.Combobox(
            adapter_inner,
            state="readonly",
            font=('Segoe UI', 10),
            width=65
        )
        self.adapter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.adapter_combo.bind("<<ComboboxSelected>>", self._on_adapter_selected)

        # Refresh button
        tk.Button(
            adapter_inner,
            text="🔄 Refresh",
            command=self._refresh_adapter,
            bg='#3b82f6',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2',
            bd=0
        ).pack(side=tk.LEFT, padx=5)

        # Content grid
        content = tk.Frame(main, bg='#0f172a')
        content.pack(fill=tk.BOTH, expand=True)

        # Left column (60%)
        left = tk.Frame(content, bg='#0f172a')
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        # Right column (40%)
        right = tk.Frame(content, bg='#0f172a', width=550)
        right.pack(side=tk.RIGHT, fill=tk.BOTH)
        right.pack_propagate(False)

        # === LEFT COLUMN ===

        # Adapter info cards grid
        info_grid_label = tk.Label(
            left,
            text="ADAPTER INFORMATION",
            font=('Segoe UI', 11, 'bold'),
            bg='#0f172a',
            fg='#60a5fa'
        )
        info_grid_label.pack(anchor=tk.W, pady=(0, 10))

        info_grid = tk.Frame(left, bg='#0f172a')
        info_grid.pack(fill=tk.X, pady=(0, 20))

        # Create 2x3 grid of info cards
        self.info_cards = {}

        row1 = tk.Frame(info_grid, bg='#0f172a')
        row1.pack(fill=tk.X, pady=(0, 10))

        self.info_cards['ip'] = InfoCard(row1, "IP Address")
        self.info_cards['ip'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.info_cards['subnet'] = InfoCard(row1, "Subnet Mask")
        self.info_cards['subnet'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.info_cards['gateway'] = InfoCard(row1, "Gateway")
        self.info_cards['gateway'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        row2 = tk.Frame(info_grid, bg='#0f172a')
        row2.pack(fill=tk.X)

        self.info_cards['dns'] = InfoCard(row2, "DNS Server")
        self.info_cards['dns'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.info_cards['dhcp'] = InfoCard(row2, "DHCP Server")
        self.info_cards['dhcp'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.info_cards['mac'] = InfoCard(row2, "MAC Address")
        self.info_cards['mac'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Switch Discovery section
        discovery_header = tk.Frame(left, bg='#0f172a')
        discovery_header.pack(fill=tk.X, pady=(20, 10))

        tk.Label(
            discovery_header,
            text="SWITCH DISCOVERY",
            font=('Segoe UI', 11, 'bold'),
            bg='#0f172a',
            fg='#60a5fa'
        ).pack(side=tk.LEFT)

        self.discover_btn = tk.Button(
            discovery_header,
            text="▶  Start",
            command=self._start_discovery,
            bg='#10b981',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=6,
            cursor='hand2',
            bd=0
        )
        self.discover_btn.pack(side=tk.RIGHT)

        # Switch info cards container
        self.switch_container = tk.Frame(left, bg='#0f172a')
        self.switch_container.pack(fill=tk.BOTH, expand=True)

        # === RIGHT COLUMN ===

        # VLAN Detection header
        vlan_header = tk.Frame(right, bg='#0f172a')
        vlan_header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            vlan_header,
            text="VLAN DETECTION",
            font=('Segoe UI', 11, 'bold'),
            bg='#0f172a',
            fg='#60a5fa'
        ).pack(side=tk.LEFT)

        # VLAN range
        range_frame = tk.Frame(vlan_header, bg='#0f172a')
        range_frame.pack(side=tk.RIGHT)

        self.vlan_start_entry = tk.Entry(
            range_frame,
            font=('Segoe UI', 9),
            width=5,
            bg='#1e293b',
            fg='#e2e8f0',
            bd=1,
            relief=tk.SOLID,
            insertbackground='#60a5fa'
        )
        self.vlan_start_entry.insert(0, "1")
        self.vlan_start_entry.pack(side=tk.LEFT, padx=3)

        tk.Label(range_frame, text="-", bg='#0f172a', fg='#94a3b8').pack(side=tk.LEFT)

        self.vlan_end_entry = tk.Entry(
            range_frame,
            font=('Segoe UI', 9),
            width=5,
            bg='#1e293b',
            fg='#e2e8f0',
            bd=1,
            relief=tk.SOLID,
            insertbackground='#60a5fa'
        )
        self.vlan_end_entry.insert(0, "100")
        self.vlan_end_entry.pack(side=tk.LEFT, padx=3)

        self.vlan_btn = tk.Button(
            range_frame,
            text="▶  Scan",
            command=self._start_vlan_probe,
            bg='#8b5cf6',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=6,
            cursor='hand2',
            bd=0
        )
        self.vlan_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Native VLAN card
        native_card = InfoCard(right, "NATIVE / UNTAGGED VLAN", "Not detected")
        native_card.pack(fill=tk.X, pady=(0, 15))
        self.native_vlan_card = native_card

        # Tagged VLANs
        tk.Label(
            right,
            text="TAGGED VLANS",
            font=('Segoe UI', 10, 'bold'),
            bg='#0f172a',
            fg='#94a3b8'
        ).pack(anchor=tk.W, pady=(0, 10))

        tagged_container = tk.Frame(right, bg='#1e293b', highlightbackground='#334155', highlightthickness=1)
        tagged_container.pack(fill=tk.BOTH, expand=True)

        self.tagged_vlans_container = tk.Frame(tagged_container, bg='#1e293b')
        self.tagged_vlans_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.tagged_placeholder = tk.Label(
            self.tagged_vlans_container,
            text="No tagged VLANs detected",
            font=('Segoe UI', 10),
            bg='#1e293b',
            fg='#64748b'
        )
        self.tagged_placeholder.pack(pady=20)

        # Footer
        footer = tk.Frame(self.root, bg='#1e293b', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="Copyright © Digidots 2025",
            font=('Segoe UI', 9),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(side=tk.LEFT, padx=20, pady=10)

    def _load_adapters(self):
        adapters = self.adapter_manager.enumerate_adapters()
        if not adapters:
            self._show_notification("No network adapters found", "warning")
            return

        ethernet_adapters = self.adapter_manager.get_ethernet_adapters()
        display_adapters = ethernet_adapters if ethernet_adapters else adapters

        adapter_names = [str(adapter) for adapter in display_adapters]
        self.adapter_combo['values'] = adapter_names

        if adapter_names:
            self.adapter_combo.current(0)
            self._on_adapter_selected(None)

    def _on_adapter_selected(self, event):
        selection = self.adapter_combo.get()
        if not selection:
            return

        for adapter in self.adapter_manager.adapters:
            if str(adapter) == selection:
                self.selected_adapter = adapter
                self._display_adapter_info(adapter)
                self.logger.log_action("Adapter Selected", adapter.description)
                break

    def _display_adapter_info(self, adapter: AdapterInfo):
        """Display adapter info in modern cards"""
        self.info_cards['ip'].set_value(adapter.ip_address or 'N/A')
        self.info_cards['subnet'].set_value(adapter.subnet_mask or 'N/A')
        self.info_cards['gateway'].set_value(adapter.gateway or 'N/A')
        self.info_cards['dns'].set_value(adapter.dns_servers[0] if adapter.dns_servers else 'N/A')
        self.info_cards['dhcp'].set_value(adapter.dhcp_server or 'N/A')
        self.info_cards['mac'].set_value(adapter.mac_address or 'N/A')

    def _refresh_adapter(self):
        if not self.selected_adapter:
            self._show_notification("Please select a network adapter", "warning")
            return

        if not self.is_admin:
            self._show_notification("Administrator privileges required", "error")
            return

        self.logger.log_action("Refresh IP", self.selected_adapter.description)

        def do_refresh():
            try:
                subprocess.run(['ipconfig', '/release'], capture_output=True, timeout=10)
                subprocess.run(['ipconfig', '/renew'], capture_output=True, timeout=30)

                self.root.after(0, self._load_adapters)
                self.root.after(0, lambda: self._show_notification("IP address renewed successfully", "success"))
            except Exception as e:
                self.logger.log_exception("refresh_adapter", e)
                self.root.after(0, lambda: self._show_notification(f"Failed to refresh: {str(e)}", "error"))

        threading.Thread(target=do_refresh, daemon=True).start()
        self._show_notification("Renewing IP address...", "info")

    def _start_discovery(self):
        if not self.selected_adapter:
            self._show_notification("Please select a network adapter", "warning")
            return

        if not self.is_admin:
            self._show_notification("Administrator privileges required for packet capture", "error")
            return

        if self.discovery and self.discovery.running:
            self.discovery.stop_discovery()
            self.discover_btn.config(text="▶  Start", bg='#10b981')
            self._show_notification("Discovery stopped", "info")
            return

        # Clear previous results
        for widget in self.switch_container.winfo_children():
            widget.destroy()
        self.switch_cards.clear()

        self.discovery = LLDPCDPDiscovery(self.selected_adapter.description)
        if self.discovery.start_discovery(self._on_discovery_result):
            self.discover_btn.config(text="■  Stop", bg='#ef4444')
            self._show_notification("Discovery started", "success")
        else:
            self._show_notification("Failed to start discovery", "error")

    def _on_discovery_result(self, result: DiscoveryResult):
        self.root.after(0, self._display_discovery_result, result)

    def _display_discovery_result(self, result: DiscoveryResult):
        """Display discovery in modern separate cards"""

        # Create unique key
        key = f"{result.switch_name}_{result.port_id}"

        # Update existing or create new
        if key in self.switch_cards:
            cards = self.switch_cards[key]
        else:
            # Create card container
            container = tk.Frame(self.switch_container, bg='#0f172a')
            container.pack(fill=tk.X, pady=(0, 15))

            # Protocol badge
            protocol_color = '#3b82f6' if result.protocol == 'LLDP' else '#f59e0b'
            badge = tk.Frame(container, bg=protocol_color, padx=10, pady=4)
            badge.pack(anchor=tk.W, pady=(0, 10))

            tk.Label(
                badge,
                text=result.protocol,
                font=('Segoe UI', 8, 'bold'),
                bg=protocol_color,
                fg='white'
            ).pack()

            # Info cards grid (2x2)
            grid = tk.Frame(container, bg='#0f172a')
            grid.pack(fill=tk.X)

            row1 = tk.Frame(grid, bg='#0f172a')
            row1.pack(fill=tk.X, pady=(0, 10))

            card_switch = InfoCard(row1, "Switch Name", result.switch_name or 'N/A')
            card_switch.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

            card_port = InfoCard(row1, "Port", result.port_id or 'N/A')
            card_port.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            row2 = tk.Frame(grid, bg='#0f172a')
            row2.pack(fill=tk.X)

            card_model = InfoCard(row2, "Model", result.model or 'N/A')
            card_model.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

            card_ip = InfoCard(row2, "Switch IP", result.vendor or 'N/A')
            card_ip.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            self.switch_cards[key] = {
                'switch': card_switch,
                'port': card_port,
                'model': card_model,
                'ip': card_ip
            }

    def _start_vlan_probe(self):
        if not self.selected_adapter:
            self._show_notification("Please select a network adapter", "warning")
            return

        if not self.is_admin:
            self._show_notification("Administrator privileges required", "error")
            return

        if self.vlan_prober and self.vlan_prober.running:
            self.vlan_prober.stop_probe()
            self.vlan_btn.config(text="▶  Scan", bg='#8b5cf6')
            return

        try:
            vlan_start = int(self.vlan_start_entry.get())
            vlan_end = int(self.vlan_end_entry.get())
        except ValueError:
            self._show_notification("Invalid VLAN range", "error")
            return

        # Reset
        self.native_vlan = None
        self.tagged_vlans.clear()
        self.native_vlan_card.set_value("Scanning...")

        for widget in self.tagged_vlans_container.winfo_children():
            widget.destroy()

        self.vlan_prober = VLANProber(self.selected_adapter.description)
        self.vlan_prober.set_vlan_range(vlan_start, vlan_end)

        if self.vlan_prober.start_probe(self._on_vlan_result):
            self.vlan_btn.config(text="■  Stop", bg='#ef4444')
            self._show_notification(f"Scanning VLANs {vlan_start}-{vlan_end}...", "info")

            # Auto-stop after scanning completes
            def check_completion():
                if self.vlan_prober and not self.vlan_prober.running:
                    self.root.after(0, lambda: self.vlan_btn.config(text="▶  Scan", bg='#8b5cf6'))
                    self.root.after(0, lambda: self._show_notification(f"Scan complete. Found {len(self.discovered_vlans) if hasattr(self, 'discovered_vlans') else 0} VLANs", "success"))
                elif self.vlan_prober and self.vlan_prober.running:
                    self.root.after(1000, check_completion)

            self.root.after(1000, check_completion)
        else:
            self._show_notification("Failed to start VLAN probe", "error")

    def _on_vlan_result(self, result: VLANProbeResult):
        self.root.after(0, self._display_vlan_result, result)

    def _display_vlan_result(self, result: VLANProbeResult):
        if result.status in ["Detected", "Active", "Probed"]:
            vlan_id = result.vlan_id

            # First = native
            if self.native_vlan is None:
                self.native_vlan = vlan_id
                self.native_vlan_card.set_value(f"VLAN {vlan_id}")
                self.native_vlan_card.value_label.config(fg='#10b981')
            else:
                # Tagged
                self.tagged_vlans.add(vlan_id)

                # Remove placeholder
                if self.tagged_placeholder.winfo_exists():
                    self.tagged_placeholder.destroy()

                # Add VLAN badge
                badge = tk.Frame(self.tagged_vlans_container, bg='#10b981', padx=12, pady=6)
                badge.pack(side=tk.LEFT, padx=5, pady=5)

                tk.Label(
                    badge,
                    text=f"VLAN {vlan_id}",
                    font=('Segoe UI', 10, 'bold'),
                    bg='#10b981',
                    fg='white'
                ).pack()

    def run(self):
        self.root.mainloop()

    def cleanup(self):
        if self.discovery:
            self.discovery.stop_discovery()
        if self.vlan_prober:
            self.vlan_prober.stop_probe()
        self.logger.log_action("Application Closed", "")


def main():
    root = tk.Tk()
    app = UNTApp(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    app.run()


if __name__ == "__main__":
    main()
