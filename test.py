import os
import datetime
import argparse
from utils import start_server, stop_server, run_benchmark
from plot import plot_results

# Text colors
BLUE = '\033[0;34m'
NC = '\033[0m'

# Default ports
REDIS_PORT = 6379
KEYDB_PORT = 6389

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Redis vs KeyDB Benchmark")
parser.add_argument("--max-threads", type=int, default=4)
parser.add_argument("--clients", type=int, nargs='+', default=[50])
parser.add_argument("--workload", type=str, choices=["balanced", "write-heavy", "read-heavy"], default="balanced")
parser.add_argument("--key-size", type=str, default="32")
parser.add_argument("--test-time", type=int, default=30)
parser.add_argument("--tls", action="store_true")
parser.add_argument("--cert-dir", type=str, default="./KeyDB/tests/tls")
args = parser.parse_args()

WORKLOAD_RATIOS = {"balanced": "1:1", "write-heavy": "1:9", "read-heavy": "9:1"}
RESULTS_DIR = f"benchmark_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
os.makedirs(RESULTS_DIR, exist_ok=True)

REDIS_CMD = f"redis-server --port {REDIS_PORT} --io-threads {args.max_threads} --protected-mode no"
KEYDB_CMD = f"keydb-server --port {KEYDB_PORT} --server-thread-affinity true --server-threads {args.max_threads} --protected-mode no"

if args.tls:
    REDIS_CMD = f"redis-server --tls-port {REDIS_PORT} --port 0 ..."
    KEYDB_CMD = f"keydb-server --tls-port {KEYDB_PORT} --port 0 ..."

# Main workflow
if __name__ == "__main__":
    print(f"{BLUE}Starting benchmarks...{NC}")
    
    try:
        redis_proc = start_server(REDIS_CMD, "Redis")
        run_benchmark("Redis", REDIS_PORT, args.tls, args.max_threads, args.clients[0], WORKLOAD_RATIOS[args.workload], args.key_size, args.test_time, args.cert_dir, os.path.join(RESULTS_DIR, "Redis"))
    finally:
        stop_server(redis_proc, "Redis", REDIS_PORT)

    try:
        keydb_proc = start_server(KEYDB_CMD, "KeyDB")
        run_benchmark("KeyDB", KEYDB_PORT, args.tls, args.max_threads, args.clients[0], WORKLOAD_RATIOS[args.workload], args.key_size, args.test_time, args.cert_dir, os.path.join(RESULTS_DIR, "KeyDB"))
    finally:
        stop_server(keydb_proc, "KeyDB", KEYDB_PORT)

    print(f"{BLUE}Generating plots...{NC}")
    plot_results(RESULTS_DIR)
    print(f"All benchmarks complete. Results in {RESULTS_DIR}.")
