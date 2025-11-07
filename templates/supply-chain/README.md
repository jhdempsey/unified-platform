# Supply Chain Vertical Template

Reference implementation for perishable food supply chain.

## What's Included

- **ML Models**: Demand forecasting, inventory optimization, supplier reliability
- **Schemas**: Order events, supplier events, inventory events
- **Flink Jobs**: Product recommendation engine
- **Agents**: Product generator, stream analysis
- **Sample Data**: Demo events for testing

## Configuration

See `config.yaml` for vertical-specific settings.

## Deployment

```bash
make deploy-dev VERTICAL=supply-chain
```

## Customization

Use this as a template for other supply chain scenarios or modify for your specific needs.
