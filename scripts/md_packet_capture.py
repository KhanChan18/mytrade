#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTP Packet Capture Script
Use scapy to capture packets from CTP server and save to pcap file
"""

import os
import sys
import time
import threading
import subprocess
import yaml
import re
from scapy.all import sniff, wrpcap

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Global variables
incoming_packets = []  # Packets from CTP server to local
outgoing_packets = []  # Packets from local to CTP server
stop_sniffing = False


def read_boot_config():
    """
    Read CTP server configuration from boot.yml
    """
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../boot.yml'))
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Get current platform and environment
        platform = config['APP_CONFIG']['platform']
        env = config['APP_CONFIG']['env']
        
        # Get trade server configuration
        trade_server = config['CTP_SERVER'][platform][env]['trade_server']
        
        # Extract IP and port from trade_server (format: tcp://ip:port)
        match = re.match(r'tcp://([^:]+):(\d+)', trade_server)
        if match:
            ip = match.group(1)
            port = int(match.group(2))
            return ip, port
        else:
            print(f"Invalid trade_server format: {trade_server}")
            return "182.254.243.31", 40001
            
    except Exception as e:
        print(f"Error reading boot.yml: {e}")
        return "182.254.243.31", 40001


def capture_packets(server_ip, server_port, incoming_file, outgoing_file):
    """
    Capture packets to and from CTP server
    """
    global incoming_packets, outgoing_packets, stop_sniffing
    
    # Use a loop with a timeout instead of relying on packet_handler return value
    def packet_handler(packet):
        """Packet processing function"""
        if packet.haslayer('IP') and packet.haslayer('TCP'):
            # Check if this is a packet related to the CTP server
            if (packet['IP'].src == server_ip and packet['TCP'].sport == server_port) or \
               (packet['IP'].dst == server_ip and packet['TCP'].dport == server_port):
                
                if packet['IP'].src == server_ip and packet['TCP'].sport == server_port:
                    # Packet from CTP server to local
                    incoming_packets.append(packet)
                else:
                    # Packet from local to CTP server
                    outgoing_packets.append(packet)
                    
                total_packets = len(incoming_packets) + len(outgoing_packets)
                print(f"Captured packets: Total {total_packets} (Incoming: {len(incoming_packets)}, Outgoing: {len(outgoing_packets)})", end='\r')
    
    # Start sniffing in a non-blocking way
    print(f"Starting packet capture for {server_ip}:{server_port}...")
    print(f"Incoming packets will be saved to: {incoming_file}")
    print(f"Outgoing packets will be saved to: {outgoing_file}")
    
    # Sniff with a small timeout, then check stop condition
    while not stop_sniffing:
        sniff(filter=f"tcp and host {server_ip} and port {server_port}", 
              prn=packet_handler, store=0, timeout=1)
    
    # Save captured packets
    if incoming_packets:
        wrpcap(incoming_file, incoming_packets)
        print(f"\nSaved {len(incoming_packets)} incoming packets to {incoming_file}")
    else:
        print("\nNo incoming packets captured")
        
    if outgoing_packets:
        wrpcap(outgoing_file, outgoing_packets)
        print(f"Saved {len(outgoing_packets)} outgoing packets to {outgoing_file}")
    else:
        print("No outgoing packets captured")


def start_process(process_type, dev_test=False):
    """
    Start either trade_controller or data_collector process
    """
    print(f"Starting {process_type} process...")
    
    # Build command
    cmd = [
        sys.executable,
        "app_entry.py",
        process_type
    ]
    
    # Add --dev-test parameter if requested
    if dev_test:
        cmd.append("--dev-test")
    
    # Start process
    process = subprocess.Popen(cmd, 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT,
                              universal_newlines=True,
                              encoding='utf-8',
                              cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Print output in real-time
    def print_output():
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(line.strip())
    
    output_thread = threading.Thread(target=print_output, daemon=True)
    output_thread.start()
    
    return process


def main():
    """
    Main function
    """
    print("CTP Packet Capture Script")
    print("=" * 50)
    
    # Read CTP server configuration
    CTP_SERVER_IP, CTP_TRADE_PORT = read_boot_config()
    
    # Define output files for incoming and outgoing packets
    SCRIPT_DIR = os.path.dirname(__file__)
    INCOMING_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "md_test_incoming.pcap"))
    OUTGOING_FILE = os.path.abspath(os.path.join(SCRIPT_DIR, "md_test_outgoing.pcap"))
    
    # Start packet capture thread
    capture_thread = threading.Thread(target=capture_packets, 
                                     args=(CTP_SERVER_IP, CTP_TRADE_PORT, INCOMING_FILE, OUTGOING_FILE), 
                                     daemon=True)
    capture_thread.start()
    
    # Start data_collector process with --dev-test parameter
    data_collector_process = start_process("data_collector", dev_test=True)
    
    try:
        # Wait for data_collector process to finish
        data_collector_process.wait()
        print("data_collector process finished")
    except KeyboardInterrupt:
        print("\nUser interrupted, stopping all processes...")
        data_collector_process.terminate()
    
    # Stop packet capture
    global stop_sniffing
    stop_sniffing = True
    
    # Wait for capture thread to complete
    capture_thread.join(timeout=2)
    print("\nScript execution completed")

if __name__ == "__main__":
    main()