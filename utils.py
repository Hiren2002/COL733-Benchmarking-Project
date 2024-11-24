import os
import subprocess
import time
import psutil

# Text colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
RED = '\033[0;31m'
NC = '\033[0m'


def start_server(cmd, name):
    """Start a server process."""
    print(f"{GREEN}Starting {name}...{NC}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)  # Allow time for the server to initialize
    return process


def stop_server(process, name, port):
    """Stop a server process and free its port."""
    try:
        print(f"{BLUE}Stopping {name}...{NC}")
        process.terminate()
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print(f"{BLUE}Force killing {name}...{NC}")
        process.kill()

    if is_port_in_use(port):
        print(f"{BLUE}Port {port} is still in use, attempting cleanup...{NC}")
        force_kill_port(port)
        if is_port_in_use(port):
            raise RuntimeError(f"Failed to free port {port} for {name}.")
    print(f"{GREEN}{name} stopped successfully and port {port} is free.{NC}")


def is_port_in_use(port):
    """Check if a port is in use."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False


def force_kill_port(port):
    """Forcefully kill processes using a specific port."""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            pid = conn.pid
            if pid:
                print(f"{BLUE}Killing process {pid} using port {port}...{NC}")
                try:
                    psutil.Process(pid).terminate()
                except psutil.NoSuchProcess:
                    print(f"{GREEN}Process {pid} no longer exists.{NC}")


def run_benchmark(name, port, tls, threads, clients, ratio, key_size, test_time, cert_dir, output_prefix, simulate_latency=0):
    """Run a memtier benchmark."""
    cmd = [
        "memtier_benchmark",
        "--port", str(port),
        "--threads", str(threads),
        "--clients", str(clients),
        "--test-time", str(test_time),
        "--data-size", str(key_size),
        "--ratio", ratio,
        "--hide-histogram",
        "--json-out-file", f"{output_prefix}.json"
    ]
    if tls:
        cmd.extend([
            "--tls",
            "--cert", os.path.join(cert_dir, "keydb.crt"),
            "--key", os.path.join(cert_dir, "keydb.key"),
            "--cacert", os.path.join(cert_dir, "ca.crt")
        ])
    if simulate_latency > 0:
        cmd.extend(["--latency", str(simulate_latency)])
    print(f"{BLUE}Running benchmark for {name}...{NC}")
    subprocess.run(cmd)
