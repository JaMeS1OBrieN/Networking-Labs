# Networking Labs

Practical networking software projects focused on troubleshooting, monitoring, subnetting and infrastructure automation.

## Project 01 — NetPulse

A Python network diagnostic tool that checks multiple hosts concurrently and reports reachability, response time and packet loss. It can export results to JSON or CSV.

### What it demonstrates
- IPv4/IPv6 address and hostname validation
- ICMP diagnostics using the system ping utility
- Concurrent checks with a thread pool
- Latency and packet-loss calculations
- Structured reporting and file export
- Unit testing and clean Python project structure

### Requirements
- Python 3.10+
- No third-party packages required

### Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m netpulse --targets 192.168.1.1,1.1.1.1,google.com --count 4
```

Export results:
```bash
python -m netpulse --targets 192.168.1.1,1.1.1.1 --count 5 --format json --output report.json
python -m netpulse --targets 192.168.1.1,1.1.1.1 --count 5 --format csv --output report.csv
```

Run tests:
```bash
python -m unittest discover -s tests -v
```

> NetPulse uses ICMP echo requests via the local operating system. Firewalls may block ping, and a failed ping does not always mean a host or service is down. Only scan systems you own or are authorised to test.

## Roadmap
- [x] Concurrent host reachability checks
- [x] Latency and packet-loss reporting
- [x] JSON and CSV export
- [ ] TCP port and service checks
- [ ] Historical measurements and graphs
- [ ] Web dashboard and alerting
- [ ] Network discovery and topology visualisation

More labs will be added as they are built and tested.
