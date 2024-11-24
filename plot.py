import os
import sys
import json
import glob
from collections import defaultdict

import matplotlib.pyplot as plt

# Function to load JSON data from a file
def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON file {file_path}")
        return None

# Function to extract metrics from JSON data
def extract_metrics(data):
    if data is None:
        return 0, {}
    totals = data.get('Totals', [])
    if not totals:
        return 0, {}
    ops_sec = totals[0].get('Ops/sec', 0)
    latency = totals[0].get('Latency', {})
    percentiles = latency.get('Percentiles', {})
    return ops_sec, percentiles

# Main function
def main(results_dir):
    # Find all JSON files in the results directory
    json_files = glob.glob(f"{results_dir}/*.json")
    if not json_files:
        print("No JSON files found in the results directory.")
        return

    # Organize data by service and scenario
    data_dict = defaultdict(lambda: defaultdict(dict))
    for file_path in json_files:
        file_name = os.path.basename(file_path)
        parts = file_name.split('_')
        if len(parts) < 3:
            continue
        service = parts[0]
        scenario = parts[1].replace('.json', '')
        data = load_json(file_path)
        if data is None:
            continue
        ops_sec, percentiles = extract_metrics(data)
        if ops_sec == 0 and not percentiles:
            print(f"Warning: No data extracted from {file_path}")
            continue
        data_dict[service][scenario]['ops_sec'] = ops_sec
        data_dict[service][scenario]['percentiles'] = percentiles

    if not data_dict:
        print("No data to plot.")
        return

    # Plot Ops/sec bar chart
    try:
        services = list(data_dict.keys())
        scenarios = list(data_dict[services[0]].keys())
        ops_data = {service: [data_dict[service][scenario]['ops_sec'] for scenario in scenarios] for service in services}

        fig, ax = plt.subplots()
        bar_width = 0.35
        index = range(len(scenarios))
        for i, service in enumerate(services):
            bars = ax.bar([x + i * bar_width for x in index], ops_data[service], bar_width, label=service)
        ax.set_xlabel('Scenarios')
        ax.set_ylabel('Ops/sec')
        ax.set_title('Benchmark Ops/sec by Service and Scenario')
        ax.set_xticks([x + (len(services)-1)*bar_width/2 for x in index])
        ax.set_xticklabels(scenarios)
        ax.legend()
        plt.tight_layout()
        plt.savefig(f"{results_dir}/ops_sec.png")
    except Exception as e:
        print(f"Error plotting Ops/sec: {e}")

    # Plot Latency Percentiles line chart
    try:
        for service in services:
            percentiles_data = [data_dict[service][scenario]['percentiles'] for scenario in scenarios]
            if not percentiles_data[0]:
                continue
            percentiles = list(percentiles_data[0].keys())
            values = [[perc.get(p, 0) for perc in percentiles_data] for p in percentiles]
            fig, ax = plt.subplots()
            for i, p in enumerate(percentiles):
                ax.plot(scenarios, [v[i] for v in values], marker='o', label=p)
            ax.set_xlabel('Scenarios')
            ax.set_ylabel('Latency (ms)')
            ax.set_title(f'{service} Latency Percentiles by Scenario')
            ax.legend()
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f"{results_dir}/latency_{service}.png")
    except Exception as e:
        print(f"Error plotting latency: {e}")

    print(f"Plots saved in the {results_dir} directory.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python plot_benchmarks.py <results_directory>")
        sys.exit(1)
    results_dir = sys.argv[1]
    main(results_dir)