# cidr_calc

CIDR notation calculator and subnet planner. Plan allocations, wildcard masks, optimal prefix sizing.

## Usage

```bash
# Plan subnet allocation from a /16
python3 cidr_calc.py plan 10.0.0.0/16 --sizes 50 100 200 25

# Show wildcard mask (for ACLs)
python3 cidr_calc.py wildcard 192.168.1.0/24

# Find optimal prefix for N hosts
python3 cidr_calc.py optimal --hosts 500

# Compare two networks
python3 cidr_calc.py diff 10.0.0.0/24 10.0.0.0/25

# Random addresses from a block
python3 cidr_calc.py random 172.16.0.0/12 --count 5
```

## Zero dependencies. Single file. Python 3.8+.
