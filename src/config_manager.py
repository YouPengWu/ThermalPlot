import json
import os

class ConfigManager:
    def __init__(self, config_file="thermal_plot_config.json"):
        self.config_file = config_file
        self.default_config = {
            "temp_settings": {}, # SensorName: {color: "#RRGGBB", style: "solid/dashed", visible: true}
            "fan_settings": {},   # FanName: {color: "#RRGGBB", style: "solid/dashed", visible: true}
            "style_settings": {   # New global style settings
                "title_size": 14,
                "axis_label_size": 12,
                "tick_label_size": 10,
                "legend_size": 12,
                "line_width": 2.5,
                "legend_position": "lower right"
            }
        }
        self.config = self.load_config()

    def load_config(self, filepath=None):
        target = filepath if filepath else self.config_file
        config = self.default_config.copy()
        
        if os.path.exists(target):
            try:
                with open(target, 'r') as f:
                    loaded_data = json.load(f)
                    # Deep merge or at least top-level merge
                    for key, value in loaded_data.items():
                        if isinstance(config.get(key), dict) and isinstance(value, dict):
                            config[key].update(value)
                        else:
                            config[key] = value
                return config
            except Exception as e:
                print(f"Error loading config: {e}")
                return config
        return config

    def save_config(self, current_settings, filepath=None):
        target = filepath if filepath else self.config_file
        try:
            with open(target, 'w') as f:
                json.dump(current_settings, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_setting(self, category, name):
        """
        Get setting for a specific item (temp or fan).
        Returns dict with color, style, visible.
        If not found, returns None (let UI decide default).
        """
        if category in self.config and name in self.config[category]:
            return self.config[category][name]
        return None

    def update_setting(self, category, name, key, value):
        if category not in self.config:
            self.config[category] = {}
        if name not in self.config[category]:
            self.config[category][name] = {"color": "#000000", "style": "solid", "visible": True}
        
        self.config[category][name][key] = value
