#!/usr/bin/env python3
"""
Simple multithreaded TCP port scanner.

For educational use only. Scan only your own machine (127.0.0.1),
scanme.nmap.org, or systems you have written permission to test.
"""

import argparse
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Common ports and their services (fallback: socket.getservbyport)
COMMON_SERVICES = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    27017: "MongoDB",
    8000: "HTTP-ALT",
    8080: "HTTP-ALT",
}


def scan_port(host, port, timeout):
    """Return the port number if it is open, otherwise None."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            if sock.connect_ex((host, port)) == 0:
                return port
    except OSError:
        pass
    return None


def get_service(port):
    """Look up the service name for a port."""
    if port in COMMON_SERVICES:
        return COMMON_SERVICES[port]
    try:
        return socket.getservbyport(port, "tcp").upper()
    except OSError:
        return "Unknown"


def parse_args():
    parser = argparse.ArgumentParser(description="Simple TCP port scanner")
    parser.add_argument("host", help="Target hostname or IP (e.g. 127.0.0.1)")
    parser.add_argument("-s", "--start", type=int, default=1, help="Start port (default 1)")
    parser.add_argument("-e", "--end", type=int, default=1024, help="End port (default 1024)")
    parser.add_argument("-t", "--threads", type=int, default=100, help="Number of threads (default 100)")
    parser.add_argument("--timeout", type=float, default=0.5, help="Timeout per port in seconds (default 0.5)")
    parser.add_argument("-o", "--output", help="Save results to this file")
    return parser.parse_args()


def main():
    args = parse_args()

    if not (1 <= args.start <= args.end <= 65535):
        sys.exit("Error: ports must satisfy 1 <= start <= end <= 65535")

    try:
        ip = socket.gethostbyname(args.host)
    except socket.gaierror:
        sys.exit(f"Error: could not resolve host '{args.host}'")

    print(f"Scanning {args.host} ({ip}) ports {args.start}-{args.end}")
    started = datetime.now()

    ports = range(args.start, args.end + 1)
    with ThreadPoolExecutor(max_workers=args.threads) as pool:
        results = pool.map(lambda p: scan_port(ip, p, args.timeout), ports)
        open_ports = sorted(p for p in results if p is not None)

    elapsed = datetime.now() - started

    lines = [f"Scan report for {args.host} ({ip})", f"{'PORT':<10}{'STATE':<10}SERVICE"]
    for port in open_ports:
        lines.append(f"{port:<10}{'open':<10}{get_service(port)}")
    if not open_ports:
        lines.append("No open ports found in the given range.")
    lines.append(f"Scanned {len(ports)} ports in {elapsed.total_seconds():.2f}s")

    report = "\n".join(lines)
    print(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
