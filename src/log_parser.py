import re

class LogParser:
    def __init__(self):
        # Regex patterns based on the reference file
        self.re_run = re.compile(r"Run number\s+(\d+)")
        self.re_time = re.compile(r"echo \[Elapsed time:\s+(\d+)\s+seconds\]")
        # Matches: "SENSOR_NAME | XXh | ok | X.X | XX degrees C"
        self.re_temp = re.compile(r"^(\w+)\s+\|\s+[0-9A-Fa-f]+h\s+\|\s+ok\s+\|\s+[\d\.]+\s+\|\s+(\d+)\s+degrees\s+C")
        # Matches raw hex line like: " 01 46 46 46 ..."
        # We look for a line that consists mainly of hex pairs
        self.re_hex = re.compile(r"^\s*((?:[0-9A-Fa-f]{2}\s+)+[0-9A-Fa-f]{2})\s*$")

    def parse_file(self, filepath):
        """
        Parses a single log file and returns the data.
        Returns:
            dict: {
                'time': [t1, t2, ...],
                'temp_data': {'SensorName': [v1, v2, ...]},
                'fan_data': {'Fan_1': [v1, ...], 'Fan_2': ...}
            }
        """
        data = {
            'time': [],
            'temp_data': {},
            'fan_data': {}
        }
        
        current_time = None
        
        # Temporary storage for the current block's data
        # Because we might not get time immediately or order might vary slightly
        # But typically: Run -> Time -> Sensors -> Hex
        
        # We generally expect sequential reading. 
        # When we hit a new "Run number", we know a new sample is starting.
        # But actually, the log has "Run number" then "Elapsed time".
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            return None, str(e)

        # To handle potential multiple files or just loose structure, 
        # let's iterate line by line.
        
        # State tracking
        in_block = False
        
        # To handle the fact that we might see sensors before time in the very first block 
        # (though header usually is just one block), let's just append when we find data.
        # But we need to align lists.
        # Strategy: Initialize lists for all known keys to the same length as time list.
        # If a sensor is missing in a step, append None or previous value? 
        # For simplicity, let's process block-by-block if possible, or just robustly append.
        
        # SIMPLER STRATEGY: 
        # Scan for "Elapsed time". That marks a valid data point X-axis.
        # Collect all subsequent data until the next "Run number" or End of File.
        
        # First, let's collect all "Run number" indices to identify blocks.
        # Actually, let's just go line by line.
        
        temp_buffer = {} # sensor -> value
        fan_buffer = []  # list of duties
        current_time_val = 0
        
        # Because the file format is:
        # Run number X
        # Time ...
        # Data ...
        # Data ...
        # (Next Run)
        
        # We will commit the buffer to the main data structure when we hit a NEW "Run number" or EOF.
        
        for line in lines:
            line = line.strip()
            
            # Check for Run Number (Start of new block)
            if self.re_run.match(line):
                # If we have gathered data, commit it!
                # Wait, the FIRST run block starts, we haven't gathered anything yet.
                # So we commit "previous" block if distinct.
                # But easiest way is: Clear buffers on new Run.
                
                # Check if we have a valid time for the previous block.
                # Actually, the file structure in reference:
                # Line 1: sensor data (from init?)
                # Line 23: Run number 1
                # Line 24: Time 0
                # ...
                
                # We should only plot meaningful time series. The initial block (lines 1-21) has no time?
                # The script (reference) logs time loop immediately. 
                # Our new script also logs time loop.
                # So every data block has a time.
                pass

            # Check for Time
            m_time = self.re_time.search(line)
            if m_time:
                # If we have a previous time pending with data, we might need to verify alignment.
                # But simple case: We found a time -> This matches the data immediately following (or surrounding).
                current_time_val = int(m_time.group(1))
                data['time'].append(current_time_val)
                
                # Ensure all existing keys in main data have an entry for this new time step.
                # We will append NaN/None initially and fill update, or just append at the end of block?
                # Better: At the END of a block (before next run), push everything to lists.
                # But "Run number" is the delimiter.
                
                # Let's adjust:
                # 1. Encounter "Run number" -> Commit PREVIOUS buffer.
                # 2. Start new buffer.
                pass

        # RE-Write with Block Commit Strategy
        
        block_time = None
        block_temps = {}
        block_fans = []
        
        # Pre-scan to find all sensor names? Not strictly necessary if we use dict keys.
        
        processed_data = {
            'time': [],
            'temp_data': {}, # name -> list
            'fan_data': {}   # fan_idx -> list
        }
        
        current_run_idx = -1
        
        for line in lines:
            line = line.strip()
            
            # Start of a new run
            m_run = self.re_run.match(line)
            if m_run:
                # Commit previous block if it was valid
                if block_time is not None:
                    self._commit_block(processed_data, block_time, block_temps, block_fans)
                
                # Reset buffers
                block_time = None
                block_temps = {}
                block_fans = []
                current_run_idx = int(m_run.group(1))
                continue
            
            # Time
            m_time = self.re_time.search(line)
            if m_time:
                block_time = int(m_time.group(1))
                continue
            
            # Temp Sensor
            m_temp = self.re_temp.match(line)
            if m_temp:
                name = m_temp.group(1)
                val = int(m_temp.group(2))
                block_temps[name] = val
                continue
            
            # Raw Hex (Fans)
            # Avoid matching lines that are just text. 
            # The pattern requires hex pairs.
            if self.re_hex.match(line):
                # Filter out "Run number" lines or similar if regex is too loose (it shouldn't be)
                parts = line.split()
                # Check for likely hex byte structure
                if all(len(p) == 2 for p in parts):
                    # As per user request/description:
                    # "0x3c 0x41 0x00" command output.
                    # Reference file: " 01 46 46 46 ..."
                    # User said: "byte 1 onwards represent fan duties (e.g., 46 hex = 70%)"
                    # Python split 0-indexed.
                    # index 0: "01" (ignore?)
                    # index 1+: duties
                    try:
                        bytes_vals = [int(p, 16) for p in parts]
                        # Assuming index 0 is status/cmd echo, so fans start at index 1
                        if len(bytes_vals) > 1:
                            # Convert to duty % (0-100). Hex 46 = 70.
                            # 70 / 100 * 100? Or straight decimal value?
                            # 0x46 = 70 dec. "fanduty70.txt".
                            # So the value IS the percentage directly.
                            block_fans = bytes_vals[1:]
                    except ValueError:
                        pass
                continue

        # Commit last block
        if block_time is not None:
            self._commit_block(processed_data, block_time, block_temps, block_fans)
            
        return processed_data, None

    def _commit_block(self, all_data, time_val, temps, fans):
        all_data['time'].append(time_val)
        
        # update temps
        for name, val in temps.items():
            if name not in all_data['temp_data']:
                # Backfill with None if this is a new sensor encountered late
                all_data['temp_data'][name] = [None] * (len(all_data['time']) - 1)
            all_data['temp_data'][name].append(val)
            
        # fill missing sensors for this step with None
        for name in all_data['temp_data']:
            if name not in temps:
                all_data['temp_data'][name].append(None)
        
        # update fans
        for i, val in enumerate(fans):
            fan_name = f"Fan_{i+1}"
            if fan_name not in all_data['fan_data']:
                all_data['fan_data'][fan_name] = [None] * (len(all_data['time']) - 1)
            all_data['fan_data'][fan_name].append(val)
            
        # fill missing fans
        # Identify all known fan keys that were NOT updated in this step
        current_step_fans = {f"Fan_{i+1}" for i in range(len(fans))}
        for fname in all_data['fan_data']:
            if fname not in current_step_fans:
                all_data['fan_data'][fname].append(None)
