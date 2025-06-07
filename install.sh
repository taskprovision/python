#!/bin/bash

# TaskProvision - AI-Powered Development Automation Platform
# One-line installer: curl -fsSL https://get.taskprovision.com | bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TASKPROVISION_VERSION="latest"
INSTALL_DIR="$HOME/taskprovision"
GITHUB_ORG="taskprovision"
GITHUB_REPO="taskprovision"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."

    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This installer currently supports Linux only"
        exit 1
    fi

    # Check memory (require at least 6GB)
    total_mem=$(free -g | awk 'NR==2{print $2}')
    if [ $total_mem -lt 6 ]; then
        print_warning "System has ${total_mem}GB RAM. Recommended: 8GB+"
    fi

    # Check required commands
    local required_commands=("curl" "git" "python3" "pip3")
    for cmd in "${required_commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            print_error "Required command '$cmd' is not installed"
            exit 1
        fi
    done

    print_success "System requirements check passed"
}

# Install Docker if not present
install_docker() {
    if ! command -v docker &> /dev/null; then
        print_status "Installing Docker..."
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker $USER
        print_success "Docker installed successfully"
    else
        print_status "Docker already installed"
    fi
}

# Install Kubernetes (k3s for lightweight deployment)
install_kubernetes() {
    if ! command -v kubectl &> /dev/null; then
        print_status "Installing Kubernetes (k3s)..."
        curl -sfL https://get.k3s.io | sh -s - --write-kubeconfig-mode 644
        export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
        sudo chmod 644 /etc/rancher/k3s/k3s.yaml

        # Add kubectl alias
        echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
        echo 'alias k=kubectl' >> ~/.bashrc

        print_success "Kubernetes (k3s) installed successfully"
    else
        print_status "Kubernetes already installed"
    fi
}

# Install Ollama for local AI
install_ollama() {
    if ! command -v ollama &> /dev/null; then
        print_status "Installing Ollama (Local AI)..."
        curl -fsSL https://ollama.ai/install.sh | sh

        # Start Ollama service
        sudo systemctl enable ollama
        sudo systemctl start ollama

        # Wait for service to start
        sleep 5

        # Pull a lightweight model for development
        print_status "Downloading AI model (this may take a few minutes)..."
        ollama pull qwen2.5:1.5b

        print_success "Ollama installed with qwen2.5:1.5b model"
    else
        print_status "Ollama already installed"
    fi
}

# Clone TaskProvision repository
clone_repository() {
    print_status "Cloning TaskProvision repository..."

    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory $INSTALL_DIR already exists. Updating..."
        cd "$INSTALL_DIR"
        git pull origin main
    else
        git clone https://github.com/${GITHUB_ORG}/${GITHUB_REPO}.git "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi

    print_success "Repository cloned successfully"
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."

    cd "$INSTALL_DIR"

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    pip install -r requirements.txt

    # Install TaskProvision package in development mode
    pip install -e .

    print_success "Python environment setup complete"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    print_status "Deploying TaskProvision to Kubernetes..."

    cd "$INSTALL_DIR"

    # Apply Kubernetes manifests
    kubectl apply -f kubernetes/

    # Wait for deployment
    print_status "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available deployment/taskprovision --timeout=300s

    # Get service URL
    local service_ip=$(kubectl get svc taskprovision-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$service_ip" ]; then
        service_ip=$(kubectl get svc taskprovision-service -o jsonpath='{.spec.clusterIP}')
    fi

    print_success "TaskProvision deployed successfully"
    print_success "Access your platform at: http://${service_ip}"
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."

    # Deploy Prometheus and Grafana
    kubectl apply -f monitoring/

    print_success "Monitoring setup complete"
}

# Create initial admin user
create_admin_user() {
    print_status "Creating initial admin user..."

    # Wait for API to be ready
    sleep 10

    # Create admin user via API
    local service_ip=$(kubectl get svc taskprovision-service -o jsonpath='{.spec.clusterIP}')

    curl -X POST "http://${service_ip}/api/auth/create-admin" \
        -H "Content-Type: application/json" \
        -d '{
            "email": "admin@taskprovision.local",
            "password": "admin123",
            "full_name": "TaskProvision Admin"
        }' || print_warning "Could not create admin user automatically"

    print_success "Admin user creation attempted"
}

# Setup sales automation
setup_sales_automation() {
    print_status "Setting up sales automation tools..."

    cd "$INSTALL_DIR"

    # Setup GitHub lead mining
    python3 campaigns/github_lead_mining.py --setup

    # Setup email sequences
    python3 campaigns/email_sequences.py --setup

    print_success "Sales automation tools configured"
}

# Show final instructions
show_final_instructions() {
    local service_ip=$(kubectl get svc taskprovision-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "localhost")

    echo ""
    echo "🎉 TaskProvision Installation Complete!"
    echo "========================================"
    echo ""
    echo "📊 Platform Access:"
    echo "   • Web Interface: http://${service_ip}"
    echo "   • API Docs: http://${service_ip}/docs"
    echo "   • Grafana: http://${service_ip}:3000"
    echo ""
    echo "🔐 Default Credentials:"
    echo "   • Email: admin@taskprovision.local"
    echo "   • Password: admin123"
    echo ""
    echo "🚀 Quick Start Commands:"
    echo "   • cd $INSTALL_DIR"
    echo "   • source venv/bin/activate"
    echo "   • python3 -m taskprovision.main"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Change admin password"
    echo "   2. Configure GitHub integration"
    echo "   3. Setup Stripe billing"
    echo "   4. Launch first sales campaign"
    echo ""
    echo "💡 Documentation: https://github.com/taskprovision/www"
    echo "🐛 Support: https://github.com/taskprovision/taskprovision/issues"
    echo ""
    print_success "Ready to start automating development workflows!"
}

# Main installation flow
main() {
    echo "🚀 TaskProvision Installer"
    echo "========================="
    echo "AI-Powered Development Automation Platform"
    echo ""

    check_requirements
    install_docker
    install_kubernetes
    install_ollama
    clone_repository
    setup_python_env
    deploy_kubernetes
    setup_monitoring
    create_admin_user
    setup_sales_automation
    show_final_instructions
}

# Handle interrupts
trap 'print_error "Installation interrupted by user"; exit 1' INT

# Run main installation
main "$@"