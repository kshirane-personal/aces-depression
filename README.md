# ACEs, Healthcare Engagement, and Depression: A BRFSS 2024 Analysis

Investigating the interaction effects between Adverse Childhood Experiences (ACEs) and preventive healthcare behaviors on depression risk, using CDC BRFSS 2024 data.

## Research Overview

- **Primary objective**: Test whether preventive healthcare engagement (routine checkups, cancer screenings, dental visits, vaccinations) buffers the adverse mental health effects of ACEs on depression risk
- **Secondary objective**: Explore non-linear interaction patterns using gradient boosting (XGBoost) and SHAP analysis
- **Data**: BRFSS 2024 (N≈59,900 ACE module respondents across 13 states/territories)

## Methods

- **Confirmatory**: Logistic regression with interaction terms, RERI (additive interaction), GAM
- **Exploratory**: XGBoost + SHAP interaction values
- **Causal framework**: DAG-based confounder adjustment

## Project Structure

```
├── data/
│   ├── raw/          # BRFSS XPT files (not tracked - see data/raw/README.md)
│   ├── processed/    # Analysis-ready datasets
│   └── interim/      # Intermediate files
├── docs/             # Research plan, references
├── notebooks/        # Exploratory analysis
├── src/              # Reusable analysis code
├── outputs/
│   ├── figures/      # Publication-ready figures
│   └── tables/       # Result tables
└── requirements.txt  # Python dependencies
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Download BRFSS 2024 data from [CDC](https://www.cdc.gov/brfss/annual_data/annual_2024.html) and place XPT files in `data/raw/`.

## Data Source

CDC Behavioral Risk Factor Surveillance System (BRFSS) 2024. Public-use, de-identified data.
