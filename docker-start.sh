#!/bin/bash
# Production Docker startup script for Threat Modeling Pipeline

set -e  # Exit on any error

echo "🐳 Starting Threat Modeling Pipeline in Docker..."
echo ""

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f "./apps/api/.env" ]; then
    echo "⚠️  No .env file found in apps/api/"
    echo "   Creating from template..."
    cp .env.docker ./apps/api/.env
    echo "✅ Please edit apps/api/.env with your API keys before starting"
    echo ""
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p inputs outputs/exports outputs/reports outputs/temp
echo "✅ Directories created"
echo ""

# Function to start services
start_services() {
    local profile=${1:-""}
    local compose_args=""
    
    if [ -n "$profile" ]; then
        compose_args="--profile $profile"
    fi
    
    echo "🚀 Building and starting all services..."
    echo "   This may take a few minutes on first run..."
    
    # Build and start services
    docker-compose $compose_args up -d --build
    
    echo ""
    echo "⏳ Waiting for services to be ready..."
    
    # Wait for database to be ready
    echo "   Waiting for PostgreSQL..."
    until docker-compose exec -T postgres pg_isready -U threat_user -d threat_modeling; do
        sleep 2
    done
    echo "   ✅ PostgreSQL is ready"
    
    # Wait for Redis to be ready
    echo "   Waiting for Redis..."
    until docker-compose exec -T redis redis-cli ping; do
        sleep 2
    done
    echo "   ✅ Redis is ready"
    
    # Wait for API to be ready
    echo "   Waiting for API server..."
    until curl -f http://localhost:8000/health >/dev/null 2>&1; do
        sleep 5
    done
    echo "   ✅ API server is ready"
    
    # Wait for frontend to be ready
    echo "   Waiting for frontend..."
    until curl -f http://localhost:3001 >/dev/null 2>&1; do
        sleep 3
    done
    echo "   ✅ Frontend is ready"
    
    echo ""
    echo "🎉 All services are running successfully!"
}

# Function to show service URLs
show_urls() {
    echo ""
    echo "🌐 Service URLs:"
    echo "   📱 Frontend:          http://localhost:3001"
    echo "   🔧 API Documentation: http://localhost:8000/docs"
    echo "   ❤️  Health Check:     http://localhost:8000/health"
    echo "   🌺 Celery Monitor:    http://localhost:5555"
    if docker-compose ps | grep -q ollama; then
        echo "   🤖 Ollama:            http://localhost:11434"
    fi
    echo ""
}

# Function to show logs
show_logs() {
    echo "📋 Recent logs from all services:"
    docker-compose logs --tail=10
}

# Function to show status
show_status() {
    echo "📊 Service Status:"
    docker-compose ps
}

# Parse command line arguments
case "${1:-start}" in
    "start")
        start_services
        show_urls
        show_status
        ;;
    "start-with-ollama")
        start_services "ollama"
        show_urls
        show_status
        ;;
    "stop")
        echo "🛑 Stopping all services..."
        docker-compose down
        echo "✅ All services stopped"
        ;;
    "restart")
        echo "🔄 Restarting all services..."
        docker-compose restart
        show_urls
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "clean")
        echo "🧹 Stopping and removing all containers, volumes, and images..."
        read -p "Are you sure? This will delete all data (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --rmi all
            echo "✅ Cleanup completed"
        else
            echo "❌ Cleanup cancelled"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Threat Modeling Pipeline Docker Management"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start              Start all services (default)"
        echo "  start-with-ollama  Start all services including local Ollama LLM"
        echo "  stop               Stop all services"
        echo "  restart            Restart all services"
        echo "  logs               Show recent logs from all services"
        echo "  status             Show service status"
        echo "  clean              Remove all containers, volumes, and images"
        echo "  help               Show this help message"
        echo ""
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac