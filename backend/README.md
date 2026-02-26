# Carbon-Trace

**Industrial Emission Auditor powered by Python closures**

This project is a proof‑of‑concept for SDG 13: Climate Action. It combines a
closure factory with simple object wrappers to securely accumulate factory‑
level emissions and deliver audit reports. A Flask web frontend allows users
to upload datasets and browse results interactively.

## Repository Structure

```text
carbon-trace/
├── config/                    # configuration values
│   └── sectors.json           # emission caps & energy multipliers
├── data/                      # data used by the CLI
│   ├── monthly_production.csv # synthetic dataset (generated if absent)
│   └── audit_summary_2026.csv # CLI output: year‑to‑date totals
├── plot/                      # CLI output directory
│   └── emissions_chart.png    # cumulative emissions chart
├── src/                       # core Python modules
│   ├── closures.py            # closure factory (private state)
│   ├── models.py              # Factory wrapper class
│   ├── data_gen.py            # synthetic CSV generator (seed optional)
│   ├── runner.py              # CLI audit engine
│   └── web_pipeline.py        # reusable pipeline for notebooks/web
├── web/                       # Flask application
│   ├── app.py
│   ├── templates/             # HTML pages
│   └── static/                # styles & copied outputs for display
├── tests/                     # unit/pipeline smoke tests
│   └── test_closures.py
├── main.py                    # command‑line entry point
└── README.md                  # this document
```

## Features

* **Closures** keep each factory's `total_emissions` private and immutable
  from the outside world.
* **Classes** (`Factory`) provide a clean interface and retain history.
* **Synthetic data generator** can be seeded or let run free for more
  realistic variability. Optional augmentation columns (`energy_source_type`,
  `raw_material_weight_tons`) are included.
* **Cleaning pipeline** injects realistic data issues and then handles them
  automatically.
* **Web application** allows uploading a OWID CO₂ file and an optional
  factory dataset; results include cleaned CSV, exploratory plots, audit
  summary, and alert information.
* **CLI mode** (`python main.py`) performs the full audit and writes outputs
  to `data/` and `plot/`.

## Getting Started

1. **Install requirements** (see `requirements.txt`):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run command‑line audit** (demonstrates closure behaviour):
   ```bash
   python main.py
   ```
   The first run will generate `data/monthly_production.csv` and then create
   `data/audit_summary_2026.csv` and `plot/emissions_chart.png`.

3. **Launch the web app** for an interactive experience:
   ```bash
   cd web
   export FLASK_APP=app.py
   flask run --port 8000
   ```
   Navigate to <http://localhost:8000>. Upload the OWID dataset (download
   from https://github.com/owid/co2-data) and, if available, a real
   monthly production file. The page displays clean data metrics, plots,
   alert tables, and links to download the cleaned and summary CSVs.

4. **Run tests**:
   ```bash
   pytest -q
   ```
   The suite covers closure state, independence, alert thresholds, and a
   smoke test of the web pipeline.

## Using Real‑World Data

If you already have factory‑level production/energy records, skip the
synthetic generator by supplying your own CSV via the web interface or by
calling `run_web_pipeline(..., production_csv="yourfile.csv")` from a
script. This satisfies the requirement to avoid random seeding and keeps the
results as accurate as the input data.

## Extending the Project

* Add additional sectors or more complex emission formulas inside
  `closures.make_emission_auditor`.
* Enhance the web UI with analytics, map views, or user authentication.
* Connect to a database or streaming source for continual auditing.

Enjoy building and iterating on Carbon‑Trace! 🎯
