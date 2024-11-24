# Redis vs KeyDB Benchmark Suite

This project benchmarks the performance of Redis and KeyDB using the `memtier_benchmark` tool. The benchmarks can be run in both TLS and non-TLS modes and support various experimental configurations to analyze server behavior under different conditions.

---

## Table of Contents
1. [Installation Instructions](#installation-instructions)
   - [Install Redis](#install-redis)
   - [Install KeyDB](#install-keydb)
   - [Install Memtier Benchmark](#install-memtier-benchmark)
   - [Generate Certificates for TLS Mode](#generate-certificates-for-tls-mode)
2. [Running the Benchmarks](#running-the-benchmarks)
   - [Command Line Arguments](#command-line-arguments)
   - [Example Commands](#example-commands)
3. [Automated Setup](#automated-setup)
4. [Contributing](#contributing)
5. [License](#license)

---

## Installation Instructions

### Install Redis
```bash
sudo apt-get update
sudo apt-get install redis -y
```

### Install KeyDB
```bash
sudo apt update
sudo apt install build-essential tcl cmake git -y

git clone https://github.com/Snapchat/KeyDB.git
cd KeyDB

make -j$(nproc)
sudo make install
```

### Install Memtier Benchmark
```bash
git clone https://github.com/RedisLabs/memtier_benchmark.git
cd memtier_benchmark
sudo apt-get install build-essential autoconf automake libssl-dev -y
autoreconf -ivf
./configure
make
sudo make install
```

### Generate Certificates for TLS Mode
To enable TLS mode, certificates need to be generated. Use the following commands to create self-signed certificates:
```bash
cd KeyDB
./KeyDB/utils/gen-test-certs.sh
```

This places the certificates in the `KeyDB/tests/tls` folder in the root of the project.

---

## Running the Benchmarks

The main script `main.py` benchmarks Redis and KeyDB using `memtier_benchmark`. It supports both TLS and non-TLS modes and can be configured for various experimental conditions.

### Command Line Arguments
- `--tls`: Enables TLS mode for the benchmark.
- `--cert-dir <path>`: Path to the directory containing TLS certificates (default: `./certs`).
- `--max-threads <int>`: Number of threads for the servers and memtier (default: 4).
- `--clients <int>`: Number of clients for the benchmark (default: 50).
- `--test-time <int>`: Duration of the test in seconds (default: 30).
- `--workload <type>`: Specifies the workload:
  - `balanced` (default): Equal ratio of GET and SET operations.
  - `write-heavy`: More SET operations.
  - `read-heavy`: More GET operations.

### Example Commands
1. **Non-TLS Mode**:
   ```bash
   python3 main.py --max-threads 4 --clients 50
   ```

2. **TLS Mode**:
   ```bash
   python3 main.py --tls --cert-dir ./certs --max-threads 4 --clients 50
   ```

3. **Custom Workload**:
   ```bash
   python3 main.py --workload write-heavy --test-time 60
   ```

4. **Stress Testing**:
   ```bash
   python3 main.py --clients 500 --test-time 120
   ```

---

## Contributing

We welcome contributions to improve the benchmarking suite. Feel free to open issues or submit pull requests.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
```

---