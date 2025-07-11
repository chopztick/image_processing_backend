#!/bin/bash

# Port conflict checker and resolver for Image Processing Service

echo "🔍 Checking for port conflicts..."

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    if netstat -tuln | grep -q ":$port "; then
        echo "❌ Port $port is already in use (needed for $service)"
        echo "   Process using port $port:"
        netstat -tulpn | grep ":$port " | head -1
        return 1
    else
        echo "✅ Port $port is available (for $service)"
        return 0
    fi
}

# Check required ports
postgres_port_ok=true
api_port_ok=true

if ! check_port 5433 "PostgreSQL"; then
    postgres_port_ok=false
fi

if ! check_port 8000 "FastAPI"; then
    api_port_ok=false
fi

echo ""

# Provide solutions if conflicts exist
if [ "$postgres_port_ok" = false ] || [ "$api_port_ok" = false ]; then
    echo "🚨 Port conflicts detected! Here are your options:"
    echo ""
    
    if [ "$postgres_port_ok" = false ]; then
        echo "📋 PostgreSQL port conflict solutions:"
        echo "   1. Stop system PostgreSQL: sudo systemctl stop postgresql"
        echo "   2. Use port 5434: Edit docker-compose.yml and change '5433:5432' to '5434:5432'"
        echo "   3. Find alternative port: netstat -tuln | grep ':543' to see what's available"
        echo ""
    fi
    
    if [ "$api_port_ok" = false ]; then
        echo "📋 FastAPI port conflict solutions:"
        echo "   1. Use port 8001: Edit docker-compose.yml and change '8000:8000' to '8001:8000'"
        echo "   2. Stop service using port 8000: sudo lsof -ti:8000 | xargs sudo kill"
        echo "   3. Find alternative port: netstat -tuln | grep ':80' to see what's available"
        echo ""
    fi
    
    echo "🔧 Quick fix: Edit docker-compose.yml directly with alternative ports"
    echo "   # Edit docker-compose.yml and change port mappings to available ports"
    
    exit 1
else
    echo "🎉 All ports are available! You can run: docker-compose up -d"
    exit 0
fi