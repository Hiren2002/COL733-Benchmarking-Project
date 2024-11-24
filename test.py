import os
import datetime
from utils import parse_args, start_server, stop_server, run_benchmark
from plot import plot_results

# Main execution
if __name__ == "__main__":
    args = parse_args()

    # Validate and create results directory
    results_dir = "benchmark_results_{}".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(results_dir, exist_ok=True)

    # TLS validation
    if args.tls:
        cert_files = ["keydb.crt", "keydb.key", "ca.crt"]
        for file in cert_files:
            if not os.path.exists(os.path.join(args.cert_dir, file)):
                raise FileNotFoundError(f"Missing TLS certificate: {file}")

    # Server commands
    redis_cmd = f"redis-server --tls-port {args.cert_dir}/keydb.crt ..." if args.tls else "redis-server ..."
    keydb_cmd = f"keydb-server --tls-port {args.cert_dir}/keydb.crt ..." if args.tls else "keydb-server ..."
    
    print("Starting benchmarks...")
    try:
        redis_process = start_server(redis_cmd, "Redis")
        run_benchmark("Redis", 6379, args.tls, args.max_threads, args.clients[0], args.workload, args.key_size, args.test_time, args.cert_dir, args.simulate_latency, results_dir)
    except Exception as e:
        print(f"Error running Redis benchmark: {e}")
    stop_server(redis_process, "Redis")
    
    try:
        keydb_process = start_server(keydb_cmd, "KeyDB")
        run_benchmark("KeyDB", 6379, args.tls, args.max_threads, args.clients[0], args.workload, args.key_size, args.test_time, args.cert_dir, args.simulate_latency, results_dir)
    except Exception as e:
        print(f"Error running KeyDB benchmark: {e}")
    stop_server(keydb_process, "KeyDB")
    
    print("Generating plots...")
    plot_results(results_dir)
    print(f"All benchmarks complete! Results saved in {results_dir}.")
