# Variables
MAX_THREADS = 4
CLIENTS = 50
TEST_TIME = 30
WORKLOAD = balanced
CERT_DIR = ./certs
PYTHON = python3

# Targets
.PHONY: all redis keydb memtier certs benchmarks clean

# Install all dependencies
all: redis keydb memtier certs

# Install Redis
redis:
	sudo apt-get update
	sudo apt-get install redis -y

# Install KeyDB
keydb:
	sudo apt update
	sudo apt install build-essential tcl cmake git -y
	git clone https://github.com/Snapchat/KeyDB.git || true
	cd KeyDB && make -j$$(nproc) && sudo make install

# Install Memtier Benchmark
memtier:
	git clone https://github.com/RedisLabs/memtier_benchmark.git || true
	cd memtier_benchmark && sudo apt-get install build-essential autoconf automake libssl-dev -y
	cd memtier_benchmark && autoreconf -ivf && ./configure && make && sudo make install

# Generate Certificates for TLS Mode
certs:
	cd KeyDB && ./utils/gen-test-certs.sh || true
	@echo "Certificates generated and stored in KeyDB/tests/tls."

# Run Benchmarks
benchmarks:
	$(PYTHON) main.py --max-threads $(MAX_THREADS) --clients $(CLIENTS) --test-time $(TEST_TIME) --workload $(WORKLOAD)

# Run TLS Benchmarks
tls-benchmarks:
	$(PYTHON) main.py --tls --cert-dir $(CERT_DIR) --max-threads $(MAX_THREADS) --clients $(CLIENTS)

# Clean up repositories and temporary files
clean:
	rm -rf KeyDB memtier_benchmark $(CERT_DIR)
	@echo "Cleaned up all generated files and repositories."
