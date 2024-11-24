import os
import glob
import json
import matplotlib.pyplot as plt

def plot_results(results_dir):
    """Plot benchmark results."""
    throughput = {}
    avg_latency = {}
    max_latency = {}

    for json_file in glob.glob(os.path.join(results_dir, "*.json")):
        with open(json_file) as f:
            data = json.load(f)
            totals = data["ALL STATS"]["Totals"]

            name = os.path.basename(json_file).split(".")[0]
            throughput[name] = totals["Ops/sec"]
            avg_latency[name] = totals["Average Latency"]
            max_latency[name] = totals["Max Latency"]

    # Throughput plot
    plt.figure(figsize=(12, 6))
    plt.bar(throughput.keys(), throughput.values(), color=["blue", "orange"], alpha=0.8)
    plt.title("Throughput Comparison (Ops/sec)")
    plt.ylabel("Ops/sec")
    plt.grid(axis='y', linestyle="--", alpha=0.7)
    plt.savefig(os.path.join(results_dir, "throughput_comparison.png"))

    # Latency plot
    plt.figure(figsize=(12, 6))
    plt.bar(avg_latency.keys(), avg_latency.values(), label="Avg Latency", color=["blue", "orange"], alpha=0.8)
    plt.title("Latency Comparison")
    plt.ylabel("Latency (ms)")
    plt.legend()
    plt.grid(axis='y', linestyle="--", alpha=0.7)
    plt.savefig(os.path.join(results_dir, "latency_comparison.png"))
