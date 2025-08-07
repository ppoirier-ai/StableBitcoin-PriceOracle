# BTC 1000-Day SMA Oracle on Solana with Pyth Network

This repository implements a decentralized price oracle on Solana that computes and stores the 1000-day simple moving average (SMA) of Bitcoin's price (BTC/USD). It uses Pyth Network for real-time price validation and historical data fetching via Pyth Benchmarks.

The setup includes:
- An off-chain Python script to fetch historical data from Pyth Benchmarks, compute the SMA, and (optionally) update the on-chain program.
- An on-chain Solana program (built with Anchor in Rust) that stores the SMA, validates it against Pyth's real-time feeds for security, and exposes it for querying.

This oracle is designed for applications like StableBitcoin (SBTC), providing a stable peg to Bitcoin's long-term trend while smoothing short-term volatility.

## Features
- **Security**: Validates SMA updates against Pyth's decentralized real-time feeds to prevent manipulation. Uses multi-publisher aggregation from Pyth for decentralization.
- **Efficiency**: Computes SMA off-chain to minimize Solana compute costs; on-chain operations are lightweight (validation and storage only).
- **Decentralization**: Relies on Pyth's oracle network (100+ publishers); update authority can be multisig or DAO-controlled.
- **Integration**: Ready for extension to mint/burn logic in treasury applications.

## Prerequisites
- Rust (1.86+)
- Solana CLI (2.2+)
- Anchor CLI (0.31+)
- Python 3.12+ with `requests`, `pandas`, and optionally `solana` for on-chain updates.
- A Solana wallet and RPC endpoint (e.g., QuickNode).

## Setup
1. Clone the repo:
`git clone https://github.com/ppoirier-ai/BTC1000SMA.git`

2. Change Directory:
`cd BTC1000SMA`

3. Install dependencies:
- Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Solana: `curl --proto '=https' --tlsv1.2 -sSfL https://solana-install.solana.workers.dev | bash`
- Anchor: `cargo install --git https://github.com/solana-foundation/anchor avm --force`
- `avm install latest`
- `avm use latest`
- Python: `pip install requests pandas solana`
- `echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc`
- `echo 'export PATH="$HOME/.avm/bin:$PATH"' >> ~/.zshrc`
- `source ~/.zshrc`

# Verify Anchor is now accessible
anchor --version  # Should output something like "anchor-cli 0.31.1"

Create public & private keys & update files:
- in terminal: `solana-keygen new --outfile target/deploy/sma_oracle-keypair.json --no-bip39-passphrase` # copy the public key and passphrase in a secure location
- change the "YourProgramIDHere" in the file programs/sma_oracle/src/lib.rs and Anchor.toml with the public key created above

4. Build the Solana program:
`anchor build`

## Usage

### Off-chain SMA Computation
Run the Python script to compute the SMA:
python scripts/compute_sma.py

This fetches 1000 days of historical BTC/USD data from Pyth Benchmarks and outputs the SMA. Extend it to send updates to the on-chain program.

### On-chain Deployment and Testing
1. Switch to devnet: `solana config set --url https://api.devnet.solana.com`
2. Deploy: `anchor deploy`
3. Test: `anchor test`

For mainnet, switch clusters and fund your wallet.

### Updating the Oracle
- Manually: Use Anchor IDL to call `update_sma` with the computed SMA.
- Automated: Schedule the Python script with a cron job and integrate transaction signing.

## Security Considerations
- Use Pyth's confidence intervals for stricter validation.
- Implement rate-limiting on updates.
- Decentralize the update authority (e.g., via Squads multisig).
- Audit before production.

## License
Apache 2.0

## Acknowledgments
- Pyth Network for oracle data.
- Anchor framework for Solana development.
