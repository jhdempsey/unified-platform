# Creating Vertical Templates

This guide explains how to create a new vertical template for the unified platform.

## Template Structure

```
templates/your-vertical/
├── config.yaml              # Vertical configuration
├── models/                  # ML models
├── schemas/                 # Avro schemas
├── flink-jobs/             # Stream processing jobs
├── agents/                  # Vertical-specific agents
├── sample-data/            # Demo data
└── docs/                   # Documentation
```

## Steps

1. Copy supply-chain template as reference
2. Customize config.yaml
3. Add your ML models
4. Define event schemas
5. Create Flink jobs
6. Add domain-specific agents
7. Deploy and test

See supply-chain template for complete example.
