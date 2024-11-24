import os
import subprocess
import datetime
import glob
import json
import time
import matplotlib.pyplot as plt

# Create results directory with timestamp
RESULTS_DIR = "benchmark_results_{}".format(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
os.makedirs(RESULTS_DIR, exist_ok=True)

# Text colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
NC = '\033[0m'

# Function to check if service is responding
def check_service(port, name):
    try:
        # subprocess.run(['redis-cli', '--tls', '-p', str(port), 'ping'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        subprocess.run(
            [
                'redis-cli', '--tls',
                '--cert', './KeyDB/tests/tls/client.crt',
                '--key', './KeyDB/tests/tls/client.key',
                '--cacert', './KeyDB/tests/tls/ca.crt',
                '-p', str(port), 'ping'
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

    except subprocess.CalledProcessError:
        print(f"{BLUE}Error: {name} on port {port} is not responding{NC}")
        exit(1)

# Function to run a single benchmark scenario
def run_benchmark_scenario(name, port, scenario, ratio, rate_limit):
    output_prefix = os.path.join(RESULTS_DIR, f"{name}_{scenario}")
    cmd = [
        'memtier_benchmark',
        '--port', str(port),
        '--protocol', 'redis',
        '--threads', '4',
        '--clients', '50',
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
    if rate_limit:
        cmd.extend(['--rate-limiting', rate_limit])
    print(f"{BLUE}Running {scenario} benchmark for {name}...{NC}")
    print(f"{GREEN}Running command: {' '.join(cmd)}{NC}")
    subprocess.run(cmd, check=True)
    time.sleep(5)

# Function to run all benchmark scenarios for a service
def run_service_benchmarks(name, port):
    print(f"{BLUE}Starting benchmarks for {name} on port {port}{NC}")
    check_service(port, name)
    scenarios = [
        ("balanced", "1:1", ""),
        ("write_heavy", "3:1", ""),
        ("read_heavy", "1:3", ""),
        ("rate_limited", "1:1", "10000")
    ]
    for scenario in scenarios:
        run_benchmark_scenario(name, port, *scenario)

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

# Function to plot Ops/sec bar chart
def plot_ops_sec(data, services, scenarios, output_dir):
    fig, ax = plt.subplots()
    bar_width = 0.35
    index = range(len(scenarios))
    for i, service in enumerate(services):
        ops_values = [data[service][scenario]['ops_sec'] for scenario in scenarios]
        bars = ax.bar([x + i * bar_width for x in index], ops_values, bar_width, label=service)
    ax.set_xlabel('Scenarios')
    ax.set_ylabel('Ops/sec')
    ax.set_title('Benchmark Ops/sec by Service and Scenario')
    ax.set_xticks([x + (len(services)-1)*bar_width/2 for x in index])
    ax.set_xticklabels(scenarios)
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "ops_sec.png"))
    plt.close()

# Function to plot latency percentiles line chart
def plot_latency_percentiles(data, service, scenarios, output_dir):
    percentiles = list(data[service][scenarios[0]]['percentiles'].keys())
    values = [[data[service][scenario]['percentiles'][p] for scenario in scenarios] for p in percentiles]
    fig, ax = plt.subplots()
    for i, p in enumerate(percentiles):
        ax.plot(scenarios, [v[i] for v in values], marker='o', label=p)
    ax.set_xlabel('Scenarios')
    ax.set_ylabel('Latency (ms)')
    ax.set_title(f'{service} Latency Percentiles by Scenario')
    ax.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"latency_{service}.png"))
    plt.close()

# Function to collect data for plotting
def collect_plot_data():
    data = {}
    for json_file in glob.glob(os.path.join(RESULTS_DIR, "*.json")):
        file_name = os.path.basename(json_file)
        parts = file_name.split('_')
        if len(parts) < 3:
            continue
        service = parts[0]
        scenario = parts[1].replace('.json', '')
        with open(json_file, "r") as f:
            try:
                data_content = json.load(f)
                totals = data_content.get("Totals", [{}])[0]
                ops_sec = totals.get("Ops/sec", 0)
                latency = totals.get("Latency", {})
                percentiles = latency.get("Percentiles", {})
                if service not in data:
                    data[service] = {}
                data[service][scenario] = {
                    'ops_sec': ops_sec,
                    'percentiles': percentiles
                }
            except json.JSONDecodeError:
                print(f"{BLUE}Warning: Invalid JSON file {json_file}{NC}")
    return data

# Main execution
if __name__ == "__main__":
    print(f"{BLUE}Starting benchmark suite...{NC}")
    print(f"{GREEN}Testing Redis...{NC}")
    run_service_benchmarks("redis", 6379)
    print(f"{GREEN}Testing KeyDB...{NC}")
    run_service_benchmarks("keydb", 6381)
    
    # Generate summary report
    print(f"{BLUE}Generating summary report...{NC}")
    generate_summary_report()
    
    # Collect data for plotting
    plot_data = collect_plot_data()
    services = list(plot_data.keys())
    if not services:
        print(f"{BLUE}No data to plot.{NC}")
    else:
        scenarios = list(plot_data[services[0]].keys())
        # Plot Ops/sec bar chart
        plot_ops_sec(plot_data, services, scenarios, RESULTS_DIR)
        # Plot latency percentiles line charts
        for service in services:
            plot_latency_percentiles(plot_data, service, scenarios, RESULTS_DIR)
    
    print(f"{BLUE}Benchmarks complete! Results are in the {RESULTS_DIR} directory{NC}")
    print(f"{BLUE}Check {RESULTS_DIR}/summary.txt for a quick overview{NC}")