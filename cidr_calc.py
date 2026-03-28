#!/usr/bin/env python3
"""cidr_calc — CIDR notation calculator and subnet planner.

Plan IP address allocations, calculate wildcard masks, find optimal CIDR blocks.

Usage:
    cidr_calc.py plan 10.0.0.0/16 --sizes 50 100 200 25
    cidr_calc.py wildcard 192.168.1.0/24
    cidr_calc.py optimal --hosts 500
    cidr_calc.py diff 10.0.0.0/24 10.0.0.0/25
    cidr_calc.py random 172.16.0.0/12 --count 5
"""

import sys
import json
import math
import random
import argparse
import ipaddress


def optimal_prefix(hosts_needed: int, ipv6: bool = False) -> int:
    """Find smallest prefix that fits N hosts."""
    max_bits = 128 if ipv6 else 32
    for prefix in range(max_bits, -1, -1):
        total = 2 ** (max_bits - prefix)
        usable = total - 2 if not ipv6 and prefix < 31 else total
        if usable >= hosts_needed:
            best = prefix
    return best


def cmd_plan(args):
    """Allocate subnets from a parent block for given host counts."""
    parent = ipaddress.ip_network(args.network, strict=False)
    sizes = sorted(args.sizes, reverse=True)  # largest first for best packing
    
    allocated = []
    remaining = [parent]
    
    for needed in sizes:
        # Find optimal prefix
        bits = (128 if parent.version == 6 else 32)
        for pfx in range(bits, -1, -1):
            total = 2 ** (bits - pfx)
            usable = total - 2 if parent.version == 4 and pfx < 31 else total
            if usable >= needed:
                target_prefix = pfx
                break
        
        # Find first remaining block that can contain this
        placed = False
        new_remaining = []
        for block in remaining:
            if not placed and block.prefixlen <= target_prefix:
                subnet = list(block.subnets(new_prefix=target_prefix))[0]
                allocated.append((needed, subnet))
                # Add leftover space
                leftovers = list(block.address_exclude(subnet))
                new_remaining.extend(sorted(leftovers))
                placed = True
            else:
                new_remaining.append(block)
        remaining = new_remaining
        
        if not placed:
            print(f'⚠ Cannot allocate {needed} hosts — insufficient space')
    
    print(f'Parent: {parent} ({parent.num_addresses} addresses)\n')
    total_used = 0
    for needed, subnet in allocated:
        usable = max(0, subnet.num_addresses - 2) if parent.version == 4 and subnet.prefixlen < 31 else subnet.num_addresses
        total_used += subnet.num_addresses
        print(f'  {str(subnet):20s}  {usable:>6} usable  (requested {needed})')
    
    waste = total_used - sum(args.sizes)
    util = sum(args.sizes) / total_used * 100 if total_used else 0
    print(f'\nTotal allocated: {total_used} addresses ({util:.1f}% utilization, {waste} overhead)')


def cmd_wildcard(args):
    """Show wildcard mask (inverse of netmask) — useful for ACLs."""
    net = ipaddress.ip_network(args.network, strict=False)
    print(f'Network:      {net.network_address}')
    print(f'Netmask:      {net.netmask}')
    print(f'Wildcard:     {net.hostmask}')
    print(f'Broadcast:    {net.broadcast_address}')
    print(f'First usable: {net.network_address + 1}')
    print(f'Last usable:  {net.broadcast_address - 1}')
    
    # Binary representation
    mask_int = int(net.netmask)
    binary = f'{mask_int:032b}'
    formatted = '.'.join(binary[i:i+8] for i in range(0, 32, 8))
    print(f'Binary mask:  {formatted}')


def cmd_optimal(args):
    """Find the optimal CIDR prefix for a given number of hosts."""
    ipv6 = args.ipv6
    max_bits = 128 if ipv6 else 32
    
    # Find exact fit
    for prefix in range(max_bits, -1, -1):
        total = 2 ** (max_bits - prefix)
        usable = total - 2 if not ipv6 and prefix < 31 else total
        if usable >= args.hosts:
            break
    
    total = 2 ** (max_bits - prefix)
    usable = total - 2 if not ipv6 and prefix < 31 else total
    waste = usable - args.hosts
    
    print(f'Hosts needed: {args.hosts}')
    print(f'Optimal prefix: /{prefix}')
    print(f'Total addresses: {total}')
    print(f'Usable hosts: {usable}')
    print(f'Wasted: {waste} ({waste/usable*100:.1f}%)')
    
    # Show nearby options
    print(f'\nNearby options:')
    for p in range(max(0, prefix - 2), min(max_bits + 1, prefix + 3)):
        t = 2 ** (max_bits - p)
        u = t - 2 if not ipv6 and p < 31 else t
        fit = '✓' if u >= args.hosts else '✗'
        print(f'  /{p:3d}: {u:>10,} usable hosts  {fit}')


def cmd_diff(args):
    """Show the difference between two networks."""
    a = ipaddress.ip_network(args.a, strict=False)
    b = ipaddress.ip_network(args.b, strict=False)
    
    print(f'Network A: {a} ({a.num_addresses} addresses)')
    print(f'Network B: {b} ({b.num_addresses} addresses)')
    print(f'Overlap: {"yes" if a.overlaps(b) else "no"}')
    
    if a.overlaps(b):
        if a.subnet_of(b):
            print(f'{a} is a subnet of {b}')
        elif b.subnet_of(a):
            print(f'{b} is a subnet of {a}')
        
        # Show non-overlapping parts
        if a != b:
            try:
                excluded = list(a.address_exclude(b)) if b.subnet_of(a) else list(b.address_exclude(a))
                print(f'Non-overlapping blocks:')
                for e in excluded:
                    print(f'  {e}')
            except ValueError:
                pass


def cmd_random(args):
    """Generate random addresses within a network."""
    net = ipaddress.ip_network(args.network, strict=False)
    hosts = list(net.hosts())
    if not hosts:
        hosts = [net.network_address]
    
    count = min(args.count, len(hosts))
    for addr in random.sample(hosts, count):
        print(addr)


def main():
    p = argparse.ArgumentParser(description='CIDR notation calculator and subnet planner')
    p.add_argument('--json', action='store_true')
    sub = p.add_subparsers(dest='cmd', required=True)

    sp = sub.add_parser('plan', help='Plan subnet allocation')
    sp.add_argument('network')
    sp.add_argument('--sizes', nargs='+', type=int, required=True, help='Host counts needed')
    sp.set_defaults(func=cmd_plan)

    sw = sub.add_parser('wildcard', help='Show wildcard/inverse mask')
    sw.add_argument('network')
    sw.set_defaults(func=cmd_wildcard)

    so = sub.add_parser('optimal', help='Find optimal prefix for host count')
    so.add_argument('--hosts', type=int, required=True)
    so.add_argument('--ipv6', action='store_true')
    so.set_defaults(func=cmd_optimal)

    sd = sub.add_parser('diff', help='Compare two networks')
    sd.add_argument('a')
    sd.add_argument('b')
    sd.set_defaults(func=cmd_diff)

    sr = sub.add_parser('random', help='Generate random addresses')
    sr.add_argument('network')
    sr.add_argument('--count', type=int, default=5)
    sr.set_defaults(func=cmd_random)

    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
