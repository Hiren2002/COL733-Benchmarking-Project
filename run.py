import os
import subprocess
import datetime
import glob
import json
import time
import argparse
import matplotlib.pyplot as plt

# Text colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Default ports for Redis and KeyDB
DEFAULT_REDIS_PORT = 6379
DEFAULT_KEYDB_PORT = 6389

# Create results directory with timestamp
RESULTS_DIR = "benchmark_results_{}".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
os.makedirs(RESULTS_DIR, exist_ok=True)

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Redis and KeyDB Benchmark Suite")
parser.add_argument("--tls", action="store_true", help="Run benchmarks in TLS mode")
parser.add_argument("--redis-port", type=int, default=DEFAULT_REDIS_PORT, help="Redis server port")
parser.add_argument("--keydb-port", type=int, default=DEFAULT_KEYDB_PORT, help="KeyDB server port")
parser.add_argument("--cert-dir", type=str, default="./KeyDB/tests/tls", help="Path to TLS certificates")
parser.add_argument("--max-clients", type=int, default=50, help="Maximum number of clients for benchmarks")
parser.add_argument("--max-threads", type=int, default=4, help="Maximum number of threads for benchmarks")
args = parser.parse_args()

# Validate TLS certificate paths
if args.tls:
    for cert_file in ["client.crt", "client.key", "ca.crt"]:
        cert_path = os.path.join(args.cert_dir, cert_file)
        if not os.path.exists(cert_path):
            raise FileNotFoundError(f"TLS certificate file not found: {cert_path}")

# Function to check if service is responding
def check_service(port, name, tls, service_type):
    """Check if Redis or KeyDB is running on the specified port."""
    
    if service_type == "Redis":
        try:
            cmd = ['redis-cli', '-p', str(port), 'ping']
            if tls:
                cmd.extend([
                    '--tls',
                    '--cert', os.path.join(args.cert_dir, "client.crt"),
                    '--key', os.path.join(args.cert_dir, "client.key"),
                    '--cacert', os.path.join(args.cert_dir, "ca.crt")
                ])
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"{GREEN}{name} is responding on port {port}{NC}")
        except subprocess.CalledProcessError as e:
            if tls:
                print(f"{BLUE}TLS issue detected: Ensure {name} is configured with proper TLS certificates{NC}")
            print(f"{BLUE}Error: {name} on port {port} is not responding ({service_type}){NC}")
            exit(1)
            
    elif service_type == "KeyDB":
        pass

# Function to run a single benchmark scenario
def run_benchmark_scenario(name, port, scenario, ratio, rate_limit, tls):
    output_prefix = os.path.join(RESULTS_DIR, f"{name}_{scenario}")
    cmd = [
        'memtier_benchmark',
        '--port', str(port),
        '--threads', str(min(args.max_threads, 4)),
        '--clients', str(min(args.max_clients, 50)),
        '--test-time', '30',
        '--data-size', '32',
        '--key-pattern', 'P:P',
        '--key-minimum', '1',
        '--key-maximum', '100000',
        '--print-percentiles', '50,90,95,99,99.9',
        '--json-out-file', f'{output_prefix}.json',
        '--hdr-file-prefix', output_prefix,
        '--ratio', ratio
    ]
    if tls:
        cmd.append('--tls')
    if rate_limit:
        cmd.extend(['--rate-limit', rate_limit])
    print(f"{BLUE}Running {scenario} benchmark for {name}...{NC}")
    print(f"{GREEN}Running command: {' '.join(cmd)}{NC}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{BLUE}Error running benchmark: {e}{NC}")
    time.sleep(5)

# Function to run all benchmark scenarios for a service
def run_service_benchmarks(name, port, tls, service_type):
    print(f"{BLUE}Starting benchmarks for {name} on port {port}{NC}")
    check_service(port, name, tls, service_type)
    scenarios = [
        ("balanced", "1:1", ""),
        ("write_heavy", "3:1", ""),
        ("read_heavy", "1:3", ""),
        ("rate_limited", "1:1", "10000")
    ]
    for scenario in scenarios:
        run_benchmark_scenario(name, port, *scenario, tls)

# Function to generate summary report
def generate_summary_report():
    summary_path = os.path.join(RESULTS_DIR, "summary.txt")
    with open(summary_path, "w") as summary_file:
        summary_file.write("Benchmark Results Summary\n")
        summary_file.write("=======================\n")
        summary_file.write(f"Timestamp: {datetime.datetime.now()}\n\n")
        for json_file in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
            summary_file.write(f"Results from {os.path.basename(json_file)}:\n")
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    totals = data.get("Totals", [{}])[0]
                    ops_sec = totals.get("Ops/sec", 0)
                    latency = totals.get("Latency", {})
                    summary_file.write(f"Totals:\n")
                    summary_file.write(f"  Ops/sec: {ops_sec}\n")
                    summary_file.write("  Latency:\n")
                    for key, value in latency.items():
                        summary_file.write(f"    {key}: {value}\n")
                    summary_file.write("\n")
            except json.JSONDecodeError:
                print(f"{BLUE}Warning: Invalid JSON file {json_file}{NC}")

# Main execution
if __name__ == "__main__":
    print(f"{BLUE}Starting benchmark suite...{NC}")
    print(f"{GREEN}Testing Redis...{NC}")
    run_service_benchmarks("redis", args.redis_port, args.tls, "Redis")
    print(f"{GREEN}Testing KeyDB...{NC}")
    run_service_benchmarks("keydb", args.keydb_port, args.tls, "KeyDB")
    
    # Generate summary report
    print(f"{BLUE}Generating summary report...{NC}")
    generate_summary_report()
    print(f"{BLUE}Benchmarks complete! Results are in the {RESULTS_DIR} directory{NC}")
    print(f"{BLUE}Check {RESULTS_DIR}/summary.txt for a quick overview{NC}")
