import os
import subprocess
import time
import datetime
import argparse

# Text colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Default ports
REDIS_PORT = 6379
KEYDB_PORT = 6379

# Parse CLI arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Redis vs KeyDB Benchmark Suite")
    parser.add_argument("--max-threads", type=int, default=4, help="Threads for server and memtier")
    parser.add_argument("--clients", type=int, nargs='+', default=[50], help="Number of clients for benchmarks (e.g., 10 50 100)")
    parser.add_argument("--workload", type=str, choices=["balanced", "write-heavy", "read-heavy"], default="balanced", help="Workload ratio (GET:SET)")
    parser.add_argument("--key-size", type=str, default="32", help="Key size in bytes (e.g., '32', '1024')")
    parser.add_argument("--test-time", type=int, default=30, help="Duration of each benchmark (seconds)")
    parser.add_argument("--tls", action="store_true", help="Run benchmarks in TLS mode")
    parser.add_argument("--cert-dir", type=str, default="./KeyDB/tests/tls", help="Path to TLS certificates")
    parser.add_argument("--simulate-latency", type=int, default=0, help="Simulate network latency in ms")
    return parser.parse_args()

# Start server
def start_server(cmd, name):
    print(f"{GREEN}Starting {name}...{NC}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)  # Allow time for the server to initialize
    return process

# Stop server
def stop_server(process, name):
    try:
        print(f"{BLUE}Stopping {name}...{NC}")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"Error stopping {name}: {e}")

# Run memtier benchmark
def run_benchmark(name, port, tls, threads, clients, ratio, key_size, test_time, cert_dir, simulate_latency, results_dir):
    output_prefix = os.path.join(results_dir, f"{name}_TLS{tls}_{threads}threads_{clients}clients_{ratio}_{key_size}key_{test_time}s")
    cmd = [
        "memtier_benchmark",
        "--port", str(port),
        "--threads", str(threads),
        "--clients", str(clients),
        "--test-time", str(test_time),
        "--data-size", str(key_size),
        "--ratio", ratio,
        "--hide-histogram",
        "--json-out-file", f"{output_prefix}.json"
    ]
    if tls:
        cmd.extend([
            "--tls",
            "--cert", os.path.join(cert_dir, "keydb.crt"),
            "--key", os.path.join(cert_dir, "keydb.key"),
            "--cacert", os.path.join(cert_dir, "ca.crt")
        ])
    if simulate_latency > 0:
        cmd.extend(["--latency", str(simulate_latency)])
    print(f"{BLUE}Running benchmark for {name} with {clients} clients, ratio {ratio}, key size {key_size} bytes...{NC}")
    subprocess.run(cmd)
