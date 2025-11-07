# Platform Infrastructure - Production Environment

# TODO: Configure production environment
# Copy from dev/ and adjust:
# - project_id = "platform-prod-..."
# - environment = "prod"
# - Use standard (not preemptible) nodes
# - Higher node counts
# - Multi-zone deployment
# - Backup/DR configuration

# For now, production is not yet configured
# When ready, copy dev/*.tf files here and modify variables

# IMPORTANT: Production should have:
# - Remote state in GCS
# - State locking
# - Separate service accounts
# - Stricter IAM policies
# - Monitoring/alerting
# - Backup strategy
