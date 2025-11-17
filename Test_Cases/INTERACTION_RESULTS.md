# Interaction-Based Results Separation

This document describes how to use Arcanum's results separation feature to compare passive vs. interactive extension testing for your research paper.

## Overview

The test harness now automatically captures and organizes taint logs, allowing you to quantify how interactions affect detected security threats. Each test run saves logs to a structured directory with metadata tracking whether interactions were used.

## Quick Start

### 1. Set Environment Variables

Before running tests, configure where results should be saved and what mode you're testing:

```bash
# Inside the Arcanum Docker container:
export ARCANUM_RESULTS_DIR="/root/arcanum_results"

# For passive (no-interaction) baseline:
export ARCANUM_RESULTS_MODE="passive"
python3.8 ~/Test_Cases/Custom_Test.py

# For interactive mode:
export ARCANUM_RESULTS_MODE="interactive"
python3.8 ~/Test_Cases/Custom_Test.py
```

### 2. Directory Structure

Results are organized automatically:

```
/root/arcanum_results/
├── amazon_address/
│   ├── amazon_address_mv2.crx/
│   │   ├── passive/
│   │   │   └── 20241117-143022/
│   │   │       ├── metadata.json
│   │   │       ├── v8logs/
│   │   │       │   ├── taint_sources.log
│   │   │       │   └── taint_storage.log
│   │   │       ├── user_data/
│   │   │       │   ├── taint_xhr.log
│   │   │       │   └── taint_fetch.log
│   │   │       └── browser_logs/
│   │   └── interactive/
│   │       └── 20241117-143045/
│   │           ├── metadata.json
│   │           ├── custom_interactive.json  # interaction spec if used
│   │           └── ...
│   └── amazon_address_mv3.crx/
│       └── ...
└── fb_post/
    └── ...
```

### 3. Metadata Format

Each run includes a `metadata.json` file:

```json
{
  "extension": "amazon_address_mv2.crx",
  "target_page": "amazon_address",
  "mode": "interactive",
  "timestamp": "20241117-143045",
  "interaction_used": true
}
```

## Analyzing Results

### Option 1: Use the Provided Script

```bash
python3.8 ~/Test_Cases/analyze_results.py /root/arcanum_results
```

This generates:
- `arcanum_analysis.csv`: structured data for each run
- Console summary: aggregate statistics by mode

CSV columns:
```
target_page,extension,mode,timestamp,interaction_used,sources_count,storage_sinks,xhr_sinks,fetch_sinks
```

### Option 2: Manual Analysis

Read the taint logs directly from the organized directories. For each extension/page pair:

1. **Count sources**: `grep -c ">>> Taint source:" */v8logs/taint_sources.log`
2. **Count sinks**: Check `user_data/taint_*.log` files for entries
3. **Compare payloads**: diff the actual log contents to see what new data appears under interactions

### Option 3: Custom Pipeline

Parse the JSON metadata and log files with your own tools (Python pandas, R tidyverse, etc.):

```python
import json
import pandas as pd
from pathlib import Path

runs = []
for metadata_file in Path('/root/arcanum_results').rglob('metadata.json'):
    with open(metadata_file) as f:
        meta = json.load(f)
    # Read corresponding log files from same directory
    # ... extract metrics ...
    runs.append(meta)

df = pd.DataFrame(runs)
# Group by (extension, target_page, mode) and aggregate
summary = df.groupby(['extension', 'target_page', 'mode']).agg({...})
```

## Paper Metrics

Use the separated results to compute:

1. **Interaction Lift**: % increase in detected sinks when using interactions
   - `(interactive_sinks - passive_sinks) / passive_sinks * 100`

2. **New Leak Discovery**: Count extensions with zero passive leaks but >0 interactive leaks
   - These represent threats invisible without user interaction

3. **Coverage**: Number of extensions where interactions unlocked additional behaviors
   - Compare unique sink destinations/payloads between modes

4. **Per-Site Analysis**: Which websites benefit most from interaction testing
   - Group by `target_page` and show mode differences

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ARCANUM_RESULTS_DIR` | `/root/arcanum_results/` | Root directory for organized logs |
| `ARCANUM_RESULTS_MODE` | `unspecified` | Label for this batch of runs (e.g., `passive`, `interactive`) |
| `ARCANUM_RESULTS_DISABLED` | `0` | Set to `1` to disable automatic result capture |

## Advanced Usage

### Batch Testing

Run all tests in both modes automatically:

```bash
#!/bin/bash
export ARCANUM_RESULTS_DIR="/root/arcanum_results"

# Passive baseline
export ARCANUM_RESULTS_MODE="passive"
python3.8 ~/Test_Cases/Custom_Test.py

# Interactive mode (requires interaction specs in ~/interactions/)
export ARCANUM_RESULTS_MODE="interactive"
python3.8 ~/Test_Cases/Custom_Test.py

# Analyze
python3.8 ~/Test_Cases/analyze_results.py /root/arcanum_results --csv results.csv
```

### Comparing Specific Extensions

To test one extension in both modes:

```bash
# Edit Custom_Test.py to comment out all tests except the one you want
# e.g., only run Amazon_Extension_MV2_Test()

export ARCANUM_RESULTS_MODE="passive"
python3.8 ~/Test_Cases/Custom_Test.py

export ARCANUM_RESULTS_MODE="interactive"
python3.8 ~/Test_Cases/Custom_Test.py

# Check results
ls -R /root/arcanum_results/amazon_address/amazon_address_mv2.crx/
```

### Disabling Results Capture

If you're debugging and don't want log pollution:

```bash
export ARCANUM_RESULTS_DISABLED=1
python3.8 ~/Test_Cases/Custom_Test.py
```

## Troubleshooting

**Q: Results directory is empty**
- Ensure `ARCANUM_RESULTS_DIR` is set and writable
- Check that tests are completing successfully (not erroring out before deinit)

**Q: interaction_used is always false**
- Verify interaction JSON files exist in `/root/interactions/`
- Check that `target_page` matches the JSON filename (e.g., `amazon_address.json`)

**Q: Metadata shows wrong mode**
- `ARCANUM_RESULTS_MODE` must be exported *before* running the test script

**Q: Logs are identical between modes**
- Extension may not have interaction-triggered behaviors
- Verify interaction spec actually executes (check console output for "Executing interaction script...")

## Example Workflow for Paper

```bash
# 1. Prepare environment
cd /root
mkdir -p arcanum_results interactions annotations

# 2. Copy artifacts
cp -r ~/Sample_Extensions/Custom/* /root/extensions/custom/
cp -r ~/recordings/* /root/recordings/
cp -r ~/annotations/* /root/annotations/
cp -r ~/interactions/* /root/interactions/

# 3. Run baseline
export ARCANUM_RESULTS_DIR="/root/arcanum_results"
export ARCANUM_RESULTS_MODE="passive"
python3.8 ~/Test_Cases/Custom_Test.py 2>&1 | tee passive_run.log

# 4. Run with interactions
export ARCANUM_RESULTS_MODE="interactive"
python3.8 ~/Test_Cases/Custom_Test.py 2>&1 | tee interactive_run.log

# 5. Analyze
python3.8 ~/Test_Cases/analyze_results.py /root/arcanum_results --csv paper_data.csv

# 6. Transfer results to host for visualization
# (Outside container)
docker cp run:/root/paper_data.csv ./
docker cp run:/root/arcanum_results/ ./results_backup/
```

Then use pandas/matplotlib or R/ggplot2 to generate figures showing interaction lift, per-extension improvements, etc.

