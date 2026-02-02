#!/bin/bash

# Default IPMI settings (Edit if needed or override via valid ipmitool config)
IPMI_HOST=""
IPMI_USER=""
IPMI_PASS=""

# Custom IPMI Raw Command Settings
# User can define NetFn, Cmd, and Data here
IPMI_RAW_NETFN=""
IPMI_RAW_CMD=""
IPMI_RAW_DATA=""

# Prompt for duration
read -p "Enter duration to run (in seconds): " duration

if ! [[ "$duration" =~ ^[0-9]+$ ]]; then
    echo "Error: Duration must be a number."
    exit 1
fi

start_time=$(date +%s)
end_time=$((start_time + duration))
count=0

# Create a log file name with timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")
logfile="thermal_log_${timestamp}.txt"

echo "Starting recording for ${duration} seconds..." | tee -a "$logfile"
echo "Log file: $logfile"

while [ $(date +%s) -lt $end_time ]; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    ((count++))
    
    echo "" | tee -a "$logfile"
    echo "Run number $count" | tee -a "$logfile"
    echo "echo [Elapsed time: $elapsed seconds]" | tee -a "$logfile"
    
    # Run IPMI commands
    # 1. Temperature Sensors
    ipmitool -I lanplus -H "$IPMI_HOST" -U "$IPMI_USER" -P "$IPMI_PASS" sdr type Temperature | tee -a "$logfile"
    
    # 2. Raw Fan Duty command using configured variables
    raw_output=$(ipmitool -I lanplus -H "$IPMI_HOST" -U "$IPMI_USER" -P "$IPMI_PASS" raw $IPMI_RAW_NETFN $IPMI_RAW_CMD $IPMI_RAW_DATA)
    echo " $raw_output" | tee -a "$logfile"
    
    # Small delay to prevent flooding, adjust if faster sampling is needed
    # The user asked for "efficiency", ipmitool itself takes time, so a small sleep or no sleep is fine.
    # Using 1s sleep as per reference batch file's intent (though it had timeout).
    sleep 1
done

echo "Execution Completed." | tee -a "$logfile"
echo "Data saved to $logfile"
