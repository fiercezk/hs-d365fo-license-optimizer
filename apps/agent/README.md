# D365 FO License Agent - Algorithm Engine

Python-based deterministic algorithm engine for license optimization.

## Setup

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Run Tests

```bash
pytest
```

## Phase 1 Algorithms (11 total)

- **2.2**: Read-Only User Detection
- **2.5**: License Minority Detection
- **3.1**: Segregation of Duties (SoD) Conflict Detection
- **3.2**: Redundant Role Detection
- **3.3**: Unused License Detection
- **3.4**: Seasonal Pattern Detection
- **4.1**: Role Right-Sizing
- **4.3**: License Reduction Prediction
- **4.7**: New User License Recommendation
- **5.1**: License Cost Trend Analysis
- **5.2**: Security Risk Scoring

See `/Requirements/` for full specifications.
