# Optimized TLS Performance in KeyDB vs. Redis Benchmarking Study

## Abstract

This project is a comprehensive benchmarking study comparing the performance of Redis and KeyDB under TLS encryption. We evaluate latency, throughput, and real-world impact across various workloads to assess which database offers superior performance in a secure environment.

## Installation

### Redis and KeyDB

Install Redis and KeyDB using Homebrew:

```bash
brew install redis
brew install keydb
```

### memtier_benchmark

Clone the repository and build from source:

```bash
git clone https://github.com/RedisLabs/memtier_benchmark.git
cd memtier_benchmark
autoreconf -ivf
./configure
make
sudo make install
```

### Python Dependencies

Install required Python packages:

```bash
pip install matplotlib
```

## Usage

### Running Benchmarks

Navigate to the project directory and execute:

```bash
./run_benchmarks.sh
```

This script will:

1. Create a results directory with a timestamp.
2. Start Redis and KeyDB servers.
3. Run predefined benchmark scenarios.
4. Generate a summary report.

### Generating Plots

To visualize the results, run:

```bash
python plot.py <results_directory>
```

Replace `<results_directory>` with the path to your benchmark results.

## Benchmark Scenarios

- **Balanced**: Equal read and write operations.
- **Write-Heavy**: Three times more writes than reads.
- **Read-Heavy**: Three times more reads than writes.
- **Rate-Limited**: Limited to 10,000 operations per second.

## Results Interpretation

- **Ops/sec**: Measures the throughput of the database.
- **Latency Percentiles**: Indicates the response time distribution.

Refer to the generated plots and `summary.txt` in the results directory for detailed insights.

## Team Members

- Hirenkumar Parmar (2020CS50435)
- Ashish Choudhary (2020CS50642)
- Si Siddhanth Raja (2020CS50443)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.