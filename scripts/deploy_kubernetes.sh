#!/bin/bash

# TaskProvision Kubernetes Deployment Script
# Handles production deployments with zero-downtime

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
IMAGE_TAG=${IMAGE_TAG:-"latest"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Deployment options
SKIP_TESTS=${SKIP_TESTS:-false}
SKIP_MIGRATIONS=${SKIP_MIGRATIONS:-false}
ROLLBACK_ON_FAILURE=${ROLLBACK_ON_FAILURE:-true}

print_status "Starting TaskProvision deployment..."
print_status "Image tag: $IMAGE_TAG"
print_status "Environment: $ENVIRONMENT"
print_status "Namespace: $NAMESPACE"

# Pre-deployment checks
pre_deployment_checks() {
    print_status "Running pre-deployment checks..."

    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check namespace exists
    if ! kubectl get namespace $NAMESPACE &> /dev/null; then
        print_error "Namespace '$NAMESPACE' does not exist"
        exit 1
    fi

    # Check image exists
    if ! docker manifest inspect taskprovision/taskprovision:$IMAGE_TAG &> /dev/null; then
        print_warning "Image taskprovision/taskprovision:$IMAGE_TAG may not exist"
    fi

    print_success "Pre-deployment checks passed"
}

# Run tests
run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        print_warning "Skipping tests (SKIP_TESTS=true)"
        return
    fi

    print_status "Running tests..."

    # Create test job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: taskprovision-tests-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: tests
        image: taskprovision/taskprovision:$IMAGE_TAG
        command: ["python", "-m", "pytest", "tests/", "-v"]
        envFrom:
        - configMapRef:
            name: taskprovision-config
        - secretRef:
            name: taskprovision-secrets
      restartPolicy: Never
  backoffLimit: 1
EOF

    # Wait for tests to complete
    kubectl wait --for=condition=complete job -l app=taskprovision-tests --timeout=300s

    print_success "Tests completed successfully"
}

# Backup current state
backup_current_state() {
    print_status "Backing up current state..."

    # Export current deployment
    kubectl get deployment taskprovision -o yaml > /tmp/taskprovision-backup-$(date +%s).yaml

    print_success "Current state backed up"
}

# Run database migrations
run_migrations() {
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        print_warning "Skipping migrations (SKIP_MIGRATIONS=true)"
        return
    fi

    print_status "Running database migrations..."

    # Create migration job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: taskprovision-migrate-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: migrate
        image: taskprovision/taskprovision:$IMAGE_TAG
        command: ["python", "-m", "alembic", "upgrade", "head"]
        envFrom:
        - configMapRef:
            name: taskprovision-config
        - secretRef:
            name: taskprovision-secrets
      restartPolicy: Never
  backoffLimit: 2
EOF

    # Wait for migration to complete
    kubectl wait --for=condition=complete job -l app=taskprovision-migrate --timeout=300s

    print_success "Database migrations completed"
}

# Update deployment
update_deployment() {
    print_status "Updating deployment to image tag: $IMAGE_TAG..."

    # Update deployment image
    kubectl set image deployment/taskprovision taskprovision=taskprovision/taskprovision:$IMAGE_TAG -n $NAMESPACE

    # Wait for rollout to complete
    kubectl rollout status deployment/taskprovision -n $NAMESPACE --timeout=300s

    print_success "Deployment updated successfully"
}

# Health checks
run_health_checks() {
    print_status "Running post-deployment health checks..."

    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app=taskprovision,component=api --timeout=120s

    # Check API health
    local service_ip=$(kubectl get svc taskprovision-service -o jsonpath='{.spec.clusterIP}')
    local retries=0

    while [ $retries -lt 10 ]; do
        if curl -f http://$service_ip/health &> /dev/null; then
            print_success "API health check passed"
            break
        fi
        print_status "Waiting for API to be healthy... ($((10-retries)) attempts left)"
        sleep 10
        retries=$((retries + 1))
    done

    if [ $retries -eq 10 ]; then
        print_error "API health check failed"
        return 1
    fi

    # Check database connectivity
    local app_pod=$(kubectl get pods -l component=api -o jsonpath='{.items[0].metadata.name}')
    if kubectl exec $app_pod -- python -c "from taskprovision.config.database import test_connection; test_connection()" &> /dev/null; then
        print_success "Database connectivity check passed"
    else
        print_error "Database connectivity check failed"
        return 1
    fi

    print_success "All health checks passed"
}

# Cleanup old resources
cleanup_old_resources() {
    print_status "Cleaning up old resources..."

    # Remove completed jobs older than 24 hours
    kubectl get jobs -o go-template --template '{{range .items}}{{.metadata.name}} {{.metadata.creationTimestamp}}{{"\n"}}{{end}}' | awk '$2 <= "'$(date -d '24 hours ago' -Ins --utc | sed 's/+0000/Z/')'" { print $1 }' |
    xargs -r kubectl delete job

    # Remove old replica sets
    kubectl get rs -o go-template --template '{{range .items}}{{if eq .spec.replicas 0}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' |
    xargs -r kubectl delete rs

    print_success "Old resources cleaned up"
}

# Rollback on failure
rollback_deployment() {
    if [ "$ROLLBACK_ON_FAILURE" = "true" ]; then
        print_error "Deployment failed, rolling back..."
        kubectl rollout undo deployment/taskprovision -n $NAMESPACE
        kubectl rollout status deployment/taskprovision -n $NAMESPACE --timeout=300s
        print_success "Rollback completed"
    else
        print_error "Deployment failed (rollback disabled)"
    fi
}

# Send deployment notification
send_notification() {
    local status=$1
    local webhook_url=${SLACK_WEBHOOK_URL:-""}

    if [ -n "$webhook_url" ]; then
        local color="good"
        local emoji="✅"

        if [ "$status" = "failed" ]; then
            color="danger"
            emoji="❌"
        fi

        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"$emoji TaskProvision Deployment $status\",
                    \"fields\": [
                        {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                        {\"title\": \"Image Tag\", \"value\": \"$IMAGE_TAG\", \"short\": true},
                        {\"title\": \"Namespace\", \"value\": \"$NAMESPACE\", \"short\": true}
                    ]
                }]
            }" \
            $webhook_url
    fi
}

# Main deployment flow
main() {
    local deployment_start=$(date)

    pre_deployment_checks
    run_tests
    backup_current_state
    run_migrations

    # Attempt deployment
    if update_deployment && run_health_checks; then
        cleanup_old_resources

        local deployment_end=$(date)
        echo ""
        echo "🎉 Deployment Successful!"
        echo "========================="
        echo "Started: $deployment_start"
        echo "Completed: $deployment_end"
        echo "Image: taskprovision/taskprovision:$IMAGE_TAG"
        echo "Environment: $ENVIRONMENT"
        echo ""

        # Show current status
        kubectl get pods -l app=taskprovision

        send_notification "successful"
        return 0
    else
        rollback_deployment
        send_notification "failed"
        return 1
    fi
}

# Handle interrupts
trap 'print_error "Deployment interrupted by user"; rollback_deployment; exit 1' INT

# Execute deployment
if main "$@"; then
    exit 0
else
    exit 1
fi
