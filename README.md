# SBTC Target Price Oracle on Solana with Pyth Network

This repository implements a decentralized price oracle on Solana that computes and stores the target price for SBTC (StableBitcoin) tokens based on Bitcoin's long-term growth trends using a smoothed rolling-window power law regression of the price of Bitcoin.

## SBTC Target Price Algorithm

The target price for SBTC (StableBitcoin) tokens is computed using the following methodology:

A rolling weighted ridge power law regression on Bitcoin's price data, fitted over a sliding window of historical bars (default: 1000 days), to model long-term growth trends following a power law form y=a⋅x^b, linearized via logarithms for regression (log(y) ≈ c + b⋅log(x)). The regression incorporates:

- **Ridge regularization** on the slope b to prevent overfitting and flatten extreme curves
- **Time-based weighting** to emphasize recent data
- **Volatility-based weighting** to downweight high-volatility periods
- **Pre- and post-regression smoothing** via simple moving averages (SMAs) to reduce noise
- **Dampening mechanism** to cap relative deviations in the output curve for stability

It enforces daily timeframe consistency across any chart resolution using request.security with the "D" interval, ensuring invariant values regardless of the viewed timeframe.

### Key Computational Steps:

1. **Volatility Calculation**: Standard deviation of log returns (Δlog(close)) over a window (default vol_length = 20)
2. **Input Smoothing**: SMA applied to closing prices (default input_smooth_length = 150)
3. **Weighted Ridge Regression**: Custom function computes sums for weighted least squares with ridge penalty (λ, default 50) on b; time weights via (length−k)^time_weight_power (default 1.50, higher favors recency); volatility weights via 1/(|vol|+ε)^vol_weight_power (default 1.50, higher penalizes volatility); handles NA values and ensures positive x,y
4. **Output Smoothing**: SMA on the regression output (default output_smooth_length = 1000)
5. **Dampening**: Limits relative log deviations in the final curve to a threshold multiple (k, default 0.1) of the stdev of log returns over a window (default stdev_length = 1000), clamping excessive changes via exponential adjustment

## Implementation

The setup includes:
- An off-chain Python script to fetch historical data from Pyth Network, compute the SBTC target price using the weighted ridge power law regression, and (optionally) update the on-chain program
- An on-chain Solana program (built with Anchor in Rust) that stores the SBTC target price, validates it against Pyth's real-time feeds for security, and exposes it for querying

**Key Features:**
- **On-chain Validation**: Uses Pyth Network's BTC/USD price feed for real-time price validation
- **Off-chain Computation**: Computes SBTC target prices off-chain to minimize Solana compute costs
- **Decentralized Data**: Leverages Pyth Network's aggregated price data from 100+ publishers
- **Mathematical Rigor**: Implements sophisticated power law regression with multiple regularization techniques
- **Single Data Source**: Uses Pyth Network exclusively for both historical and real-time Bitcoin price data

## Features
- **Mathematical Rigor**: Implements weighted ridge power law regression with multiple regularization techniques
- **Security**: Validates SBTC target price updates against Pyth's decentralized real-time feeds to prevent manipulation
- **Efficiency**: Computes SBTC target prices off-chain to minimize Solana compute costs; on-chain operations are lightweight (validation and storage only)
- **Decentralization**: Relies on Pyth's oracle network (100+ publishers); update authority can be multisig or DAO-controlled
- **Integration**: Ready for extension to mint/burn logic in treasury applications
- **Stability**: Dampening mechanism prevents excessive volatility in the SBTC target price

## Algorithm Parameters

The SBTC target price computation uses the following default parameters:
- **Regression Window**: 1000 days (sliding window for power law regression)
- **Ridge Penalty (λ)**: 50 (prevents overfitting)
- **Time Weight Power**: 1.50 (emphasizes recent data)
- **Volatility Weight Power**: 1.50 (penalizes high volatility periods)
- **Input Smoothing**: 150-day SMA on closing prices
- **Output Smoothing**: 1000-day SMA on regression output
- **Dampening Threshold (k)**: 0.1 (caps relative deviations)
- **Volatility Window**: 20 days (for log return calculation)
- **Standard Deviation Window**: 1000 days (for dampening calculation)

## Prerequisites
- Rust (1.86+)
- Solana CLI (2.2+)
- Anchor CLI (0.31+)
- Python 3.12+ with `requests`, `pandas`, `numpy`, and `flask`
- For production: `gunicorn` (WSGI server) and `jq` (JSON processor)
- A Solana wallet and RPC endpoint (e.g., QuickNode)

## Setup
1. Clone the repo:
```bash
git clone https://github.com/ppoirier-ai/BTC1000SMA.git
```

2. Change Directory:
```bash
cd BTC1000SMA
```

3. Install dependencies:
- Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Solana: `curl --proto '=https' --tlsv1.2 -sSfL https://solana-install.solana.workers.dev | bash`
- Anchor: `cargo install --git https://github.com/solana-foundation/anchor avm --force`
- `avm install latest`
- `avm use latest`
- Python: `conda install pandas requests numpy` (or `pip install pandas requests numpy`)
- `echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc`
- `echo 'export PATH="$HOME/.avm/bin:$PATH"' >> ~/.zshrc`
- `source ~/.zshrc`

# Verify Anchor is now accessible
```bash
anchor --version  # Should output something like "anchor-cli 0.31.1"
```

4. Build the Solana program:
```bash
anchor build
```

## Usage

### Quick Start
1. **Start the API server:**
   ```bash
   cd scripts
   python sbtc_api.py
   ```

2. **Test the API:**
   ```bash
   curl http://localhost:5000/sbtc/current
   ```

3. **Deploy the Solana program:**
   ```bash
   anchor deploy --provider.cluster devnet
   ```

### API Server Deployment

#### Local Development
1. **Install Dependencies:**
   ```bash
   pip install flask requests pandas numpy
   ```

2. **Start the API Server:**
   ```bash
   cd scripts
   python sbtc_api.py
   ```
   The server will start on `http://localhost:5000`

3. **Test the API:**
   ```bash
   # Run automated tests
   python test_api.py
   
   # Or test manually
   curl http://localhost:5000/sbtc/current
   curl http://localhost:5000/health
   ```

#### Production Deployment (Cloud Server)
1. **Deploy to Cloud Server:**
   ```bash
   # Upload files to your cloud server
   scp -r scripts/ user@your-server:/path/to/sbtc-oracle/
   
   # SSH into server
   ssh user@your-server
   
   # Install dependencies
   pip install flask requests pandas numpy gunicorn
   
   # Start with Gunicorn (production WSGI server)
   cd /path/to/sbtc-oracle/scripts
   gunicorn -w 4 -b 0.0.0.0:5000 sbtc_api:app
   ```

2. **Set up Process Management:**
   ```bash
   # Using systemd (Ubuntu/Debian)
   sudo nano /etc/systemd/system/sbtc-oracle.service
   ```
   
   Add the following service configuration:
   ```ini
   [Unit]
   Description=SBTC Target Price Oracle API
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/path/to/sbtc-oracle/scripts
   ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 sbtc_api:app
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start the service:
   ```bash
   sudo systemctl enable sbtc-oracle
   sudo systemctl start sbtc-oracle
   sudo systemctl status sbtc-oracle
   ```

3. **Set up Cron Job for Regular Updates:**
   ```bash
   # Edit crontab
   crontab -e
   
   # Add this line to update every hour
   0 * * * * curl -X GET http://localhost:5000/sbtc/current > /var/log/sbtc-update.log 2>&1
   ```

### API Endpoints

#### 1. Compute SBTC Target Price
```bash
GET /sbtc/current
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current_btc_price": 46689.71,
    "sbtc_target_price": 46689.71,
    "sbtc_scaled_cents": 4668970,
    "data_points_used": 1000,
    "computation_timestamp": "2025-09-28T11:38:22.496636",
    "data_source": "Pyth Network BTC/USD Price Feed (8SXvChNYFh3qEi4J6tK1wQREu5x6YdE3C6HmZzThoG6E)"
  }
}
```

#### 2. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-28T11:38:18.535357"
}
```

#### 3. Store SBTC Datapoint
```bash
POST /datapoints/store
```

**Request Body (optional):**
```json
{
  "sbtc_value": 47000.0,
  "btc_price": 46500.0,
  "data_points_used": 1000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "datapoint": {
      "timestamp": 1759553648,
      "sbtc_value": 47000.0,
      "btc_price": 46500.0,
      "data_points_used": 1000,
      "stored_at": "2025-10-04T12:54:08.857441"
    },
    "total_datapoints": 1
  }
}
```

#### 4. Get Last Datapoint
```bash
GET /datapoints/last
```

**Response:**
```json
{
  "success": true,
  "data": {
    "datapoint": {
      "timestamp": 1759553648,
      "sbtc_value": 47000.0,
      "btc_price": 46500.0,
      "data_points_used": 1000,
      "stored_at": "2025-10-04T12:54:08.857441"
    },
    "total_datapoints": 1
  }
}
```

#### 5. Get Datapoint Batch
```bash
GET /datapoints/batch?start_timestamp=1759553600&end_timestamp=1759553700
```

**Response:**
```json
{
  "success": true,
  "data": {
    "datapoints": [
      {
        "timestamp": 1759553648,
        "sbtc_value": 47000.0,
        "btc_price": 46500.0,
        "data_points_used": 1000,
        "stored_at": "2025-10-04T12:54:08.857441"
      }
    ],
    "count": 1,
    "start_timestamp": 1759553600,
    "end_timestamp": 1759553700,
    "total_datapoints": 1
  }
}
```

#### 6. API Information
```bash
GET /
```

**Response:**
```json
{
  "name": "SBTC Target Price Oracle API",
  "version": "1.0.0",
  "description": "Computes SBTC target price using weighted ridge power law regression on Bitcoin price data",
  "endpoints": {
    "GET /sbtc/current": "Compute current SBTC target price using 1000 days of BTC data",
    "POST /datapoints/store": "Store a new SBTC datapoint with timestamp and value",
    "GET /datapoints/last": "Get the most recent SBTC datapoint",
    "GET /datapoints/batch?start_timestamp=X&end_timestamp=Y": "Get datapoints within timestamp range",
    "GET /health": "Health check",
    "GET /": "This information"
  }
}
```

### Datapoint Storage and Retrieval

The API provides comprehensive datapoint storage and retrieval functionality:

#### Features
- **Automatic SBTC Computation**: Store datapoints with auto-computed SBTC values
- **Custom Values**: Store datapoints with custom SBTC, BTC price, and data point counts
- **Timestamp-based Queries**: Retrieve datapoints within specific time ranges
- **In-memory Storage**: Fast access to recent datapoints (keeps last 1000)
- **RESTful API**: Simple HTTP endpoints for all operations

#### Usage Examples

**Store a datapoint with auto-computed values:**
```bash
curl -X POST http://localhost:5000/datapoints/store \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Store a datapoint with custom values:**
```bash
curl -X POST http://localhost:5000/datapoints/store \
  -H "Content-Type: application/json" \
  -d '{
    "sbtc_value": 47000.0,
    "btc_price": 46500.0,
    "data_points_used": 1000
  }'
```

**Get the most recent datapoint:**
```bash
curl http://localhost:5000/datapoints/last
```

**Get datapoints from the last hour:**
```bash
curl "http://localhost:5000/datapoints/batch?start_timestamp=$(date -d '1 hour ago' +%s)&end_timestamp=$(date +%s)"
```

**Get datapoints from the last 24 hours:**
```bash
curl "http://localhost:5000/datapoints/batch?start_timestamp=$(date -d '1 day ago' +%s)&end_timestamp=$(date +%s)"
```

### On-chain Integration

#### Deploy Solana Program
1. **Switch to devnet:**
   ```bash
   solana config set --url https://api.devnet.solana.com
   ```

2. **Deploy the program:**
   ```bash
   anchor deploy --provider.cluster devnet
   ```

3. **Test the program:**
   ```bash
   anchor test --skip-local-validator
   ```

#### Update Oracle with API Data
```bash
# Get current SBTC target price from API
SBTC_VALUE=$(curl -s http://localhost:5000/sbtc/current | jq -r '.data.sbtc_scaled_cents')

# Update the on-chain oracle (example using Solana CLI)
solana program invoke --program-id FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa \
  --accounts oracle_state=<ORACLE_STATE_ACCOUNT> \
  --accounts pyth_price_account=8SXvChNYFh3qEi4J6tK1wQREu5x6YdE3C6HmZzThoG6E \
  --accounts authority=<YOUR_WALLET> \
  --data update_trend $SBTC_VALUE
```

### Automated Updates

#### Using Cron Job
```bash
# Create update script
cat > /path/to/update_oracle.sh << 'EOF'
#!/bin/bash
API_URL="http://localhost:5000/sbtc/current"
LOG_FILE="/var/log/sbtc-oracle-update.log"

# Get SBTC value from API
RESPONSE=$(curl -s "$API_URL")
SBTC_VALUE=$(echo "$RESPONSE" | jq -r '.data.sbtc_scaled_cents')

if [ "$SBTC_VALUE" != "null" ] && [ "$SBTC_VALUE" != "" ]; then
    echo "$(date): Updating oracle with SBTC value: $SBTC_VALUE" >> "$LOG_FILE"
    # Add your Solana program update command here
    # solana program invoke ...
else
    echo "$(date): Failed to get SBTC value from API" >> "$LOG_FILE"
fi
EOF

chmod +x /path/to/update_oracle.sh

# Add to crontab (update every hour)
echo "0 * * * * /path/to/update_oracle.sh" | crontab -
```

#### Using Python Script
```python
import requests
import subprocess
import time

def update_oracle():
    try:
        # Get SBTC value from API
        response = requests.get('http://localhost:5000/sbtc/current')
        data = response.json()
        
        if data['success']:
            sbtc_value = data['data']['sbtc_scaled_cents']
            print(f"Updating oracle with SBTC value: {sbtc_value}")
            
            # Update on-chain oracle
            # Add your Solana program update command here
            # subprocess.run(['solana', 'program', 'invoke', ...])
            
        else:
            print(f"API error: {data['error']}")
            
    except Exception as e:
        print(f"Update failed: {e}")

# Run every hour
while True:
    update_oracle()
    time.sleep(3600)  # 1 hour
```

### Updating the Oracle
- **Manually**: Use Anchor IDL to call `update_trend` with the computed SBTC target price
- **Automated**: Schedule the Python script with a cron job and integrate transaction signing

### Program Functions
- `initialize()`: Initialize the oracle state account
- `update_trend(new_sbtc_target: u64)`: Update the oracle with a new SBTC target price (validates against Pyth price)
- `get_trend()`: Retrieve the current SBTC target price

## Security Considerations
- Uses Pyth's confidence intervals for validation
- Validates SBTC target prices against current Bitcoin price (within 10x range)
- Implements rate-limiting on updates
- Decentralize the update authority (e.g., via Squads multisig)
- Mathematical validation of regression parameters
- Audit before production

## Program ID
- **Devnet**: `FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa`
- **Localnet**: `FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa`

## Pyth Network Price Feed
- **BTC/USD Price Feed**: `8SXvChNYFh3qEi4J6tK1wQREu5x6YdE3C6HmZzThoG6E`
- **Network**: Solana Mainnet/Devnet
- **Data Source**: Pyth Network aggregated from 100+ publishers
- **Usage**: Both historical data fetching and real-time price validation

## License
Apache 2.0

## Acknowledgments
- Pyth Network for both historical and real-time Bitcoin price data
- Anchor framework for Solana development