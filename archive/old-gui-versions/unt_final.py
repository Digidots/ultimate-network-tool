"""
Ultimate Network Tool (UNT) - Final Modern GUI
Professional network discovery tool with glassmorphism design
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ctypes
import subprocess
from logger import get_logger
from network_adapter import NetworkAdapterManager, AdapterInfo
from lldp_cdp_discovery import LLDPCDPDiscovery, DiscoveryResult
from vlan_probe import VLANProber, VLANProbeResult


class GlassFrame(tk.Frame):
    """Glassmorphism-style frame"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg='#1e293b', bd=1, relief=tk.SOLID, **kwargs)
        self.configure(highlightbackground='#334155', highlightthickness=1)


class ModernCard(tk.Frame):
    """Modern card component with shadow effect"""
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, bg='#1e293b', **kwargs)
        self.configure(highlightbackground='#334155', highlightthickness=1, bd=0)

        if title:
            header = tk.Frame(self, bg='#0f172a', height=45)
            header.pack(fill=tk.X)
            header.pack_propagate(False)

            tk.Label(
                header,
                text=title,
                font=('Segoe UI', 11, 'bold'),
                bg='#0f172a',
                fg='#60a5fa'
            ).pack(side=tk.LEFT, padx=20, pady=12)


class UNTFinalApp:
    """Modern single-tab GUI application"""

    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Network Tool")
        self.root.geometry("1400x850")
        self.root.resizable(True, True)

        # Dark gradient background
        self.root.configure(bg='#0f172a')

        # Initialize components
        self.logger = get_logger()
        self.adapter_manager = NetworkAdapterManager()
        self.discovery = None
        self.vlan_prober = None
        self.selected_adapter = None

        # VLAN tracking
        self.native_vlan = None
        self.tagged_vlans = set()

        # Check admin
        self.is_admin = self._check_admin()

        # Build GUI
        self._build_gui()

        # Load adapters
        self._load_adapters()

        self.logger.log_action("Application Started (Final UI)", f"Admin: {self.is_admin}")

    def _check_admin(self) -> bool:
        """Check admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _build_gui(self):
        """Build the modern GUI"""

        # === Header ===
        header = tk.Frame(self.root, bg='#1e293b', height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        # Title section
        title_frame = tk.Frame(header, bg='#1e293b')
        title_frame.pack(side=tk.LEFT, padx=30, pady=15)

        tk.Label(
            title_frame,
            text="🔍 Ultimate Network Tool",
            font=('Segoe UI', 20, 'bold'),
            bg='#1e293b',
            fg='#60a5fa'
        ).pack(anchor=tk.W)

        tk.Label(
            title_frame,
            text="Professional Network Discovery & VLAN Analysis",
            font=('Segoe UI', 9),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(anchor=tk.W)

        # Admin status
        status_frame = tk.Frame(header, bg='#0f172a', padx=15, pady=8)
        status_frame.pack(side=tk.RIGHT, padx=30)

        admin_color = '#10b981' if self.is_admin else '#ef4444'
        admin_text = "ADMINISTRATOR" if self.is_admin else "USER MODE"

        tk.Label(
            status_frame,
            text="●",
            font=('Segoe UI', 16),
            bg='#0f172a',
            fg=admin_color
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            status_frame,
            text=admin_text,
            font=('Segoe UI', 10, 'bold'),
            bg='#0f172a',
            fg='#e2e8f0'
        ).pack(side=tk.LEFT)

        # === Main Container ===
        main_container = tk.Frame(self.root, bg='#0f172a')
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # === Adapter Selection Bar ===
        adapter_card = GlassFrame(main_container)
        adapter_card.pack(fill=tk.X, pady=(0, 15))

        adapter_inner = tk.Frame(adapter_card, bg='#1e293b')
        adapter_inner.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            adapter_inner,
            text="NETWORK ADAPTER",
            font=('Segoe UI', 9, 'bold'),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.adapter_combo = ttk.Combobox(
            adapter_inner,
            state="readonly",
            font=('Segoe UI', 10),
            width=60
        )
        self.adapter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.adapter_combo.bind("<<ComboboxSelected>>", self._on_adapter_selected)

        # Refresh button
        self.refresh_btn = tk.Button(
            adapter_inner,
            text="🔄 Refresh IP",
            command=self._refresh_adapter,
            bg='#3b82f6',
            fg='white',
            font=('Segoe UI', 9, 'bold'),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        # === Main Content Grid ===
        content_grid = tk.Frame(main_container, bg='#0f172a')
        content_grid.pack(fill=tk.BOTH, expand=True)

        # Left column
        left_col = tk.Frame(content_grid, bg='#0f172a')
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right column
        right_col = tk.Frame(content_grid, bg='#0f172a', width=400)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_col.pack_propagate(False)

        # === Left Column: Adapter Info & Discovery ===

        # Adapter Info Card
        adapter_info_card = ModernCard(left_col, title="Adapter Information")
        adapter_info_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        info_content = tk.Frame(adapter_info_card, bg='#1e293b')
        info_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.adapter_info_text = scrolledtext.ScrolledText(
            info_content,
            font=('Consolas', 9),
            wrap=tk.WORD,
            bg='#0f172a',
            fg='#e2e8f0',
            bd=0,
            padx=10,
            pady=10,
            insertbackground='#60a5fa'
        )
        self.adapter_info_text.pack(fill=tk.BOTH, expand=True)

        # LLDP/CDP Discovery Card
        discovery_card = ModernCard(left_col, title="Switch Discovery (LLDP/CDP)")
        discovery_card.pack(fill=tk.BOTH, expand=True)

        discovery_content = tk.Frame(discovery_card, bg='#1e293b')
        discovery_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Discovery button
        self.discover_btn = tk.Button(
            discovery_content,
            text="▶  Start Discovery",
            command=self._start_discovery,
            bg='#10b981',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.discover_btn.pack(pady=(0, 15))

        # Discovery results container
        self.discovery_results_frame = tk.Frame(discovery_content, bg='#1e293b')
        self.discovery_results_frame.pack(fill=tk.BOTH, expand=True)

        # === Right Column: VLAN Probe ===

        # VLAN Probe Card
        vlan_card = ModernCard(right_col, title="VLAN Detection")
        vlan_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        vlan_content = tk.Frame(vlan_card, bg='#1e293b')
        vlan_content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # VLAN range
        range_frame = tk.Frame(vlan_content, bg='#1e293b')
        range_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            range_frame,
            text="VLAN RANGE",
            font=('Segoe UI', 9, 'bold'),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.vlan_start_entry = tk.Entry(
            range_frame,
            font=('Segoe UI', 10),
            width=6,
            bg='#0f172a',
            fg='#e2e8f0',
            bd=1,
            relief=tk.SOLID,
            insertbackground='#60a5fa'
        )
        self.vlan_start_entry.insert(0, "1")
        self.vlan_start_entry.pack(side=tk.LEFT, padx=3)

        tk.Label(
            range_frame,
            text="to",
            font=('Segoe UI', 10),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(side=tk.LEFT, padx=5)

        self.vlan_end_entry = tk.Entry(
            range_frame,
            font=('Segoe UI', 10),
            width=6,
            bg='#0f172a',
            fg='#e2e8f0',
            bd=1,
            relief=tk.SOLID,
            insertbackground='#60a5fa'
        )
        self.vlan_end_entry.insert(0, "100")
        self.vlan_end_entry.pack(side=tk.LEFT, padx=3)

        # VLAN probe button
        self.vlan_btn = tk.Button(
            vlan_content,
            text="▶  Start VLAN Probe",
            command=self._start_vlan_probe,
            bg='#8b5cf6',
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.vlan_btn.pack(pady=(0, 15))

        # Native VLAN box
        native_label = tk.Label(
            vlan_content,
            text="NATIVE/UNTAGGED VLAN",
            font=('Segoe UI', 9, 'bold'),
            bg='#1e293b',
            fg='#94a3b8'
        )
        native_label.pack(anchor=tk.W, pady=(0, 5))

        self.native_vlan_box = tk.Frame(vlan_content, bg='#0f172a', height=60)
        self.native_vlan_box.pack(fill=tk.X, pady=(0, 15))
        self.native_vlan_box.pack_propagate(False)

        self.native_vlan_label = tk.Label(
            self.native_vlan_box,
            text="Not detected",
            font=('Segoe UI', 24, 'bold'),
            bg='#0f172a',
            fg='#64748b'
        )
        self.native_vlan_label.pack(expand=True)

        # Tagged VLANs box
        tagged_label = tk.Label(
            vlan_content,
            text="TAGGED VLANS",
            font=('Segoe UI', 9, 'bold'),
            bg='#1e293b',
            fg='#94a3b8'
        )
        tagged_label.pack(anchor=tk.W, pady=(0, 5))

        tagged_scroll_frame = tk.Frame(vlan_content, bg='#0f172a')
        tagged_scroll_frame.pack(fill=tk.BOTH, expand=True)

        self.tagged_vlans_text = scrolledtext.ScrolledText(
            tagged_scroll_frame,
            font=('Consolas', 10),
            wrap=tk.WORD,
            bg='#0f172a',
            fg='#10b981',
            bd=0,
            padx=10,
            pady=10,
            height=10,
            insertbackground='#60a5fa'
        )
        self.tagged_vlans_text.pack(fill=tk.BOTH, expand=True)
        self.tagged_vlans_text.insert('1.0', "No tagged VLANs detected")
        self.tagged_vlans_text.config(state=tk.DISABLED)

        # Summary card
        summary_card = ModernCard(right_col, title="Summary")
        summary_card.pack(fill=tk.X)

        summary_content = tk.Frame(summary_card, bg='#1e293b')
        summary_content.pack(fill=tk.BOTH, padx=15, pady=15)

        self.summary_text = tk.Label(
            summary_content,
            text="Ready to scan",
            font=('Segoe UI', 9),
            bg='#1e293b',
            fg='#94a3b8',
            justify=tk.LEFT
        )
        self.summary_text.pack(anchor=tk.W)

        # === Footer ===
        footer = tk.Frame(self.root, bg='#1e293b', height=35)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="Copyright © Digidots 2025  |  Ultimate Network Tool v2.0",
            font=('Segoe UI', 9),
            bg='#1e293b',
            fg='#94a3b8'
        ).pack(side=tk.LEFT, padx=20, pady=8)

    def _load_adapters(self):
        """Load network adapters"""
        adapters = self.adapter_manager.enumerate_adapters()

        if not adapters:
            messagebox.showwarning("No Adapters", "No network adapters found.")
            return

        ethernet_adapters = self.adapter_manager.get_ethernet_adapters()
        display_adapters = ethernet_adapters if ethernet_adapters else adapters

        adapter_names = [str(adapter) for adapter in display_adapters]
        self.adapter_combo['values'] = adapter_names

        if adapter_names:
            self.adapter_combo.current(0)
            self._on_adapter_selected(None)

    def _on_adapter_selected(self, event):
        """Handle adapter selection"""
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
        """Display adapter information"""
        self.adapter_info_text.delete('1.0', tk.END)
        info = self.adapter_manager.format_adapter_info(adapter)
        self.adapter_info_text.insert('1.0', info)

    def _refresh_adapter(self):
        """Refresh adapter IP (renew DHCP lease)"""
        if not self.selected_adapter:
            messagebox.showwarning("No Adapter", "Please select a network adapter.")
            return

        if not self.is_admin:
            messagebox.showerror("Admin Required", "Administrator privileges required to renew IP.")
            return

        self.logger.log_action("Refresh IP", self.selected_adapter.description)

        try:
            # Release and renew IP
            adapter_name = self.selected_adapter.description

            subprocess.run(['ipconfig', '/release'], capture_output=True, timeout=10)
            subprocess.run(['ipconfig', '/renew'], capture_output=True, timeout=30)

            # Reload adapters
            self._load_adapters()

            messagebox.showinfo("Success", "IP address renewed successfully!")

        except Exception as e:
            self.logger.log_exception("refresh_adapter", e)
            messagebox.showerror("Error", f"Failed to refresh IP: {str(e)}")

    def _start_discovery(self):
        """Start LLDP/CDP discovery"""
        if not self.selected_adapter:
            messagebox.showwarning("No Adapter", "Please select a network adapter.")
            return

        if not self.is_admin:
            messagebox.showerror("Admin Required", "Administrator privileges required for packet capture.")
            return

        if self.discovery and self.discovery.running:
            self.discovery.stop_discovery()
            self.discover_btn.config(text="▶  Start Discovery", bg='#10b981')
            return

        # Clear previous results
        for widget in self.discovery_results_frame.winfo_children():
            widget.destroy()

        self.discovery = LLDPCDPDiscovery(self.selected_adapter.description)
        if self.discovery.start_discovery(self._on_discovery_result):
            self.discover_btn.config(text="■  Stop Discovery", bg='#ef4444')
        else:
            messagebox.showerror("Error", "Failed to start discovery. Check logs.")

    def _on_discovery_result(self, result: DiscoveryResult):
        """Handle discovery result"""
        self.root.after(0, self._display_discovery_result, result)

    def _display_discovery_result(self, result: DiscoveryResult):
        """Display discovery result in a nice box"""
        # Create result card
        result_box = tk.Frame(self.discovery_results_frame, bg='#0f172a', bd=1, relief=tk.SOLID)
        result_box.pack(fill=tk.X, pady=5)

        # Header with protocol badge
        header = tk.Frame(result_box, bg='#0f172a')
        header.pack(fill=tk.X, padx=10, pady=8)

        protocol_color = '#3b82f6' if result.protocol == 'LLDP' else '#f59e0b'
        protocol_badge = tk.Label(
            header,
            text=result.protocol,
            font=('Segoe UI', 9, 'bold'),
            bg=protocol_color,
            fg='white',
            padx=8,
            pady=3
        )
        protocol_badge.pack(side=tk.LEFT, padx=(0, 10))

        timestamp = result.timestamp.strftime("%H:%M:%S")
        tk.Label(
            header,
            text=timestamp,
            font=('Consolas', 9),
            bg='#0f172a',
            fg='#64748b'
        ).pack(side=tk.LEFT)

        # Content
        content = tk.Frame(result_box, bg='#0f172a')
        content.pack(fill=tk.X, padx=10, pady=(0, 10))

        info_items = [
            ("Switch", result.switch_name or 'N/A'),
            ("Port", result.port_id or 'N/A'),
            ("Model", result.model or 'N/A'),
            ("Vendor", result.vendor or 'N/A')
        ]

        for label, value in info_items:
            row = tk.Frame(content, bg='#0f172a')
            row.pack(fill=tk.X, pady=2)

            tk.Label(
                row,
                text=f"{label}:",
                font=('Segoe UI', 9),
                bg='#0f172a',
                fg='#94a3b8',
                width=10,
                anchor=tk.W
            ).pack(side=tk.LEFT)

            tk.Label(
                row,
                text=value,
                font=('Consolas', 9, 'bold'),
                bg='#0f172a',
                fg='#10b981'
            ).pack(side=tk.LEFT)

    def _start_vlan_probe(self):
        """Start VLAN probing"""
        if not self.selected_adapter:
            messagebox.showwarning("No Adapter", "Please select a network adapter.")
            return

        if not self.is_admin:
            messagebox.showerror("Admin Required", "Administrator privileges required for VLAN probing.")
            return

        if self.vlan_prober and self.vlan_prober.running:
            self.vlan_prober.stop_probe()
            self.vlan_btn.config(text="▶  Start VLAN Probe", bg='#8b5cf6')
            self._update_summary()
            return

        try:
            vlan_start = int(self.vlan_start_entry.get())
            vlan_end = int(self.vlan_end_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Range", "Please enter valid VLAN IDs.")
            return

        # Reset VLAN tracking
        self.native_vlan = None
        self.tagged_vlans.clear()
        self.native_vlan_label.config(text="Scanning...", fg='#f59e0b')
        self.tagged_vlans_text.config(state=tk.NORMAL)
        self.tagged_vlans_text.delete('1.0', tk.END)
        self.tagged_vlans_text.insert('1.0', "Scanning...")
        self.tagged_vlans_text.config(state=tk.DISABLED)

        self.vlan_prober = VLANProber(self.selected_adapter.description)
        self.vlan_prober.set_vlan_range(vlan_start, vlan_end)

        if self.vlan_prober.start_probe(self._on_vlan_result):
            self.vlan_btn.config(text="■  Stop VLAN Probe", bg='#ef4444')
        else:
            messagebox.showerror("Error", "Failed to start VLAN probe. Check logs.")

    def _on_vlan_result(self, result: VLANProbeResult):
        """Handle VLAN probe result"""
        self.root.after(0, self._display_vlan_result, result)

    def _display_vlan_result(self, result: VLANProbeResult):
        """Display VLAN result"""
        # Only process detected/active VLANs
        if result.status in ["Detected", "Probed", "Active"]:
            vlan_id = result.vlan_id

            # First detected VLAN is native/untagged
            if self.native_vlan is None:
                self.native_vlan = vlan_id
                self.native_vlan_label.config(text=f"VLAN {vlan_id}", fg='#10b981')
            else:
                # All others are tagged
                self.tagged_vlans.add(vlan_id)

                # Update tagged VLANs display
                self.tagged_vlans_text.config(state=tk.NORMAL)
                self.tagged_vlans_text.delete('1.0', tk.END)

                if self.tagged_vlans:
                    sorted_vlans = sorted(list(self.tagged_vlans))
                    vlan_text = ", ".join([f"VLAN {v}" for v in sorted_vlans])
                    self.tagged_vlans_text.insert('1.0', vlan_text)
                else:
                    self.tagged_vlans_text.insert('1.0', "No additional tagged VLANs")

                self.tagged_vlans_text.config(state=tk.DISABLED)

            self._update_summary()

    def _update_summary(self):
        """Update summary text"""
        total_vlans = 1 if self.native_vlan else 0
        total_vlans += len(self.tagged_vlans)

        summary = f"VLANs found: {total_vlans}"
        if self.native_vlan:
            summary += f"\nNative: VLAN {self.native_vlan}"
        if self.tagged_vlans:
            summary += f"\nTagged: {len(self.tagged_vlans)} VLANs"

        self.summary_text.config(text=summary)

    def run(self):
        """Run the application"""
        self.root.mainloop()

    def cleanup(self):
        """Cleanup on exit"""
        if self.discovery:
            self.discovery.stop_discovery()
        if self.vlan_prober:
            self.vlan_prober.stop_probe()
        self.logger.log_action("Application Closed (Final UI)", "")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = UNTFinalApp(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    app.run()


if __name__ == "__main__":
    main()
