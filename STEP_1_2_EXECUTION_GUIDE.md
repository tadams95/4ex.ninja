# Step 1.2 Execution Guide
## Data Acquisition & Preparation

### Quick Start

Execute Step 1.2 with a single command:

```bash
./execute_step_1_2.sh
```

### What This Does

The Step 1.2 execution process includes:

1. **🔍 Pre-execution Validation**
   - Tests infrastructure readiness
   - Validates backup data sources
   - Ensures OANDA API connectivity

2. **📦 Infrastructure Setup**
   - Configures backup data sources
   - Creates necessary directories
   - Sets up logging and reporting

3. **📊 Data Acquisition**
   - Downloads historical data for all target currency pairs
   - Covers major and minor pairs across multiple timeframes
   - Implements retry logic and error handling

4. **🔍 Quality Validation**
   - Validates data completeness
   - Checks for gaps and anomalies
   - Generates quality scores

5. **📋 Report Generation**
   - Creates detailed completion reports
   - Generates markdown summaries
   - Provides next step recommendations

### Expected Outputs

After successful execution:

```
backtest_results/step_1_2_execution/
├── step_1_2_completion_report_YYYYMMDD_HHMMSS.json
├── step_1_2_summary_YYYYMMDD_HHMMSS.md
└── execution_summary_YYYYMMDD_HHMMSS.json

data/historical/
├── EURUSD_M1_20240101_20241231.csv
├── EURUSD_M5_20240101_20241231.csv
├── EURUSD_H1_20240101_20241231.csv
├── EURUSD_H4_20240101_20241231.csv
├── EURUSD_D1_20240101_20241231.csv
└── ... (all other pairs and timeframes)

logs/
├── step_1_2_execution.log
└── data_acquisition.log
```

### Target Data

**Currency Pairs:**
- **Major Pairs (8):** EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD, EUR/GBP
- **Minor Pairs (12):** EUR/JPY, EUR/CHF, EUR/AUD, EUR/CAD, EUR/NZD, GBP/JPY, GBP/CHF, GBP/AUD, GBP/CAD, AUD/JPY, CHF/JPY, CAD/JPY

**Timeframes:** M1, M5, H1, H4, D1

**Period:** January 1, 2024 - December 31, 2024

**Total Combinations:** 20 pairs × 5 timeframes = 100 data files

### Prerequisites

1. **OANDA API Access**
   - Valid OANDA account with API access
   - API token configured in environment

2. **Environment Setup**
   - Python 3.8+ with required packages
   - Sufficient disk space (estimated 2-5 GB)
   - Stable internet connection

3. **Configuration Files**
   - `.env` file with OANDA credentials
   - `config/config.yaml` for system settings

### Troubleshooting

**Common Issues:**

1. **OANDA API Errors**
   ```
   Check logs/step_1_2_execution.log for API-specific errors
   Verify API token and account permissions
   ```

2. **Network Timeouts**
   ```
   Pipeline includes automatic retry logic
   Check network connectivity and firewall settings
   ```

3. **Disk Space Issues**
   ```
   Ensure at least 5 GB free space in project directory
   Check data/ directory permissions
   ```

4. **Missing Dependencies**
   ```
   Run: pip install -r requirements.txt
   Check that all required packages are installed
   ```

### Manual Execution

If you prefer to run components individually:

```bash
# Navigate to backend directory
cd 4ex.ninja-backend

# Test infrastructure
python scripts/test_data_acquisition.py

# Run data acquisition
python scripts/data_acquisition_pipeline_fixed.py

# Run full execution pipeline
python scripts/execute_step_1_2.py
```

### Success Criteria

Step 1.2 is considered successful when:

- ✅ ≥80% of target data files downloaded successfully
- ✅ Average data quality score ≥85%
- ✅ Missing data percentage ≤0.1%
- ✅ All quality validation reports generated
- ✅ Backup data source configuration completed

### Next Steps

Upon successful completion:

1. **Review Reports**
   - Check completion report for detailed metrics
   - Review quality validation results
   - Identify any data gaps or issues

2. **Backup Data**
   - Archive downloaded data files
   - Save execution reports
   - Document any configuration changes

3. **Proceed to Step 2.1**
   - Strategy Parameter Configuration
   - Use completed data for backtesting
   - Begin comprehensive testing phase

### Support

For issues or questions:
- Check logs in `logs/` directory
- Review execution reports in `backtest_results/step_1_2_execution/`
- Consult the comprehensive backtesting plan documentation
