"""
Ultimate Network Tool (UNT) - Modern GUI Application
Modular Windows networking tool with tabbed interface and modern design
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ctypes
from logger import get_logger
from network_adapter import NetworkAdapterManager, AdapterInfo
from lldp_cdp_discovery import LLDPCDPDiscovery, DiscoveryResult
from vlan_probe import VLANProber, VLANProbeResult


class ModernButton(tk.Canvas):
    """Custom modern flat button"""

    def __init__(self, parent, text, command, bg_color="#3498db", hover_color="#2980b9",
                 fg_color="white", **kwargs):
        super().__init__(parent, height=40, bd=0, highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.fg_color = fg_color
        self.text = text

        self.configure(bg=bg_color)
        self.text_id = self.create_text(
            0, 20, text=text, fill=fg_color,
            font=("Segoe UI", 10, "bold"), anchor="w"
        )

        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        self.coords(self.text_id, event.width // 2, 20)

    def _on_enter(self, event):
        self.configure(bg=self.hover_color)

    def _on_leave(self, event):
        self.configure(bg=self.bg_color)

    def set_text(self, text):
        self.text = text
        self.itemconfig(self.text_id, text=text)

    def set_color(self, bg_color, hover_color=None):
        self.bg_color = bg_color
        self.hover_color = hover_color or bg_color
        self.configure(bg=bg_color)


class UNTModernApp:
    """Modern tabbed application"""

    # Color scheme
    COLORS = {
        'primary': '#1e88e5',      # Blue
        'primary_dark': '#1565c0',
        'secondary': '#7c4dff',    # Purple
        'secondary_dark': '#651fff',
        'success': '#43a047',      # Green
        'success_dark': '#2e7d32',
        'warning': '#fb8c00',      # Orange
        'warning_dark': '#e65100',
        'danger': '#e53935',       # Red
        'danger_dark': '#c62828',
        'dark': '#263238',         # Dark gray
        'medium': '#37474f',
        'light': '#eceff1',        # Light gray
        'white': '#ffffff',
        'text_dark': '#212121',
        'text_light': '#757575'
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Ultimate Network Tool")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)
        self.root.configure(bg=self.COLORS['light'])

        # Initialize components
        self.logger = get_logger()
        self.adapter_manager = NetworkAdapterManager()
        self.discovery = None
        self.vlan_prober = None
        self.selected_adapter = None

        # Check admin privileges
        self.is_admin = self._check_admin()

        # Configure styles
        self._configure_styles()

        # Build GUI
        self._build_gui()

        # Load adapters
        self._load_adapters()

        self.logger.log_action("Application Started (Modern UI)", f"Admin: {self.is_admin}")

    def _check_admin(self) -> bool:
        """Check if running with admin privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False

    def _configure_styles(self):
        """Configure ttk styles for modern look"""
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook (tabs) style
        style.configure('TNotebook', background=self.COLORS['light'], borderwidth=0)
        style.configure('TNotebook.Tab',
                       background=self.COLORS['medium'],
                       foreground=self.COLORS['white'],
                       padding=[20, 10],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.COLORS['primary'])],
                 foreground=[('selected', self.COLORS['white'])])

        # Combobox style
        style.configure('TCombobox',
                       fieldbackground=self.COLORS['white'],
                       background=self.COLORS['white'],
                       foreground=self.COLORS['text_dark'],
                       arrowcolor=self.COLORS['primary'])

        # Frame style
        style.configure('Card.TFrame', background=self.COLORS['white'], relief='flat')

    def _build_gui(self):
        """Build the modern GUI layout"""

        # === Top Bar ===
        top_bar = tk.Frame(self.root, bg=self.COLORS['dark'], height=70)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)

        # Logo/Title area
        title_frame = tk.Frame(top_bar, bg=self.COLORS['dark'])
        title_frame.pack(side=tk.LEFT, padx=30, pady=15)

        title_label = tk.Label(
            title_frame,
            text="Ultimate Network Tool",
            font=("Segoe UI", 20, "bold"),
            bg=self.COLORS['dark'],
            fg=self.COLORS['white']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_frame,
            text="Professional Network Discovery & Analysis",
            font=("Segoe UI", 9),
            bg=self.COLORS['dark'],
            fg=self.COLORS['text_light']
        )
        subtitle_label.pack()

        # Status indicators
        status_frame = tk.Frame(top_bar, bg=self.COLORS['dark'])
        status_frame.pack(side=tk.RIGHT, padx=30)

        # Admin status
        admin_status_frame = tk.Frame(status_frame, bg=self.COLORS['medium'], padx=15, pady=8)
        admin_status_frame.pack()

        admin_color = self.COLORS['success'] if self.is_admin else self.COLORS['danger']
        admin_text = "ADMINISTRATOR" if self.is_admin else "USER MODE"

        admin_dot = tk.Label(
            admin_status_frame,
            text="●",
            font=("Segoe UI", 16),
            bg=self.COLORS['medium'],
            fg=admin_color
        )
        admin_dot.pack(side=tk.LEFT, padx=(0, 8))

        admin_label = tk.Label(
            admin_status_frame,
            text=admin_text,
            font=("Segoe UI", 10, "bold"),
            bg=self.COLORS['medium'],
            fg=self.COLORS['white']
        )
        admin_label.pack(side=tk.LEFT)

        # === Adapter Selection Bar ===
        adapter_bar = tk.Frame(self.root, bg=self.COLORS['white'], height=60)
        adapter_bar.pack(fill=tk.X, side=tk.TOP)
        adapter_bar.pack_propagate(False)

        adapter_inner = tk.Frame(adapter_bar, bg=self.COLORS['white'])
        adapter_inner.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        tk.Label(
            adapter_inner,
            text="Network Adapter:",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark']
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.adapter_combo = ttk.Combobox(
            adapter_inner,
            state="readonly",
            font=("Segoe UI", 10),
            width=50
        )
        self.adapter_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.adapter_combo.bind("<<ComboboxSelected>>", self._on_adapter_selected)

        # === Main Tabbed Content ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create tabs
        self._create_overview_tab()
        self._create_discovery_tab()
        self._create_vlan_tab()
        self._create_settings_tab()

        # === Footer ===
        footer = tk.Frame(self.root, bg=self.COLORS['medium'], height=35)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="Copyright © Digidots 2025  |  Ultimate Network Tool v1.0",
            font=("Segoe UI", 9),
            bg=self.COLORS['medium'],
            fg=self.COLORS['white']
        ).pack(side=tk.LEFT, padx=20, pady=8)

    def _create_overview_tab(self):
        """Create overview/dashboard tab"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.notebook.add(tab, text="  Overview  ")

        # Main container
        container = tk.Frame(tab, bg=self.COLORS['light'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Adapter info card
        card = ttk.Frame(container, style='Card.TFrame')
        card.pack(fill=tk.BOTH, expand=True)

        # Card header
        header = tk.Frame(card, bg=self.COLORS['primary'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Adapter Information",
            font=("Segoe UI", 12, "bold"),
            bg=self.COLORS['primary'],
            fg=self.COLORS['white']
        ).pack(side=tk.LEFT, padx=20, pady=12)

        # Card content
        content_frame = tk.Frame(card, bg=self.COLORS['white'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.adapter_info_text = scrolledtext.ScrolledText(
            content_frame,
            font=("Consolas", 10),
            wrap=tk.WORD,
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            bd=0,
            padx=15,
            pady=15
        )
        self.adapter_info_text.pack(fill=tk.BOTH, expand=True)

    def _create_discovery_tab(self):
        """Create LLDP/CDP discovery tab"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.notebook.add(tab, text="  Switch Discovery  ")

        container = tk.Frame(tab, bg=self.COLORS['light'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Control panel
        control_panel = ttk.Frame(container, style='Card.TFrame')
        control_panel.pack(fill=tk.X, pady=(0, 15))

        control_inner = tk.Frame(control_panel, bg=self.COLORS['white'])
        control_inner.pack(fill=tk.X, padx=20, pady=20)

        tk.Label(
            control_inner,
            text="LLDP / CDP Discovery",
            font=("Segoe UI", 12, "bold"),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark']
        ).pack(anchor=tk.W, pady=(0, 10))

        tk.Label(
            control_inner,
            text="Passively listen for Link Layer Discovery Protocol (LLDP) and Cisco Discovery Protocol (CDP) frames to identify connected switches and ports.",
            font=("Segoe UI", 9),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_light'],
            wraplength=800,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 15))

        btn_frame = tk.Frame(control_inner, bg=self.COLORS['white'])
        btn_frame.pack(fill=tk.X)

        self.discover_btn_widget = ModernButton(
            btn_frame,
            text="  ▶  Start Discovery",
            command=self._start_discovery,
            bg_color=self.COLORS['success'],
            hover_color=self.COLORS['success_dark'],
            width=200
        )
        self.discover_btn_widget.pack(side=tk.LEFT)

        # Results panel
        results_card = ttk.Frame(container, style='Card.TFrame')
        results_card.pack(fill=tk.BOTH, expand=True)

        results_header = tk.Frame(results_card, bg=self.COLORS['secondary'], height=45)
        results_header.pack(fill=tk.X)
        results_header.pack_propagate(False)

        tk.Label(
            results_header,
            text="Discovery Results",
            font=("Segoe UI", 11, "bold"),
            bg=self.COLORS['secondary'],
            fg=self.COLORS['white']
        ).pack(side=tk.LEFT, padx=20, pady=10)

        results_content = tk.Frame(results_card, bg=self.COLORS['white'])
        results_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.discovery_results_text = scrolledtext.ScrolledText(
            results_content,
            font=("Consolas", 10),
            wrap=tk.WORD,
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            bd=0,
            padx=15,
            pady=15
        )
        self.discovery_results_text.pack(fill=tk.BOTH, expand=True)

    def _create_vlan_tab(self):
        """Create VLAN probing tab"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.notebook.add(tab, text="  VLAN Probe  ")

        container = tk.Frame(tab, bg=self.COLORS['light'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Control panel
        control_panel = ttk.Frame(container, style='Card.TFrame')
        control_panel.pack(fill=tk.X, pady=(0, 15))

        control_inner = tk.Frame(control_panel, bg=self.COLORS['white'])
        control_inner.pack(fill=tk.X, padx=20, pady=20)

        tk.Label(
            control_inner,
            text="VLAN Detection & Probing",
            font=("Segoe UI", 12, "bold"),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark']
        ).pack(anchor=tk.W, pady=(0, 10))

        tk.Label(
            control_inner,
            text="Detect tagged VLANs on the network port using passive discovery and safe, rate-limited active probing with 802.1Q tagged frames.",
            font=("Segoe UI", 9),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_light'],
            wraplength=800,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 15))

        # VLAN range configuration
        range_frame = tk.Frame(control_inner, bg=self.COLORS['white'])
        range_frame.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            range_frame,
            text="VLAN Range:",
            font=("Segoe UI", 10, "bold"),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark']
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.vlan_start_entry = tk.Entry(
            range_frame,
            font=("Segoe UI", 10),
            width=8,
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            bd=1,
            relief=tk.SOLID
        )
        self.vlan_start_entry.insert(0, "1")
        self.vlan_start_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(
            range_frame,
            text="to",
            font=("Segoe UI", 10),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark']
        ).pack(side=tk.LEFT, padx=5)

        self.vlan_end_entry = tk.Entry(
            range_frame,
            font=("Segoe UI", 10),
            width=8,
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            bd=1,
            relief=tk.SOLID
        )
        self.vlan_end_entry.insert(0, "100")
        self.vlan_end_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(
            range_frame,
            text="(Max: 4094)",
            font=("Segoe UI", 9),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_light']
        ).pack(side=tk.LEFT, padx=10)

        # Buttons
        btn_frame = tk.Frame(control_inner, bg=self.COLORS['white'])
        btn_frame.pack(fill=tk.X)

        self.vlan_btn_widget = ModernButton(
            btn_frame,
            text="  ▶  Start VLAN Probe",
            command=self._start_vlan_probe,
            bg_color=self.COLORS['secondary'],
            hover_color=self.COLORS['secondary_dark'],
            width=200
        )
        self.vlan_btn_widget.pack(side=tk.LEFT)

        # Results panel
        results_card = ttk.Frame(container, style='Card.TFrame')
        results_card.pack(fill=tk.BOTH, expand=True)

        results_header = tk.Frame(results_card, bg=self.COLORS['warning'], height=45)
        results_header.pack(fill=tk.X)
        results_header.pack_propagate(False)

        tk.Label(
            results_header,
            text="VLAN Probe Results",
            font=("Segoe UI", 11, "bold"),
            bg=self.COLORS['warning'],
            fg=self.COLORS['white']
        ).pack(side=tk.LEFT, padx=20, pady=10)

        results_content = tk.Frame(results_card, bg=self.COLORS['white'])
        results_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.vlan_results_text = scrolledtext.ScrolledText(
            results_content,
            font=("Consolas", 10),
            wrap=tk.WORD,
            bg=self.COLORS['light'],
            fg=self.COLORS['text_dark'],
            bd=0,
            padx=15,
            pady=15
        )
        self.vlan_results_text.pack(fill=tk.BOTH, expand=True)

    def _create_settings_tab(self):
        """Create settings/info tab"""
        tab = tk.Frame(self.notebook, bg=self.COLORS['light'])
        self.notebook.add(tab, text="  Settings  ")

        container = tk.Frame(tab, bg=self.COLORS['light'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        info_card = ttk.Frame(container, style='Card.TFrame')
        info_card.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(info_card, bg=self.COLORS['dark'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Application Information",
            font=("Segoe UI", 12, "bold"),
            bg=self.COLORS['dark'],
            fg=self.COLORS['white']
        ).pack(side=tk.LEFT, padx=20, pady=12)

        content = tk.Frame(info_card, bg=self.COLORS['white'])
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        info_text = """
Ultimate Network Tool (UNT)
Version 1.0 - Modern Edition

A professional modular Windows networking tool for network discovery and analysis.

Features:
• LLDP/CDP passive discovery for switch identification
• VLAN probing with configurable ranges
• Safe, rate-limited network operations
• Comprehensive logging system
• Administrator privilege detection
• Modular architecture for easy expansion

Requirements:
• Windows 10/11
• Python 3.8+
• Npcap packet capture driver
• Administrator privileges (for packet capture)

Safety Features:
• 50ms delay between VLAN probes
• 200ms timeout per probe
• Graceful error handling
• Non-intrusive network activity

Copyright © Digidots 2025
        """

        tk.Label(
            content,
            text=info_text,
            font=("Segoe UI", 10),
            bg=self.COLORS['white'],
            fg=self.COLORS['text_dark'],
            justify=tk.LEFT
        ).pack(anchor=tk.W)

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
            self.discover_btn_widget.set_text("  ▶  Start Discovery")
            self.discover_btn_widget.set_color(self.COLORS['success'], self.COLORS['success_dark'])
            return

        self.discovery_results_text.delete(1.0, tk.END)
        self.discovery_results_text.insert(
            tk.END,
            f"Starting discovery on {self.selected_adapter.description}...\n\n"
        )

        self.discovery = LLDPCDPDiscovery(self.selected_adapter.description)
        if self.discovery.start_discovery(self._on_discovery_result):
            self.discover_btn_widget.set_text("  ■  Stop Discovery")
            self.discover_btn_widget.set_color(self.COLORS['danger'], self.COLORS['danger_dark'])
        else:
            messagebox.showerror("Error", "Failed to start discovery. Check logs.")

    def _on_discovery_result(self, result: DiscoveryResult):
        """Handle discovery result"""
        self.root.after(0, self._display_discovery_result, result)

    def _display_discovery_result(self, result: DiscoveryResult):
        """Display discovery result"""
        timestamp = result.timestamp.strftime("%H:%M:%S")
        output = f"[{timestamp}] [{result.protocol}]\n"
        output += f"  Switch Name: {result.switch_name or 'N/A'}\n"
        output += f"  Port ID: {result.port_id or 'N/A'}\n"
        output += f"  Model: {result.model or 'N/A'}\n"
        output += f"  Vendor: {result.vendor or 'N/A'}\n\n"

        self.discovery_results_text.insert(tk.END, output)
        self.discovery_results_text.see(tk.END)

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
            self.vlan_btn_widget.set_text("  ▶  Start VLAN Probe")
            self.vlan_btn_widget.set_color(self.COLORS['secondary'], self.COLORS['secondary_dark'])
            return

        try:
            vlan_start = int(self.vlan_start_entry.get())
            vlan_end = int(self.vlan_end_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Range", "Please enter valid VLAN IDs.")
            return

        self.vlan_results_text.delete(1.0, tk.END)
        self.vlan_results_text.insert(
            tk.END,
            f"Starting VLAN probe on {self.selected_adapter.description}...\n"
            f"Range: {vlan_start}-{vlan_end}\n\n"
        )

        self.vlan_prober = VLANProber(self.selected_adapter.description)
        self.vlan_prober.set_vlan_range(vlan_start, vlan_end)

        if self.vlan_prober.start_probe(self._on_vlan_result):
            self.vlan_btn_widget.set_text("  ■  Stop VLAN Probe")
            self.vlan_btn_widget.set_color(self.COLORS['danger'], self.COLORS['danger_dark'])
        else:
            messagebox.showerror("Error", "Failed to start VLAN probe. Check logs.")

    def _on_vlan_result(self, result: VLANProbeResult):
        """Handle VLAN probe result"""
        self.root.after(0, self._display_vlan_result, result)

    def _display_vlan_result(self, result: VLANProbeResult):
        """Display VLAN result"""
        if result.status in ["Detected", "Active"]:
            timestamp = result.timestamp.strftime("%H:%M:%S")
            output = f"[{timestamp}] VLAN {result.vlan_id}: {result.status} ({result.source})\n"
            self.vlan_results_text.insert(tk.END, output)
            self.vlan_results_text.see(tk.END)

    def run(self):
        """Run the application"""
        self.root.mainloop()

    def cleanup(self):
        """Cleanup on exit"""
        if self.discovery:
            self.discovery.stop_discovery()
        if self.vlan_prober:
            self.vlan_prober.stop_probe()
        self.logger.log_action("Application Closed (Modern UI)", "")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = UNTModernApp(root)

    def on_closing():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    app.run()


if __name__ == "__main__":
    main()
