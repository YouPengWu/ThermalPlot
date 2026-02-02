from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

class ThermalPlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Create Figure and Canvas
        # Increase DPI for better clarity if needed, though tight_layout helps sizing
        self.figure = Figure(figsize=(8, 6), dpi=120) # Increased DPI
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.updateGeometry()
        
        self.layout.addWidget(self.canvas)
        
        # Configure global font sizes for clarity
        import matplotlib as mpl
        mpl.rcParams.update({
            'font.size': 12,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 12,
            'lines.linewidth': 2.5 # Thicker lines by default
        })
        
        # Initial empty plot
        self.ax_main = self.figure.add_subplot(111)
        self.ax_main.set_title("Temperature vs Fan Duty vs Time", fontweight='bold')
        self.ax_main.grid(True, linestyle=':', alpha=0.6)
        
        # Annotation for Tooltip
        self.annot = None
        self.current_ax = None
        
        # Connect Hover Event
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

    def on_hover(self, event):
        vis = self.annot.get_visible() if self.annot else False
        if event.inaxes:
            # Check all lines in the axis where mouse is
            ax = event.inaxes
            found = False
            for line in ax.get_lines():
                cont, ind = line.contains(event)
                if cont:
                    self.update_annot(line, ind)
                    self.annot.set_visible(True)
                    self.figure.canvas.draw_idle()
                    found = True
                    break
            if not found and vis:
                self.annot.set_visible(False)
                self.figure.canvas.draw_idle()
    
    def update_annot(self, line, ind):
        x, y = line.get_data()
        # Takes the first index if multiple
        idx = ind["ind"][0]
        self.annot.xy = (x[idx], y[idx])
        
        text = f"{line.get_label()}\nTime: {x[idx]:.1f}s\nVal: {y[idx]:.1f}"
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.8)
        self.annot.set_color('black')
        self.annot.get_bbox_patch().set_facecolor('white')

    def plot_data(self, time_data, temp_data, fan_data, settings, mode_idx=0, title_suffix=""):
        """
        Re-plots all data based on mode.
        mode_idx: 
          0 = Dual Axis (Temp Left, Fan Right)
          1 = Temp Only (Left)
          2 = Fan Only (Left)
        title_suffix: filename or string to append to title
        """
        # Apply Styles
        styles = settings.get("style_settings", {})
        title_size = styles.get("title_size", 14)
        axis_size = styles.get("axis_label_size", 12)
        tick_size = styles.get("tick_label_size", 10)
        legend_size = styles.get("legend_size", 12)
        lw = styles.get("line_width", 2.5)
        
        mpl.rcParams.update({
            'font.family': 'serif',
            'font.serif': ['Times New Roman', 'Liberation Serif', 'DejaVu Serif', 'serif'],
            'font.size': axis_size, # Base size
            'axes.titlesize': title_size,
            'axes.labelsize': axis_size,
            'xtick.labelsize': tick_size,
            'ytick.labelsize': tick_size,
            'legend.fontsize': legend_size,
            'lines.linewidth': lw
        })
        
        self.figure.clf()
        
        # Setup Axes based on mode
        ax1 = self.figure.add_subplot(111)
        ax2 = None
        
        # Common Grid
        ax1.grid(True, linestyle=':', alpha=0.6)
        ax1.set_xlabel('Time (s)', fontsize=axis_size)
        ax1.tick_params(axis='both', labelsize=tick_size)
        
        # Title
        # Get custom title settings
        custom_title = styles.get("custom_title", "")
        title_position = styles.get("title_position", "top")
        
        # Determine title text
        if custom_title:
            full_title = custom_title
        else:
            # Auto-generated title without filename
            if mode_idx == 0: 
                full_title = "Temperature vs Fan Duty vs Time"
            elif mode_idx == 1: 
                full_title = "Temperature vs Time"
            elif mode_idx == 2: 
                full_title = "Fan Duty vs Time"
        
        # Set title position
        if title_position == "bottom":
            # Place title below X-axis
            ax1.set_xlabel('')  # Clear default xlabel temporarily
            # Add title as text below the plot
            ax1.text(0.5, -0.15, full_title, 
                    ha='center', va='top',
                    transform=ax1.transAxes,
                    fontweight='bold', fontsize=title_size)
            # Re-add X-axis label above the title
            ax1.text(0.5, -0.08, 'Time (s)', 
                    ha='center', va='top',
                    transform=ax1.transAxes,
                    fontsize=axis_size)
        else:
            # Default: title at top
            ax1.set_title(full_title, fontweight='bold', fontsize=title_size)
        
        # Initialize Annotation (again because clf() wiped it)
        self.annot = ax1.annotate("", xy=(0,0), xytext=(20,20),textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)

        # Logic for each mode
        if mode_idx == 0: # Dual
            ax1.set_ylabel('Temperature (°C)', fontweight='normal', fontsize=axis_size)
            
            ax2 = ax1.twinx()
            ax2.set_ylabel('Fan Duty (%)', fontweight='normal', rotation=270, labelpad=15, fontsize=axis_size)
            ax2.yaxis.set_label_position("right")
            ax2.yaxis.tick_right()
            ax2.tick_params(axis='y', labelsize=tick_size)
            
            self._plot_temps(ax1, time_data, temp_data, settings, lw)
            self._plot_fans(ax2, time_data, fan_data, settings, lw)
            
        elif mode_idx == 1: # Temp Only
            ax1.set_ylabel('Temperature (°C)', fontweight='normal', fontsize=axis_size)
            self._plot_temps(ax1, time_data, temp_data, settings, lw)
            
        elif mode_idx == 2: # Fan Only
            ax1.set_ylabel('Fan Duty (%)', fontweight='normal', fontsize=axis_size)
            self._plot_fans(ax1, time_data, fan_data, settings, lw)

        # Legend Handling
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ([], [])
        if ax2:
            lines2, labels2 = ax2.get_legend_handles_labels()
            
        all_lines = lines1 + lines2
        all_labels = labels1 + labels2
        
        if all_lines:
            # Position from settings
            leg_pos = styles.get("legend_position", "lower right")
            # Lower Right, White background, No Border
            leg = ax1.legend(all_lines, all_labels, 
                             loc=leg_pos, 
                             fontsize=legend_size,
                             frameon=True, facecolor='white', edgecolor='none')
            leg.get_frame().set_alpha(1.0)

        # Layout Adjustment (increase bottom margin if title is at bottom)
        if styles.get("title_position", "top") == "bottom":
            self.figure.tight_layout(rect=[0, 0.08, 1, 1])  # Leave space at bottom
        else:
            self.figure.tight_layout()
        
        # Set Figure Background back to White
        self.figure.patch.set_facecolor('white')

        self.canvas.draw()

    def _plot_temps(self, ax, time_data, temp_data, settings, lw):
        for name, values in temp_data.items():
            sett = settings.get("temp_settings", {}).get(name, {})
            if not sett.get("visible", True): continue
            
            color = sett.get("color", None)
            style = sett.get("style", "solid")
            linestyle = '--' if style == 'dashed' else '-'
            
            min_len = min(len(time_data), len(values))
            if min_len == 0: continue
            ax.plot(time_data[:min_len], values[:min_len], label=name, color=color, linestyle=linestyle, linewidth=lw, picker=5)

    def _plot_fans(self, ax, time_data, fan_data, settings, lw):
        for name, values in fan_data.items():
            sett = settings.get("fan_settings", {}).get(name, {})
            if not sett.get("visible", True): continue
            
            color = sett.get("color", None)
            style = sett.get("style", "solid")
            linestyle = '--' if style == 'dashed' else '-'
            
            min_len = min(len(time_data), len(values))
            if min_len == 0: continue
            ax.plot(time_data[:min_len], values[:min_len], label=name, color=color, linestyle=linestyle, linewidth=lw, picker=5)

    def save_image(self, filepath, width=None, height=None, dpi=300):
        try:
            if not filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf', '.svg')):
                filepath += ".png"
            
            # If custom dimensions provided, temporarily adjust figure size
            if width and height:
                # Calculate figure size in inches based on DPI
                fig_width = width / dpi
                fig_height = height / dpi
                original_size = self.figure.get_size_inches()
                self.figure.set_size_inches(fig_width, fig_height)
                self.figure.savefig(filepath, dpi=dpi, bbox_inches='tight')
                # Restore original size
                self.figure.set_size_inches(original_size)
            else:
                self.figure.savefig(filepath, dpi=dpi, bbox_inches='tight')
            
            return True
        except Exception as e:
            return str(e)
