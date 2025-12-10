import sys
from pathlib import Path

# Read the file
with open('ml_consumer_production.py', 'r') as f:
    content = f.read()

# Fix imports
content = content.replace(
    'from ml.models.demand_forecasting.model import DemandForecastingModel',
    'from demand_forecasting.model import DemandForecastingModel'
)
content = content.replace(
    'from ml.models.inventory_optimization.model import InventoryOptimizationModel',
    'from inventory_optimization.model import InventoryOptimizationModel'
)
content = content.replace(
    'from ml.models.supplier_reliability.model import SupplierReliabilityModel',
    'from supplier_reliability.model import SupplierReliabilityModel'
)

# Add vertical-models to path at the top
import_section = '''import sys
from pathlib import Path

# Add vertical models to path
sys.path.insert(0, "/app/vertical-models")
'''

# Insert after initial imports
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'sys.path.insert' in line and 'parent.parent' in line:
        lines[i] = import_section
        break

content = '\n'.join(lines)

with open('ml_consumer_production.py', 'w') as f:
    f.write(content)

print("✅ Fixed imports")
