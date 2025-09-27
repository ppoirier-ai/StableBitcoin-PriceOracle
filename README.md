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
- An off-chain Python script to fetch historical data from CoinGecko, compute the SBTC target price using the weighted ridge power law regression, and (optionally) update the on-chain program
- An on-chain Solana program (built with Anchor in Rust) that stores the SBTC target price, validates it against Pyth's real-time feeds for security, and exposes it for querying

**Key Features:**
- **On-chain Validation**: Uses Pyth Network's BTC/USD price feed for real-time price validation
- **Off-chain Computation**: Computes SBTC target prices off-chain to minimize Solana compute costs
- **Decentralized Data**: Leverages Pyth Network's aggregated price data from 100+ publishers
- **Mathematical Rigor**: Implements sophisticated power law regression with multiple regularization techniques

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
- Python 3.12+ with `requests`, `pandas`, `numpy`
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

### Off-chain SBTC Target Price Computation
Run the Python script to compute the SBTC target price:
```bash
python3 scripts/compute_sma.py
```

This fetches 365 days of historical BTC/USD data from CoinGecko and outputs the SBTC target price. The script:
- Fetches daily Bitcoin price data
- Computes weighted ridge power law regression with volatility weighting
- Applies time-based weighting and ridge regularization
- Implements dampening mechanism for stability
- Scales the result to cents for on-chain storage
- Outputs both the raw value and scaled value

### On-chain Deployment and Testing
1. Switch to devnet: `solana config set --url https://api.devnet.solana.com`
2. Deploy: `anchor deploy --provider.cluster devnet`
3. Test: `anchor test --skip-local-validator`

For mainnet, switch clusters and fund your wallet.

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

## License
Apache 2.0

## Acknowledgments
- Pyth Network for oracle data
- CoinGecko for historical price data
- Anchor framework for Solana development