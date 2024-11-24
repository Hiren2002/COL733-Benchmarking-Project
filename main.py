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
KEYDB_PORT = 6379

# Results directory
RESULTS_DIR = "benchmark_results_{}".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
os.makedirs(RESULTS_DIR, exist_ok=True)

# CLI arguments
parser = argparse.ArgumentParser(description="Redis vs KeyDB Benchmark Suite")
parser.add_argument("--max-threads", type=int, default=4, help="Threads for server and memtier")
parser.add_argument("--clients", type=int, nargs='+', default=[50], help="Number of clients for benchmarks (e.g., 10 50 100)")
parser.add_argument("--workload", type=str, choices=["balanced", "write-heavy", "read-heavy"], default="balanced", help="Workload ratio (GET:SET)")
parser.add_argument("--key-size", type=str, default="32", help="Key size in bytes (e.g., '32', '1024')")
parser.add_argument("--test-time", type=int, default=30, help="Duration of each benchmark (seconds)")
parser.add_argument("--tls", action="store_true", help="Run benchmarks in TLS mode")
parser.add_argument("--cert-dir", type=str, default="./KeyDB/tests/tls", help="Path to TLS certificates")
parser.add_argument("--simulate-latency", type=int, default=0, help="Simulate network latency in ms")
args = parser.parse_args()

# TLS validation
if args.tls:
    cert_files = ["keydb.crt", "keydb.key", "ca.crt"]
    for file in cert_files:
        if not os.path.exists(os.path.join(args.cert_dir, file)):
            raise FileNotFoundError(f"Missing TLS certificate: {file}")

# Server startup commands
REDIS_TLS_CMD = f"redis-server --tls-port {REDIS_PORT} --port 0 --tls-cert-file {args.cert_dir}/keydb.crt --tls-key-file {args.cert_dir}/keydb.key --tls-ca-cert-file {args.cert_dir}/ca.crt --io-threads {args.max_threads} --protected-mode no "
KEYDB_TLS_CMD = f"keydb-server --tls-port {KEYDB_PORT} --port 0 --tls-cert-file {args.cert_dir}/keydb.crt --tls-key-file {args.cert_dir}/keydb.key --tls-ca-cert-file {args.cert_dir}/ca.crt --server-thread-affinity true --server-threads {args.max_threads} --protected-mode no "
REDIS_CMD = f"redis-server --port {REDIS_PORT} --io-threads {args.max_threads} --protected-mode no "
KEYDB_CMD = f"keydb-server --port {KEYDB_PORT} --server-thread-affinity true --server-threads {args.max_threads} --protected-mode no "

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
def run_benchmark(name, port, tls, threads, clients, ratio, key_size, test_time):
    output_prefix = os.path.join(RESULTS_DIR, f"{name}_TLS{tls}_{threads}threads_{clients}clients_{ratio}_{key_size}key_{test_time}s")
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
            "--cert", os.path.join(args.cert_dir, "keydb.crt"),
            "--key", os.path.join(args.cert_dir, "keydb.key"),
            "--cacert", os.path.join(args.cert_dir, "ca.crt")
        ])
    if args.simulate_latency > 0:
        cmd.extend(["--latency", str(args.simulate_latency)])
    print(f"{BLUE}Running benchmark for {name} with {clients} clients, ratio {ratio}, key size {key_size} bytes...{NC}")
    subprocess.run(cmd)

# Map workload types to ratios
WORKLOAD_RATIOS = {
    "balanced": "1:1",
    "write-heavy": "1:9",
    "read-heavy": "9:1"
}
    
def plot_results():
    # Initialize dictionaries for throughput and latency
    throughput = {}
    avg_latency = {}
    max_latency = {}

    # Read each JSON file in the results directory
    for json_file in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
        with open(json_file) as f:
            data = json.load(f)
            totals = data["ALL STATS"]["Totals"]

            # Extract metrics
            name = os.path.basename(json_file).split(".")[0]  # Extract Redis/KeyDB from filename
            throughput[name] = totals["Ops/sec"]
            avg_latency[name] = totals["Average Latency"]
            max_latency[name] = totals["Max Latency"]
            
    # Plot throughput comparison
    plt.figure(figsize=(12, 6))
    plt.bar(throughput.keys(), throughput.values(), color=["blue", "orange"], alpha=0.8)
    plt.title("Throughput Comparison (Ops/sec)")
    plt.ylabel("Ops/sec")
    plt.xlabel("Server")
    plt.grid(axis='y', linestyle="--", alpha=0.7)

    # Save and display throughput plot
    throughput_plot = os.path.join(RESULTS_DIR, "throughput_comparison.png")
    plt.savefig(throughput_plot)
    print(f"Throughput plot saved: {throughput_plot}")
    # plt.show()

    # Plot latency comparison
    plt.figure(figsize=(12, 6))
    x_positions = list(avg_latency.keys())
    plt.bar(x_positions, avg_latency.values(), label="Avg Latency", color=["blue", "orange"], alpha=0.8)
    # plt.bar(x_positions, max_latency.values(), label="Max Latency", color=["lightblue", "peachpuff"], alpha=0.6)
    plt.title("Latency Comparison")
    plt.ylabel("Latency (ms)")
    plt.xlabel("Server")
    plt.legend()
    plt.grid(axis='y', linestyle="--", alpha=0.7)

    # Save and display latency plot
    latency_plot = os.path.join(RESULTS_DIR, "latency_comparison.png")
    plt.savefig(latency_plot)
    print(f"Latency plot saved: {latency_plot}")
    # plt.show()

# Main execution
if __name__ == "__main__":
        
    print(f"{BLUE}Starting benchmarks...{NC}")
    try:
        redis_process = start_server(REDIS_TLS_CMD if args.tls else REDIS_CMD, "Redis")
        run_benchmark("Redis", REDIS_PORT, args.tls, args.max_threads, args.clients[0], WORKLOAD_RATIOS[args.workload], args.key_size, args.test_time)
    except Exception as e:
        print(f"Error running Redis benchmark: {e}")
    stop_server(redis_process, "Redis")
    
    try:
        keydb_process = start_server(KEYDB_TLS_CMD if args.tls else KEYDB_CMD, "KeyDB")
        run_benchmark("KeyDB", KEYDB_PORT, args.tls, args.max_threads, args.clients[0], WORKLOAD_RATIOS[args.workload], args.key_size, args.test_time)
    except Exception as e:
        print(f"Error running KeyDB benchmark: {e}")
    stop_server(keydb_process, "KeyDB")
    
    print(f"{BLUE}Generating plots...{NC}")
    plot_results()    
    
    print(f"{GREEN}All benchmarks complete! Results saved in {RESULTS_DIR}.{NC}")
