carbon-trace/
├── config/
│   └── sectors.json          # Emission factors & caps
├── data/
│   ├── monthly_production.csv  # Synthetic dataset (we'll generate)
│   └── audit_summary_2026.csv  # Output: year-to-date totals
├── src/
│   ├── __init__.py
│   ├── closures.py           # Core closure factory
│   ├── models.py             # Factory class
│   ├── data_gen.py           # Synthetic CSV generator
│   └── runner.py             # Main orchestrator
├── tests/
│   └── test_closures.py      # State persistence tests
├── plot/
│   └── emissions_chart.png   # Output chart
├── main.py                   # Entry point + CLI
└── README.md                 # Instructions