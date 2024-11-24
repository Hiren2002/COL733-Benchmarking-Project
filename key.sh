cat > ~/keydb-benchmark/keydb.conf << EOF
# Network
port 6380
protected-mode no
bind 127.0.0.1

# Performance
server-threads 4
server-thread-affinity true

# Memory
maxmemory 1gb
maxmemory-policy allkeys-lru

# Disable all persistence
save ""
appendonly no
dbfilename ""

# Logging
logfile ""
loglevel notice
EOF
