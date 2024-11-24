#!/bin/bash

# Create results directory with timestamp
RESULTS_DIR="benchmark_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p $RESULTS_DIR

# Text colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check if service is responding
check_service() {
    local port=$1
    local name=$2
    redis-cli -p $port ping > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: $name on port $port is not responding${NC}"
        exit 1
    fi
}

# Function to run a single benchmark scenario
run_benchmark_scenario() {
    local name=$1
    local port=$2
    local scenario=$3
    local ratio=$4
    local rate_limit=$5
    local output_prefix="$RESULTS_DIR/${name}_${scenario}"

    echo -e "${BLUE}Running $scenario benchmark for $name...${NC}"
    
    local cmd="memtier_benchmark \
        --port $port \
        --protocol=redis \
        --threads=4 \
        --clients=50 \
        --test-time=30 \
        --data-size=32 \
        --key-pattern=P:P \
        --key-minimum=1 \
        --key-maximum=100000 \
        --print-percentiles=50,90,95,99,99.9 \
        --json-out-file=${output_prefix}.json \
        --hdr-file-prefix=${output_prefix} \
        --ratio=$ratio"

    # Add rate limit if specified
    if [ ! -z "$rate_limit" ]; then
        cmd="$cmd --rate-limiting=$rate_limit"
    fi

    echo -e "${GREEN}Running command: $cmd${NC}"
    eval $cmd
    
    # Sleep between tests
    sleep 5
}

# Function to run all benchmark scenarios for a service
run_service_benchmarks() {
    local name=$1
    local port=$2
    
    echo -e "${BLUE}Starting benchmarks for $name on port $port${NC}"
    
    # Check if service is running
    check_service $port $name
    
    # 1. Balanced Read/Write test
    run_benchmark_scenario $name $port "balanced" "1:1" ""
    
    # 2. Write-heavy test
    run_benchmark_scenario $name $port "write_heavy" "3:1" ""
    
    # 3. Read-heavy test
    run_benchmark_scenario $name $port "read_heavy" "1:3" ""
    
    # 4. Rate-limited test (10K ops/sec)
    run_benchmark_scenario $name $port "rate_limited" "1:1" "10000"
}

echo -e "${BLUE}Starting benchmark suite...${NC}"

# Run Redis benchmarks
echo -e "${GREEN}Testing Redis...${NC}"
run_service_benchmarks "redis" "6379"

# Run KeyDB benchmarks
echo -e "${GREEN}Testing KeyDB...${NC}"
run_service_benchmarks "keydb" "6380"

# Generate summary report
echo -e "${BLUE}Generating summary report...${NC}"
echo "Benchmark Results Summary" > "$RESULTS_DIR/summary.txt"
echo "======================" >> "$RESULTS_DIR/summary.txt"
echo "Timestamp: $(date)" >> "$RESULTS_DIR/summary.txt"
echo "" >> "$RESULTS_DIR/summary.txt"

# Parse JSON results and add to summary
for json_file in $RESULTS_DIR/*.json; do
    echo "Results from $(basename $json_file):" >> "$RESULTS_DIR/summary.txt"
    # Extract key metrics using grep (you might want to use jq if available)
    cat $json_file | grep -E "Totals|Ops/sec|Latency" >> "$RESULTS_DIR/summary.txt"
    echo "" >> "$RESULTS_DIR/summary.txt"
done

echo -e "${BLUE}Benchmarks complete! Results are in the $RESULTS_DIR directory${NC}"
echo -e "${BLUE}Check $RESULTS_DIR/summary.txt for a quick overview${NC}"