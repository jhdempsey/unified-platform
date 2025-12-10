with open('main.py', 'r') as f:
    content = f.read()

# Add imports for other models
new_imports = '''try:
    from demand_forecasting.model import DemandForecastingModel
    from demand_forecasting.rf_model import SupplyChainRFModel
    from inventory_optimization.model import InventoryOptimizationModel
    from supplier_reliability.model import SupplierReliabilityModel
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Could not import models: {e}")
    MODELS_AVAILABLE = False
    DemandForecastingModel = None
    SupplyChainRFModel = None
    InventoryOptimizationModel = None
    SupplierReliabilityModel = None'''

# Find and replace imports
old_imports = '''try:
    from demand_forecasting.model import DemandForecastingModel
    from demand_forecasting.rf_model import SupplyChainRFModel
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Could not import models: {e}")
    print(f"   Falling back to stub predictions")
    MODELS_AVAILABLE = False
    DemandForecastingModel = None
    SupplyChainRFModel = None'''

content = content.replace(old_imports, new_imports)

# Add loading for inventory and supplier models in load_models()
inventory_load = '''
    # Load Inventory Optimization model
    try:
        if InventoryOptimizationModel:
            models["inventory_optimization"] = InventoryOptimizationModel()
            model_metadata["inventory_optimization"] = {
                "type": "optimization",
                "version": "1.0.0",
                "framework": "numpy",
                "description": "Inventory optimization model",
                "status": "active",
            }
            print("✅ Loaded: inventory_optimization")
    except Exception as e:
        print(f"⚠️  Failed to load inventory model: {e}")

    # Load Supplier Reliability model
    try:
        if SupplierReliabilityModel:
            models["supplier_reliability"] = SupplierReliabilityModel()
            model_metadata["supplier_reliability"] = {
                "type": "scoring",
                "version": "1.0.0",
                "framework": "numpy",
                "description": "Supplier reliability scoring model",
                "status": "active",
            }
            print("✅ Loaded: supplier_reliability")
    except Exception as e:
        print(f"⚠️  Failed to load supplier model: {e}")'''

# Insert after RF model loading
if 'print(f"✅ Loaded {len(models)} models")' in content:
    content = content.replace(
        'print(f"✅ Loaded {len(models)} models")',
        inventory_load + '\n\n    print(f"✅ Loaded {len(models)} models")'
    )

with open('main.py', 'w') as f:
    f.write(content)

print("✅ Updated model loading")
