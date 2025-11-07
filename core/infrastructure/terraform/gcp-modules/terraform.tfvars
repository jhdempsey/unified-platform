project_id   = "gen-lang-client-0282248851"
project_name = "ai-platform"
region       = "us-central1"
environment  = "demo"

use_autopilot           = true
use_preemptible         = true
redis_tier              = "BASIC"
redis_memory_gb         = 1
min_nodes               = 1
max_nodes               = 3
max_cloud_run_instances = 10

allow_unauthenticated = true

ai_gateway_image = "gcr.io/gen-lang-client-0282248851/ai-gateway:latest"
