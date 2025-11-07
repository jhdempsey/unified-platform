#!/bin/bash
# Backup critical data before teardown

ENVIRONMENT=${1:-dev}
BACKUP_DIR="backups/$(date +%Y%m%d-%H%M%S)-${ENVIRONMENT}"

mkdir -p "$BACKUP_DIR"

echo "💾 Backing up critical data"
echo "   Environment: $ENVIRONMENT"
echo "   Backup directory: $BACKUP_DIR"

# Terraform state
if [ -d "core/infrastructure/terraform/environments/$ENVIRONMENT" ]; then
    echo "  → Terraform state"
    cp core/infrastructure/terraform/environments/$ENVIRONMENT/terraform.tfstate* \
        "$BACKUP_DIR/" 2>/dev/null || true
fi

# PostgreSQL (if accessible)
echo "  → PostgreSQL database"
kubectl exec -n platform-$ENVIRONMENT deployment/postgres -- \
    pg_dump -U platform platform > "$BACKUP_DIR/postgres.sql" 2>/dev/null || \
    echo "    ⚠️  Could not backup PostgreSQL"

# Configuration
echo "  → Configuration files"
cp deployments/$ENVIRONMENT/*.yaml "$BACKUP_DIR/" 2>/dev/null || true
cp deployments/$ENVIRONMENT/*.tfvars "$BACKUP_DIR/" 2>/dev/null || true

echo ""
echo "✅ Backup complete: $BACKUP_DIR"
