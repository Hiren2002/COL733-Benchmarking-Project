import os
import glob
import json
import matplotlib.pyplot as plt

# Plot benchmark results
def plot_results(results_dir):
    throughput = {}
    avg_latency = {}
    max_latency = {}

    # Read each JSON file in the results directory
    for json_file in glob.glob(os.path.join(results_dir, "*.json")):
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
    throughput_plot = os.path.join(results_dir, "throughput_comparison.png")
    plt.savefig(throughput_plot)
    print(f"Throughput plot saved: {throughput_plot}")
    
    # Plot latency comparison
    plt.figure(figsize=(12, 6))
    plt.bar(avg_latency.keys(), avg_latency.values(), label="Avg Latency", color=["blue", "orange"], alpha=0.8)
    plt.title("Latency Comparison")
    plt.ylabel("Latency (ms)")
    plt.xlabel("Server")
    plt.legend()
    plt.grid(axis='y', linestyle="--", alpha=0.7)
    latency_plot = os.path.join(results_dir, "latency_comparison.png")
    plt.savefig(latency_plot)
    print(f"Latency plot saved: {latency_plot}")
