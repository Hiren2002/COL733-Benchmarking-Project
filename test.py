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

# Default ports
REDIS_PORT = 6379
KEYDB_PORT = 6380

# Results directory
RESULTS_DIR = "benchmark_results_{}".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
os.makedirs(RESULTS_DIR, exist_ok=True)

# CLI arguments
parser = argparse.ArgumentParser(description="Redis vs KeyDB Benchmark Suite")
parser.add_argument("--tls", action="store_true", help="Run benchmarks in TLS mode")
parser.add_argument("--cert-dir", type=str, default="./KeyDB/tests/tls", help="Path to TLS certificates")
parser.add_argument("--max-threads", type=int, default=4, help="Threads for server and memtier")
args = parser.parse_args()

# TLS validation
if args.tls:
    cert_files = ["redis.crt", "redis.key", "ca.crt"]
    for file in cert_files:
        if not os.path.exists(os.path.join(args.cert_dir, file)):
            raise FileNotFoundError(f"Missing TLS certificate: {file}")

# Server startup commands
REDIS_TLS_CMD = f"redis-server --tls-port {REDIS_PORT} --port 0 --tls-cert-file {args.cert_dir}/redis.crt --tls-key-file {args.cert_dir}/redis.key --tls-ca-cert-file {args.cert_dir}/ca.crt --protected-mode no --io-threads {args.max_threads}"
KEYDB_TLS_CMD = f"keydb-server --tls-port {KEYDB_PORT} --port 0 --tls-cert-file {args.cert_dir}/redis.crt --tls-key-file {args.cert_dir}/redis.key --tls-ca-cert-file {args.cert_dir}/ca.crt --server-threads {args.max_threads} --server-thread-affinity true --protected-mode no"
REDIS_CMD = f"redis-server --port {REDIS_PORT} --protected-mode no --io-threads {args.max_threads}"
KEYDB_CMD = f"keydb-server --port {KEYDB_PORT} --server-threads {args.max_threads} --server-thread-affinity true --protected-mode no"

# Start server
def start_server(cmd, name):
    print(f"{GREEN}Starting {name}...{NC}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)  # Allow time for the server to initialize
    return process

# Stop server
def stop_server(process, name):
    print(f"{BLUE}Stopping {name}...{NC}")
    process.terminate()
    process.wait()

# Run memtier benchmark
def run_benchmark(name, port, tls, threads):
    output_prefix = os.path.join(RESULTS_DIR, f"{name}")
    cmd = [
        "memtier_benchmark",
        "--port", str(port),
        "--threads", str(threads),
        "--clients", "50",  # Reduced for single machine setup
        "--test-time", "30",
        "--hide-histogram",
        "--ratio", "1:1",
        "--json-out-file", f"{output_prefix}.json"
    ]
    if tls:
        cmd.extend([
            "--tls",
            "--cert", os.path.join(args.cert_dir, "redis.crt"),
            "--key", os.path.join(args.cert_dir, "redis.key"),
            "--cacert", os.path.join(args.cert_dir, "ca.crt")
        ])
    print(f"{BLUE}Running benchmark for {name}...{NC}")
    print(f"{GREEN}Command: {' '.join(cmd)}{NC}")
    subprocess.run(cmd)

# Plot results
def plot_results():
    throughput = {}
    latency = {}
    for json_file in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
        with open(json_file) as f:
            data = json.load(f)
            totals = data["Totals"][0]
            name = os.path.basename(json_file).split(".")[0]
            throughput[name] = totals["Ops/sec"]
            latency[name] = totals["Latency"]["Avg Latency"]
    # Plot
    plt.figure(figsize=(10, 5))
    plt.bar(throughput.keys(), throughput.values(), color=["blue", "orange"])
    plt.title("Ops/sec Comparison")
    plt.ylabel("Ops/sec")
    plt.savefig(os.path.join(RESULTS_DIR, "throughput.png"))
    plt.figure(figsize=(10, 5))
    plt.bar(latency.keys(), latency.values(), color=["blue", "orange"])
    plt.title("Latency Comparison")
    plt.ylabel("Avg Latency (ms)")
    plt.savefig(os.path.join(RESULTS_DIR, "latency.png"))

# Main execution
if __name__ == "__main__":
    print(f"{BLUE}Starting benchmarks...{NC}")
    redis_process = start_server(REDIS_TLS_CMD if args.tls else REDIS_CMD, "Redis")
    run_benchmark("Redis", REDIS_PORT, args.tls, args.max_threads)
    stop_server(redis_process, "Redis")
    keydb_process = start_server(KEYDB_TLS_CMD if args.tls else KEYDB_CMD, "KeyDB")
    run_benchmark("KeyDB", KEYDB_PORT, args.tls, args.max_threads)
    stop_server(keydb_process, "KeyDB")
    print(f"{BLUE}Generating plots...{NC}")
    plot_results()
    print(f"{GREEN}Benchmarks complete. Results and plots saved in {RESULTS_DIR}.{NC}")
