from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QListWidget, QTextEdit, 
                             QGroupBox, QScrollArea, QLabel, QCheckBox, QColorDialog, 
                             QComboBox, QSplitter, QFrame, QLineEdit, QDialog, QMessageBox,
                             QSpinBox, QDoubleSpinBox, QFormLayout) # Added SpinBoxes
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal
from src.plotter import ThermalPlotter
from src.log_parser import LogParser
from src.config_manager import ConfigManager
import os



class ColorButton(QPushButton):
    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        self.color = color
        self.update_style()
        self.clicked.connect(self.pick_color)

    def update_style(self):
        self.setStyleSheet(f"background-color: {self.color}; border: 1px solid Gray;")

    def pick_color(self):
        c = QColorDialog.getColor(initial=QColor(self.color))
        if c.isValid():
            self.color = c.name()
            self.update_style()
            # Signal parent? We might need a callback logic.

class ConfigRow(QWidget):
    def __init__(self, name, category, settings, index=0, parent=None):
        super().__init__(parent)
        self.name = name
        self.category = category
        self.settings = settings
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        self.checkbox = QCheckBox(name)
        self.checkbox.setChecked(settings.get("visible", True))
        self.checkbox.stateChanged.connect(self.update_visibility)
        
        self.color_btn = ColorButton(settings.get("color", "#ff0000" if category=="fan_settings" else "#0000ff"))
        self.color_btn.clicked.connect(self.update_color)
        
        self.style_combo = QComboBox()
        self.style_combo.addItems(["solid", "dashed"])
        self.style_combo.setCurrentText(settings.get("style", "solid"))
        self.style_combo.currentTextChanged.connect(self.update_style)
        
        layout.addWidget(self.checkbox, stretch=1)
        layout.addWidget(self.color_btn)
        layout.addWidget(self.style_combo)
        
        self.setStyleSheet("QWidget { background: transparent; }")

    def update_visibility(self):
        self.settings['visible'] = self.checkbox.isChecked()
        self.window().update_plot()

    def update_color(self):
        self.settings['color'] = self.color_btn.color
        self.window().update_plot()

    def update_style(self, text):
        self.settings['style'] = text
        self.window().update_plot()

class ImageSizeDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Export Settings")
        self.setMinimumWidth(350)
        self.config_manager = config_manager
        
        layout = QFormLayout(self)
        
        # Load saved settings
        saved_settings = config_manager.config.get('image_export_settings', {})
        saved_width = saved_settings.get('width', 2560)
        saved_height = saved_settings.get('height', 1440)
        saved_dpi = saved_settings.get('dpi', 300)
        
        # Preset sizes
        self.combo_preset = QComboBox()
        self.presets = {
            "HD (1920x1080)": (1920, 1080),
            "Full HD (2560x1440)": (2560, 1440),
            "4K (3840x2160)": (3840, 2160),
            "A4 Portrait (2480x3508)": (2480, 3508),
            "A4 Landscape (3508x2480)": (3508, 2480),
            "Custom": (0, 0)
        }
        self.combo_preset.addItems(list(self.presets.keys()))
        self.combo_preset.setCurrentText("Full HD (2560x1440)")  # Default preset
        self.combo_preset.currentTextChanged.connect(self.on_preset_changed)
        layout.addRow("Preset Size:", self.combo_preset)
        
        # Width
        self.spin_width = QSpinBox()
        self.spin_width.setRange(100, 10000)
        self.spin_width.setValue(saved_width)
        self.spin_width.setSuffix(" px")
        layout.addRow("Width:", self.spin_width)
        
        # Height
        self.spin_height = QSpinBox()
        self.spin_height.setRange(100, 10000)
        self.spin_height.setValue(saved_height)
        self.spin_height.setSuffix(" px")
        layout.addRow("Height:", self.spin_height)
        
        # DPI
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(72, 600)
        self.spin_dpi.setValue(saved_dpi)
        self.spin_dpi.setSuffix(" dpi")
        layout.addRow("DPI:", self.spin_dpi)
        
        # Buttons
        btn_box = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.on_ok_clicked)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(ok_btn)
        btn_box.addWidget(cancel_btn)
        layout.addRow(btn_box)
    
    def on_preset_changed(self, preset_name):
        if preset_name in self.presets and preset_name != "Custom":
            width, height = self.presets[preset_name]
            self.spin_width.setValue(width)
            self.spin_height.setValue(height)
    
    def on_ok_clicked(self):
        # Save settings to config before closing
        self.config_manager.config['image_export_settings'] = {
            'width': self.spin_width.value(),
            'height': self.spin_height.value(),
            'dpi': self.spin_dpi.value()
        }
        self.accept()
    
    def get_settings(self):
        return {
            'width': self.spin_width.value(),
            'height': self.spin_height.value(),
            'dpi': self.spin_dpi.value()
        }

class StyleSettingsDialog(QDialog):
    def __init__(self, settings, callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Style Settings")
        self.setMinimumWidth(300)
        self.callback = callback
        
        layout = QFormLayout(self)
        
        # Title Size
        self.spin_title = QSpinBox()
        self.spin_title.setRange(8, 48)
        self.spin_title.setValue(settings.get('title_size', 14))
        layout.addRow("Title Size:", self.spin_title)
        
        # Axis Label
        self.spin_axis = QSpinBox()
        self.spin_axis.setRange(8, 36)
        self.spin_axis.setValue(settings.get('axis_label_size', 12))
        layout.addRow("Axis Label Size:", self.spin_axis)
        
        # Tick Label
        self.spin_tick = QSpinBox()
        self.spin_tick.setRange(6, 24)
        self.spin_tick.setValue(settings.get('tick_label_size', 10))
        layout.addRow("Tick Number Size:", self.spin_tick)
        
        # Legend
        self.spin_legend = QSpinBox()
        self.spin_legend.setRange(6, 24)
        self.spin_legend.setValue(settings.get('legend_size', 12))
        layout.addRow("Legend Size:", self.spin_legend)
        
        # Legend Position
        self.combo_legend_pos = QComboBox()
        self.legend_positions = {
            "Upper Right": "upper right",
            "Upper Left": "upper left",
            "Lower Right": "lower right",
            "Lower Left": "lower left"
        }
        self.combo_legend_pos.addItems(list(self.legend_positions.keys()))
        current_pos = settings.get('legend_position', 'lower right')
        # Find key by value
        for k, v in self.legend_positions.items():
            if v == current_pos:
                self.combo_legend_pos.setCurrentText(k)
                break
        layout.addRow("Legend Position:", self.combo_legend_pos)
        
        # Line Width
        self.spin_linewidth = QDoubleSpinBox()
        self.spin_linewidth.setRange(0.5, 10.0)
        self.spin_linewidth.setSingleStep(0.5)
        self.spin_linewidth.setValue(settings.get('line_width', 2.5))
        layout.addRow("Line Width:", self.spin_linewidth)
        
        # Custom Title
        self.input_custom_title = QLineEdit()
        self.input_custom_title.setText(settings.get('custom_title', ''))
        self.input_custom_title.setPlaceholderText("Leave empty for auto-generated title")
        layout.addRow("Custom Title:", self.input_custom_title)
        
        # Title Position
        self.combo_title_pos = QComboBox()
        self.title_positions = {
            "Top": "top",
            "Bottom (below X-axis)": "bottom"
        }
        self.combo_title_pos.addItems(list(self.title_positions.keys()))
        current_title_pos = settings.get('title_position', 'top')
        for k, v in self.title_positions.items():
            if v == current_title_pos:
                self.combo_title_pos.setCurrentText(k)
                break
        layout.addRow("Title Position:", self.combo_title_pos)

        # Connect all signals for real-time update
        self.spin_title.valueChanged.connect(self.on_changed)
        self.spin_axis.valueChanged.connect(self.on_changed)
        self.spin_tick.valueChanged.connect(self.on_changed)
        self.spin_legend.valueChanged.connect(self.on_changed)
        self.spin_linewidth.valueChanged.connect(self.on_changed)
        self.combo_legend_pos.currentTextChanged.connect(self.on_changed)
        self.input_custom_title.textChanged.connect(self.on_changed)
        self.combo_title_pos.currentTextChanged.connect(self.on_changed)
        
        # Add a Close button instead of Apply
        btn_box = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_box.addStretch()
        btn_box.addWidget(close_btn)
        layout.addRow(btn_box)

    def on_changed(self):
        new_styles = {
            'title_size': self.spin_title.value(),
            'axis_label_size': self.spin_axis.value(),
            'tick_label_size': self.spin_tick.value(),
            'legend_size': self.spin_legend.value(),
            'line_width': self.spin_linewidth.value(),
            'legend_position': self.legend_positions[self.combo_legend_pos.currentText()],
            'title_position': self.title_positions[self.combo_title_pos.currentText()],
            'custom_title': self.input_custom_title.text()  # Passed for immediate use but not saved
        }
        self.callback(new_styles)

    def update_visibility(self):
        self.settings['visible'] = self.checkbox.isChecked()
        self.window().update_plot() # Trigger main window update

    def update_color(self):
        self.settings['color'] = self.color_btn.color
        self.window().update_plot()

    def update_style(self):
        self.settings['style'] = self.style_combo.currentText()
        self.window().update_plot()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thermal Plotter")
        # Set a reasonable default size for laptops, but don't force maximize
        self.resize(1280, 800)
        
        self.parser = LogParser()
        
        # Ensure config directory checks
        config_path = os.path.join(os.getcwd(), "config", "config.json")
        self.config_manager = ConfigManager(config_path)
        
        # Data storage
        self.time_data = []
        self.temp_data = {}
        self.fan_data = {}
        self.loaded_data_map = {} # Store file_path -> parsed_data
        self.current_file_path = None
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # === LEFT PANEL ===
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        self.btn_load_file = QPushButton("Load Files")
        self.btn_load_file.clicked.connect(self.load_files)
        self.btn_load_folder = QPushButton("Load Folder")
        self.btn_load_folder.clicked.connect(self.load_folder)
        
        self.file_list = QListWidget()
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_file_context_menu)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(150)
        self.log_view.setPlaceholderText("Log output...")
        
        left_layout.addWidget(self.btn_load_file)
        left_layout.addWidget(self.btn_load_folder)
        left_layout.addWidget(QLabel("Log Files:"))
        left_layout.addWidget(self.file_list, stretch=1)
        self.file_list.itemClicked.connect(self.on_file_selected)
        left_layout.addWidget(QLabel("Status:"))
        left_layout.addWidget(self.log_view)
        
        # === CENTER PANEL (Config) ===
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(10, 10, 10, 10)
        
        # Config Group
        config_group = QGroupBox("Operations")
        config_layout = QVBoxLayout(config_group)
        
        btn_layout = QHBoxLayout()
        self.btn_save_config = QPushButton("Save Config")
        self.btn_save_config.clicked.connect(self.save_configuration)
        self.btn_load_config = QPushButton("Load Config")
        self.btn_load_config.clicked.connect(self.load_configuration)
        btn_layout.addWidget(self.btn_load_config)
        btn_layout.addWidget(self.btn_save_config)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Temperature + Fan Duty", "Temperature Only", "Fan Duty Only"])
        self.mode_combo.currentIndexChanged.connect(self.update_plot)
        
        self.btn_open_styles = QPushButton("Plot Styles")
        self.btn_open_styles.clicked.connect(self.open_styles_dialog)
        
        config_layout.addLayout(btn_layout)
        config_layout.addWidget(QLabel("Display Mode:"))
        config_layout.addWidget(self.mode_combo)
        config_layout.addWidget(self.btn_open_styles)
        center_layout.addWidget(config_group)

        
        # Temp Settings
        self.temp_group = QGroupBox("Temperature Sensors")
        # Add toggle all
        self.check_all_temp = QCheckBox("Show All Temps")
        self.check_all_temp.setChecked(True)
        self.check_all_temp.stateChanged.connect(lambda: self.toggle_all("temp_settings", self.check_all_temp.isChecked()))
        
        self.temp_scroll = QScrollArea()
        self.temp_scroll.setWidgetResizable(True)
        self.temp_container = QWidget()
        self.temp_layout = QVBoxLayout(self.temp_container)
        self.temp_scroll.setWidget(self.temp_container)
        
        t_layout_wrap = QVBoxLayout(self.temp_group)
        t_layout_wrap.addWidget(self.check_all_temp)
        t_layout_wrap.addWidget(self.temp_scroll)
        center_layout.addWidget(self.temp_group)

        # Fan Settings
        self.fan_group = QGroupBox("Fan Duty")
        self.check_all_fan = QCheckBox("Show All Fans")
        self.check_all_fan.setChecked(True)
        self.check_all_fan.stateChanged.connect(lambda: self.toggle_all("fan_settings", self.check_all_fan.isChecked()))
        
        self.fan_scroll = QScrollArea()
        self.fan_scroll.setWidgetResizable(True)
        self.fan_container = QWidget()
        self.fan_layout = QVBoxLayout(self.fan_container)
        self.fan_scroll.setWidget(self.fan_container)
        
        f_layout_wrap = QVBoxLayout(self.fan_group)
        f_layout_wrap.addWidget(self.check_all_fan)
        f_layout_wrap.addWidget(self.fan_scroll)
        center_layout.addWidget(self.fan_group)

        self.updating_ui = False

        # === RIGHT PANEL (Plot) ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.plotter = ThermalPlotter()
        
        # Bottom bar for buttons (Save Image)
        bottom_bar = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        
        bottom_layout.addStretch() # Push button to right
        
        self.btn_save_image = QPushButton("Save Image")
        self.btn_save_image.setFixedWidth(100) # Small fixed width
        self.btn_save_image.clicked.connect(self.save_plot_image) # Connected signal
        bottom_layout.addWidget(self.btn_save_image)
        
        right_layout.addWidget(self.plotter, stretch=1) # Force plotter to expand
        right_layout.addWidget(bottom_bar)
        
        # === STATUS BAR (Footer) ===
        # Place name and email at the far left
        self.status_bar = self.statusBar()
        self.lbl_footer = QLabel(" YouPeng, Wu (twpeng50606@gmail.com) 2026   v1.00")
        self.lbl_footer.setStyleSheet("color: gray; font-style: italic; font-size: 10pt; margin-bottom: 2px;")
        self.status_bar.addWidget(self.lbl_footer)

        left_panel.setMinimumWidth(200)
        center_panel.setMinimumWidth(280)

        # Global Style Fix: Minimalist Gray / No Borders
        self.setStyleSheet("""
            QMainWindow { background-color: #F5F5F5; }
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #CCCCCC; 
                margin-top: 10px; 
                padding-top: 10px;
                background-color: #FFFFFF;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }
            QPushButton { 
                background-color: #E0E0E0; 
                border: 1px solid #BCBCBC; 
                padding: 5px; 
                min-height: 20px;
            }
            QPushButton:hover { background-color: #D6D6D6; }
            QListWidget, QTextEdit { 
                border: 1px solid #CCCCCC; 
                background-color: #FFFFFF;
            }
        """)

        # Add to Splitter for adjustable width
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        
        # Adjust Ratios to be less cramped
        splitter.setStretchFactor(0, 1) # Left
        splitter.setStretchFactor(1, 2) # Center
        splitter.setStretchFactor(2, 3) # Right (Plot) - Still largest but less dominant

        splitter.setStretchFactor(0, 1) # Left
        splitter.setStretchFactor(1, 2) # Center
        splitter.setStretchFactor(2, 3) # Right (Plot) - Still largest but less dominant

        main_layout.addWidget(splitter)
        
        # Apply startup config
        self.populate_config_ui()

    def load_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(self, "Open Logs", "", "Text Files (*.txt);;All Files (*)")
        if filenames:
            self.file_list.clear()
            self.loaded_data_map = {}
            self.log_view.clear()
            
            logs_content = ""
            sorted_files = sorted(filenames)
            for f in sorted_files:
                self.file_list.addItem(os.path.basename(f))
                # Set absolute path in UserRole for later retrieval
                self.file_list.item(self.file_list.count()-1).setData(Qt.ItemDataRole.UserRole, f)
                
                data, err = self.parser.parse_file(f)
                if data:
                    self.loaded_data_map[f] = data
                    logs_content += f"Loaded {os.path.basename(f)}: {len(data['time'])} points.\n"
                    if err:
                         logs_content += f"Warning: {err}\n"
            
            if sorted_files:
                self.log_view.setText(logs_content)
                # Select the first one by default
                self.on_file_selected(self.file_list.item(0))
                self.file_list.setCurrentRow(0)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.file_list.clear()
            self.loaded_data_map = {}
            self.log_view.clear()

            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".txt")]
            files.sort()
            
            logs_content = ""
            for f in files:
                self.file_list.addItem(os.path.basename(f))
                self.file_list.item(self.file_list.count()-1).setData(Qt.ItemDataRole.UserRole, f)
                
                data, err = self.parser.parse_file(f)
                if data:
                    self.loaded_data_map[f] = data
                    logs_content += f"Loaded {os.path.basename(f)}: {len(data['time'])} points.\n"
            
            if files:
                self.log_view.setText(logs_content)
                self.on_file_selected(self.file_list.item(0))
                self.file_list.setCurrentRow(0)

    def on_file_selected(self, item):
        if not item:
            return
            
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path in self.loaded_data_map:
            data = self.loaded_data_map[file_path]
            self.time_data = data['time']
            self.temp_data = data['temp_data']
            self.fan_data = data['fan_data']
            self.current_file_path = file_path
            
            self.populate_config_ui()
            self.update_plot()

    def show_file_context_menu(self, position):
        item = self.file_list.itemAt(position)
        if not item:
            return
        
        from PyQt6.QtGui import QAction, QMenu
        menu = QMenu()
        rename_action = QAction("Rename File", self)
        rename_action.triggered.connect(lambda: self.rename_file(item))
        menu.addAction(rename_action)
        menu.exec(self.file_list.mapToGlobal(position))

    def rename_file(self, item):
        from PyQt6.QtWidgets import QInputDialog
        old_path = item.data(Qt.ItemDataRole.UserRole)
        old_dir = os.path.dirname(old_path)
        old_name = os.path.basename(old_path)
        
        new_name, ok = QInputDialog.getText(self, "Rename File", "New file name:", QLineEdit.EchoMode.Normal, old_name)
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(old_dir, new_name)
            try:
                # Rename on disk
                if os.path.exists(new_path):
                    QMessageBox.warning(self, "Error", "File already exists!")
                    return
                os.rename(old_path, new_path)
                
                # Update internal state
                data = self.loaded_data_map.pop(old_path)
                self.loaded_data_map[new_path] = data
                
                # Update UI
                item.setText(new_name)
                item.setData(Qt.ItemDataRole.UserRole, new_path)
                
                if self.current_file_path == old_path:
                    self.current_file_path = new_path
                    self.update_plot()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {e}")

    def open_styles_dialog(self):
        styles = self.config_manager.config.get('style_settings', {})
        dialog = StyleSettingsDialog(styles, self.apply_style_changes, self)
        dialog.exec()

    def apply_style_changes(self, new_styles):
        self.config_manager.config['style_settings'] = new_styles
        self.update_plot()

    def toggle_all(self, category, state):
        self.updating_ui = True
        try:
            layout = self.temp_layout if category == "temp_settings" else self.fan_layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), ConfigRow):
                    item.widget().checkbox.setChecked(state)
        finally:
            self.updating_ui = False
            self.update_plot()

    def merge_data(self, new_data):
        # Naive merge: Append. 
        # If time resets, we might have issues plotting continuous line.
        # But if files are sequential parts, time might continue?
        # If runs reset (Run 1 again), it's likely a separate run. 
        # For now, let's just Append.
        self.time_data.extend(new_data['time'])
        
        for k, v in new_data['temp_data'].items():
            if k not in self.temp_data:
                self.temp_data[k] = [] # Should pad?
            self.temp_data[k].extend(v)
            
        for k, v in new_data['fan_data'].items():
            if k not in self.fan_data:
                self.fan_data[k] = []
            self.fan_data[k].extend(v)

    def populate_config_ui(self):
        # Clear existing config widgets safely
        while self.temp_layout.count():
            item = self.temp_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        while self.fan_layout.count():
            item = self.fan_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Palette for auto-assignment
        # Standard matplotlib-like cycle
        palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]
        
        # Temp Rows
        for idx, name in enumerate(self.temp_data.keys()):
            # Init setting if missing
            if name not in self.config_manager.config['temp_settings']:
                self.config_manager.config['temp_settings'][name] = {"visible": True, "color": None, "style": "solid"}
            
            # Auto-assign color if None
            if self.config_manager.config['temp_settings'][name].get("color") is None:
                auto_col = palette[idx % len(palette)]
                self.config_manager.config['temp_settings'][name]["color"] = auto_col
            
            row = ConfigRow(name, "temp_settings", self.config_manager.config['temp_settings'][name], index=idx)
            self.temp_layout.addWidget(row)
            
        # Fan Rows
        for idx, name in enumerate(self.fan_data.keys()):
            if name not in self.config_manager.config['fan_settings']:
                self.config_manager.config['fan_settings'][name] = {"visible": True, "color": None, "style": "solid"}

            # Auto-assign color if None (use offset or reverse palette to distinguish from temps slightly?)
            if self.config_manager.config['fan_settings'][name].get("color") is None:
                # Use same palette but maybe shifted or just cycle
                # Since fans are on separate axis/group, same colors are fine, 
                # but let's shift to avoid exact match with first few temps if possible.
                auto_col = palette[(idx + 5) % len(palette)]
                self.config_manager.config['fan_settings'][name]["color"] = auto_col
            
            row = ConfigRow(name, "fan_settings", self.config_manager.config['fan_settings'][name], index=idx)
            self.fan_layout.addWidget(row)
        
        # Add spacer to push items top
        self.temp_layout.addStretch()
        self.fan_layout.addStretch()


    def update_plot(self):
        if hasattr(self, 'updating_ui') and self.updating_ui:
            return
            
        # Pass settings
        settings = self.config_manager.config
        mode_idx = self.mode_combo.currentIndex()
        
        # Pass filenames if available
        files_str = ""
        if self.current_file_path:
            files_str = os.path.basename(self.current_file_path)
            
        # 0: Dual, 1: Temp, 2: Fan
        self.plotter.plot_data(self.time_data, self.temp_data, self.fan_data, settings, mode_idx, title_suffix=files_str)

    def save_configuration(self):
        # Ensure config directory exists
        config_dir = os.path.join(os.getcwd(), "config")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        f, _ = QFileDialog.getSaveFileName(self, "Save Config", os.path.join(config_dir, "config.json"), "JSON (*.json)")
        if f:
            if not f.lower().endswith(".json"):
                f += ".json"
            
            try:
                self.config_manager.save_config(self.config_manager.config, f)
                QMessageBox.information(self, "Success", f"Configuration saved to {f}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save config: {e}")

    def load_configuration(self):
        config_dir = os.path.join(os.getcwd(), "config")
        if not os.path.exists(config_dir):
            config_dir = os.getcwd() # Fallback
            
        f, _ = QFileDialog.getOpenFileName(self, "Load Config", config_dir, "JSON (*.json)")
        if f:
            try:
                self.config_manager.config = self.config_manager.load_config(f)
                self.populate_config_ui() # Refresh UI
                self.update_plot()
                QMessageBox.information(self, "Success", f"Configuration loaded from {f}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load config: {e}")

    def save_plot_image(self):
        # First, show size selection dialog
        size_dialog = ImageSizeDialog(self.config_manager, self)
        if size_dialog.exec() != QDialog.DialogCode.Accepted:
            return  # User cancelled
        
        settings = size_dialog.get_settings()
        
        # Then show file save dialog
        f, _ = QFileDialog.getSaveFileName(self, "Save Image", "plot.png", "Images (*.png *.jpg)")
        if f:
            result = self.plotter.save_image(f, settings['width'], settings['height'], settings['dpi'])
            if result is True:
                QMessageBox.information(self, "Success", f"Image saved to {f}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to save image: {result}")
