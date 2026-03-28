#!/usr/bin/env python3
"""cidr_calc - CIDR subnet calculator."""
import sys, ipaddress
if __name__ == "__main__":
    if len(sys.argv) < 2: print("Usage: cidr_calc <CIDR>"); sys.exit(1)
    net = ipaddress.ip_network(sys.argv[1], strict=False)
    print(f"Network: {net.network_address}")
    print(f"Broadcast: {net.broadcast_address}")
    print(f"Netmask: {net.netmask}")
    print(f"Hosts: {net.num_addresses - 2 if net.prefixlen < 31 else net.num_addresses}")
    print(f"Range: {net.network_address + 1} - {net.broadcast_address - 1}" if net.prefixlen < 31 else f"Range: {net.network_address} - {net.broadcast_address}")
    print(f"Prefix: /{net.prefixlen}")
