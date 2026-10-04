"""
Ultimate Network Tool (UNT) - Main GUI Application
Modular Windows networking tool with LLDP/CDP discovery and VLAN probing
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ctypes
import sys
from pathlib import Path
from logger import get_logger
from network_adapter import NetworkAdapterManager, AdapterInfo
from lldp_cdp_discovery import LLDPCDPDiscovery, DiscoveryResult
from vlan_probe import VLANProber, VLANProbeResult


class UNTApplication:
    """Main application class"""

    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Network Tool (UNT)")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Initialize components
        self.logger = get_logger()
        self.adapter_manager = NetworkAdapterManager()
        self.discovery = None
        self.vlan_prober = None
        self.selected_adapter = None

        # Check admin privileges
        self.is_admin = self._check_admin()

        # Build GUI
        self._build_gui()

        # Load adapters
        self._load_adapters()

        self.logger.log_action("Application Started", f"Admin: {self.is_admin}")

    def _check_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _build_gui(self):
        """Build the GUI layout"""

        # === Header Frame ===
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        header_frame.pack_propagate(False)

        # Title
        title_label = tk.Label(
            header_frame,
            text="Ultimate Network Tool",
            font=("Segoe UI", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Admin indicator
        admin_color = "#27ae60" if self.is_admin else "#e74c3c"
        admin_text = "ADMIN" if self.is_admin else "USER"
        self.admin_indicator = tk.Label(
            header_frame,
            text=f"● {admin_text}",
            font=("Segoe UI", 10, "bold"),
            bg="#2c3e50",
            fg=admin_color
        )
        self.admin_indicator.pack(side=tk.RIGHT, padx=20, pady=10)

        # === Main Content ===
        main_frame = tk.Frame(self.root, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Panel - Adapter Selection & Info
        left_panel = tk.Frame(main_frame, bg="white", width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Adapter Selection
        adapter_label = tk.Label(
            left_panel,
            text="Network Adapter",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        )
        adapter_label.pack(anchor=tk.W, pady=(5, 2))

        self.adapter_combo = ttk.Combobox(
            left_panel,
            state="readonly",
            font=("Segoe UI", 9)
        )
        self.adapter_combo.pack(fill=tk.X, pady=(0, 10))
        self.adapter_combo.bind("<<ComboboxSelected>>", self._on_adapter_selected)

        # Adapter Info
        info_label = tk.Label(
            left_panel,
            text="Adapter Information",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        )
        info_label.pack(anchor=tk.W, pady=(10, 2))

        self.adapter_info_text = scrolledtext.ScrolledText(
            left_panel,
            height=15,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#f8f9fa"
        )
        self.adapter_info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Control Buttons
        button_frame = tk.Frame(left_panel, bg="white")
        button_frame.pack(fill=tk.X, pady=10)

        self.discover_btn = tk.Button(
            button_frame,
            text="Start Discovery",
            command=self._start_discovery,
            bg="#3498db",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.discover_btn.pack(fill=tk.X, pady=2)

        self.vlan_btn = tk.Button(
            button_frame,
            text="Start VLAN Probe",
            command=self._start_vlan_probe,
            bg="#9b59b6",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.vlan_btn.pack(fill=tk.X, pady=2)

        # VLAN Range
        vlan_range_frame = tk.Frame(left_panel, bg="white")
        vlan_range_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            vlan_range_frame,
            text="VLAN Range:",
            font=("Segoe UI", 9),
            bg="white"
        ).pack(side=tk.LEFT)

        self.vlan_start_entry = tk.Entry(vlan_range_frame, width=6, font=("Segoe UI", 9))
        self.vlan_start_entry.insert(0, "1")
        self.vlan_start_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(vlan_range_frame, text="-", bg="white").pack(side=tk.LEFT)

        self.vlan_end_entry = tk.Entry(vlan_range_frame, width=6, font=("Segoe UI", 9))
        self.vlan_end_entry.insert(0, "100")
        self.vlan_end_entry.pack(side=tk.LEFT, padx=5)

        # Right Panel - Results
        right_panel = tk.Frame(main_frame, bg="white")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        results_label = tk.Label(
            right_panel,
            text="Discovery Results",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        )
        results_label.pack(anchor=tk.W, pady=(5, 2))

        self.results_text = scrolledtext.ScrolledText(
            right_panel,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#f8f9fa"
        )
        self.results_text.pack(fill=tk.BOTH, expand=True)

        # === Footer ===
        footer_frame = tk.Frame(self.root, bg="#34495e", height=30)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        footer_frame.pack_propagate(False)

        copyright_label = tk.Label(
            footer_frame,
            text="Copyright Digidots 2025",
            font=("Segoe UI", 9),
            bg="#34495e",
            fg="white"
        )
        copyright_label.pack(side=tk.LEFT, padx=20, pady=5)

    def _load_adapters(self):
        """Load network adapters into dropdown"""
        adapters = self.adapter_manager.enumerate_adapters()

        if not adapters:
            messagebox.showwarning("No Adapters", "No network adapters found.")
            return

        # Prefer Ethernet adapters
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

        # Find adapter
        for adapter in self.adapter_manager.adapters:
            if str(adapter) == selection:
                self.selected_adapter = adapter
                self._display_adapter_info(adapter)
                self.logger.log_action("Adapter Selected", adapter.description)
                break

    def _display_adapter_info(self, adapter: AdapterInfo):
        """Display adapter information"""
        self.adapter_info_text.delete(1.0, tk.END)
        info = self.adapter_manager.format_adapter_info(adapter)
        self.adapter_info_text.insert(tk.END, info)

    def _start_discovery(self):
        """Start LLDP/CDP discovery"""
        if not self.selected_adapter:
            messagebox.showwarning("No Adapter", "Please select a network adapter.")
            return

        if not self.is_admin:
            messagebox.showerror(
                "Admin Required",
                "Administrator privileges required for packet capture."
            )
            return

        if self.discovery and self.discovery.running:
            self.discovery.stop_discovery()
            self.discover_btn.config(text="Start Discovery", bg="#3498db")
            return

        # Start discovery
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"Starting discovery on {self.selected_adapter.description}...\n\n")

        self.discovery = LLDPCDPDiscovery(self.selected_adapter.description)
        if self.discovery.start_discovery(self._on_discovery_result):
            self.discover_btn.config(text="Stop Discovery", bg="#e67e22")
        else:
            messagebox.showerror("Error", "Failed to start discovery. Check logs.")

    def _on_discovery_result(self, result: DiscoveryResult):
        """Handle discovery result"""
        self.root.after(0, self._display_discovery_result, result)

    def _display_discovery_result(self, result: DiscoveryResult):
        """Display discovery result in GUI"""
        timestamp = result.timestamp.strftime("%H:%M:%S")
        output = f"[{timestamp}] [{result.protocol}]\n"
        output += f"  Switch Name: {result.switch_name or 'N/A'}\n"
        output += f"  Port ID: {result.port_id or 'N/A'}\n"
        output += f"  Model: {result.model or 'N/A'}\n"
        output += f"  Vendor: {result.vendor or 'N/A'}\n\n"

        self.results_text.insert(tk.END, output)
        self.results_text.see(tk.END)

    def _start_vlan_probe(self):
        """Start VLAN probing"""
        if not self.selected_adapter:
            messagebox.showwarning("No Adapter", "Please select a network adapter.")
            return

        if not self.is_admin:
            messagebox.showerror(
                "Admin Required",
                "Administrator privileges required for VLAN probing."
            )
            return

        if self.vlan_prober and self.vlan_prober.running:
            self.vlan_prober.stop_probe()
            self.vlan_btn.config(text="Start VLAN Probe", bg="#9b59b6")
            return

        # Get VLAN range
        try:
            vlan_start = int(self.vlan_start_entry.get())
            vlan_end = int(self.vlan_end_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Range", "Please enter valid VLAN IDs.")
            return

        # Start probing
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END,
                                f"Starting VLAN probe on {self.selected_adapter.description}...\n"
                                f"Range: {vlan_start}-{vlan_end}\n\n")

        self.vlan_prober = VLANProber(self.selected_adapter.description)
        self.vlan_prober.set_vlan_range(vlan_start, vlan_end)

        if self.vlan_prober.start_probe(self._on_vlan_result):
            self.vlan_btn.config(text="Stop VLAN Probe", bg="#e67e22")
        else:
            messagebox.showerror("Error", "Failed to start VLAN probe. Check logs.")

    def _on_vlan_result(self, result: VLANProbeResult):
        """Handle VLAN probe result"""
        self.root.after(0, self._display_vlan_result, result)

    def _display_vlan_result(self, result: VLANProbeResult):
        """Display VLAN result in GUI"""
        # Only display notable results
        if result.status in ["Detected", "Active"]:
            timestamp = result.timestamp.strftime("%H:%M:%S")
            output = f"[{timestamp}] VLAN {result.vlan_id}: {result.status} ({result.source})\n"
            self.results_text.insert(tk.END, output)
            self.results_text.see(tk.END)

    def run(self):
        """Run the application"""
        self.root.mainloop()

    def cleanup(self):
        """Cleanup on exit"""
        if self.discovery:
            self.discovery.stop_discovery()
        if self.vlan_prober:
            self.vlan_prober.stop_probe()
        self.logger.log_action("Application Closed", "")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = UNTApplication(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    app.run()


if __name__ == "__main__":
    main()
