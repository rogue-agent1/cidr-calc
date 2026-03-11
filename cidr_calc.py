#!/usr/bin/env python3
"""CIDR calculator — subnet info, contains, overlap. Zero deps."""
import sys

def ip_to_int(ip): return sum(int(o)<<(24-8*i) for i,o in enumerate(ip.split('.')))
def int_to_ip(n): return '.'.join(str((n>>s)&0xFF) for s in [24,16,8,0])

class CIDR:
    def __init__(self, notation):
        ip, prefix = notation.split('/')
        self.prefix = int(prefix)
        self.mask = (0xFFFFFFFF << (32-self.prefix)) & 0xFFFFFFFF
        self.network = ip_to_int(ip) & self.mask
        self.broadcast = self.network | ~self.mask & 0xFFFFFFFF
    def contains(self, ip):
        return ip_to_int(ip) & self.mask == self.network
    def overlaps(self, other):
        return not (self.broadcast < other.network or other.broadcast < self.network)
    def host_count(self):
        return max(0, 2**(32-self.prefix) - 2) if self.prefix < 31 else 2**(32-self.prefix)
    def info(self):
        return {"network": int_to_ip(self.network), "broadcast": int_to_ip(self.broadcast),
                "mask": int_to_ip(self.mask), "hosts": self.host_count(), "prefix": self.prefix}

def test():
    c = CIDR("192.168.1.0/24")
    assert c.contains("192.168.1.50")
    assert not c.contains("192.168.2.1")
    assert c.host_count() == 254
    assert c.info()["broadcast"] == "192.168.1.255"
    c2 = CIDR("192.168.1.128/25")
    assert c.overlaps(c2)
    c3 = CIDR("10.0.0.0/8")
    assert not c.overlaps(c3)
    assert c3.host_count() == 16777214
    print(f"/24 info: {c.info()}")
    print(f"/8 hosts: {c3.host_count():,}")
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1: print(CIDR(sys.argv[1]).info())
    else: test()
