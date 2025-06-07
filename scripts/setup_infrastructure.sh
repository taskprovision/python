#!/bin/bash

# TaskProvision Infrastructure Setup Script
# Sets up complete development and production infrastructure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
NAMESPACE="taskprovision"
ENVIRONMENT=${ENVIRONMENT:-"development"}

print_status "Setting up TaskProvision infrastructure..."
print_status "Environment: $ENVIRONMENT"
print_status "Namespace: $NAMESPACE"

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    local required_commands=("kubectl" "docker" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            print_error "Required command '$cmd' is not installed"
            exit 1
        fi
    done

    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

# Setup namespace
setup_namespace() {
    print_status "Setting up namespace..."

    kubectl apply -f kubernetes/namespace.yaml
    kubectl config set-context --current --namespace=$NAMESPACE

    print_success "Namespace '$NAMESPACE' configured"
}

# Setup storage
setup_storage() {
    print_status "Setting up storage..."

    # Create storage class for local development
    if [ "$ENVIRONMENT" = "development" ]; then
        cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
  namespace: $NAMESPACE
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Delete
EOF
    fi

    print_success "Storage configured"
}

# Deploy core services
deploy_core_services() {
    print_status "Deploying core services..."

    # Apply configurations
    kubectl apply -f kubernetes/configmap.yaml

    # Deploy services
    kubectl apply -f kubernetes/deployment.yaml
    kubectl apply -f kubernetes/service.yaml

    print_success "Core services deployed"
}

# Setup ingress
setup_ingress() {
    print_status "Setting up ingress..."

    # Install nginx ingress controller if not present
    if ! kubectl get ingressclass nginx &> /dev/null; then
        print_status "Installing nginx ingress controller..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

        # Wait for ingress controller to be ready
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=120s
    fi

    # Apply ingress configuration
    kubectl apply -f kubernetes/ingress.yaml

    print_success "Ingress configured"
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."

    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

    # Deploy monitoring stack
    kubectl apply -f monitoring/ -n monitoring

    print_success "Monitoring configured"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."

    # Wait for main deployment
    kubectl wait --for=condition=available deployment/taskprovision --timeout=300s

    # Wait for database
    kubectl wait --for=condition=ready pod -l component=database --timeout=300s

    # Wait for Ollama (may take longer to download models)
    kubectl wait --for=condition=ready pod -l component=ai --timeout=600s

    print_success "All services are ready"
}

# Initialize Ollama models
initialize_ollama() {
    print_status "Initializing Ollama models..."

    # Get Ollama pod name
    local ollama_pod=$(kubectl get pods -l component=ai -o jsonpath='{.items[0].metadata.name}')

    if [ -n "$ollama_pod" ]; then
        # Pull required model
        kubectl exec $ollama_pod -- ollama pull qwen2.5:1.5b
        print_success "Ollama model initialized"
    else
        print_warning "Ollama pod not found, skipping model initialization"
    fi
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."

    # Get app pod name
    local app_pod=$(kubectl get pods -l component=api -o jsonpath='{.items[0].metadata.name}')

    if [ -n "$app_pod" ]; then
        # Run migrations
        kubectl exec $app_pod -- python -m alembic upgrade head
        print_success "Database migrations completed"
    else
        print_warning "Application pod not found, skipping migrations"
    fi
}

# Create initial admin user
create_admin_user() {
    print_status "Creating initial admin user..."

    local service_ip=$(kubectl get svc taskprovision-service -o jsonpath='{.spec.clusterIP}')

    # Wait for API to be ready
    local retries=0
    while [ $retries -lt 30 ]; do
        if curl -f http://$service_ip/health &> /dev/null; then
            break
        fi
        print_status "Waiting for API to be ready... ($((30-retries)) attempts left)"
        sleep 10
        retries=$((retries + 1))
    done

    # Create admin user
    curl -X POST "http://$service_ip/api/auth/create-admin" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@taskprovision.local",
            "password": "admin123",
            "full_name": "TaskProvision Admin"
        }' || print_warning "Could not create admin user automatically"

    print_success "Admin user creation attempted"
}

# Setup development tools
setup_dev_tools() {
    if [ "$ENVIRONMENT" = "development" ]; then
        print_status "Setting up development tools..."

        # Port forward for local development
        cat > port-forward.sh << 'EOF'
#!/bin/bash
echo "Setting up port forwarding for development..."
kubectl port-forward svc/taskprovision-service 8000:80 &
kubectl port-forward svc/postgres-service 5432:5432 &
kubectl port-forward svc/redis-service 6379:6379 &
kubectl port-forward svc/ollama-service 11434:11434 &
echo "Port forwarding active. Press Ctrl+C to stop."
wait
EOF
        chmod +x port-forward.sh

        print_success "Development tools configured"
        print_status "Run './port-forward.sh' to access services locally"
    fi
}

# Show final status
show_status() {
    echo ""
    echo "🎉 TaskProvision Infrastructure Setup Complete!"
    echo "=============================================="
    echo ""
    echo "📊 Deployment Status:"
    kubectl get pods -o wide
    echo ""
    echo "🌐 Services:"
    kubectl get svc
    echo ""
    echo "🔗 Ingress:"
    kubectl get ingress
    echo ""

    local service_ip=$(kubectl get svc taskprovision-service -o jsonpath='{.spec.clusterIP}')
    echo "📍 Access Points:"
    echo "   • Internal API: http://$service_ip"
    echo "   • Health Check: http://$service_ip/health"
    echo "   • API Docs: http://$service_ip/docs"
    echo ""

    if [ "$ENVIRONMENT" = "development" ]; then
        echo "🔧 Development:"
        echo "   • Run './port-forward.sh' for local access"
        echo "   • API: http://localhost:8000"
        echo "   • Postgres: localhost:5432"
        echo "   • Redis: localhost:6379"
        echo "   • Ollama: http://localhost:11434"
        echo ""
    fi

    echo "🔐 Default Credentials:"
    echo "   • Email: admin@taskprovision.local"
    echo "   • Password: admin123"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Change admin password"
    echo "   2. Configure external integrations"
    echo "   3. Setup SSL certificates (production)"
    echo "   4. Configure monitoring alerts"
    echo ""
    print_success "Infrastructure is ready for use!"
}

# Main execution
main() {
    check_prerequisites
    setup_namespace
    setup_storage
    deploy_core_services
    setup_ingress
    setup_monitoring
    wait_for_services
    initialize_ollama
    run_migrations
    create_admin_user
    setup_dev_tools
    show_status
}

# Handle interrupts
trap 'print_error "Setup interrupted by user"; exit 1' INT

# Run main setup
main "$@"