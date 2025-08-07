use anchor_lang::prelude::*;
use pyth_sdk_solana::{load_price_feed_from_account_info, Price, PriceFeed};

declare_id!("FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa");  // Replace with actual from anchor keys sync

#[program]
pub mod sma_oracle {
    use super::*;

    #[account]
    pub struct OracleState {
        pub sma_1000: u64,  // Scaled price (e.g., USD cents)
        pub last_update: i64,
    }

    pub fn update_sma(ctx: Context<UpdateSMA>, new_sma: u64) -> Result<()> {
        let pyth_account = &ctx.accounts.pyth_price_account;

        // Load Pyth price feed with error mapping
        let price_feed: PriceFeed = load_price_feed_from_account_info(pyth_account).map_err(|_| ErrorCode::PythError)?;

        // Get current price with staleness check (max 60s old)
        let clock = Clock::get()?;
        let max_age = 60u64;  // Staleness threshold in seconds
        let current_price_opt: Option<Price> = price_feed.get_price_no_older_than(clock.unix_timestamp, max_age);

        let price: Price = current_price_opt.ok_or(ErrorCode::StalePrice)?;

        // Security: Check confidence interval to ensure reliable data
        require!(price.conf < 1000, ErrorCode::HighConfidence);  // Example threshold; adjust based on feed

        // Convert i64 price to u64 (assume positive for BTC/USD; handle expo if needed)
        let current_price: u64 = price.price.try_into().map_err(|_| ErrorCode::InvalidPrice)?;

        // Sanity check: SMA within 50% of current price
        require!(new_sma > current_price / 2 && new_sma < current_price * 2, ErrorCode::InvalidSMA);

        let oracle_state = &mut ctx.accounts.oracle_state;
        oracle_state.sma_1000 = new_sma;
        oracle_state.last_update = clock.unix_timestamp;

        Ok(())
    }

    pub fn get_sma(ctx: Context<GetSMA>) -> Result<u64> {
        Ok(ctx.accounts.oracle_state.sma_1000)
    }
}

#[derive(Accounts)]
pub struct UpdateSMA<'info> {
    #[account(mut)]
    pub oracle_state: Account<'info, OracleState>,
    pub pyth_price_account: AccountInfo<'info>,  // Pyth BTC/USD feed account
    #[account(signer)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct GetSMA<'info> {
    pub oracle_state: Account<'info, OracleState>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid SMA value")]
    InvalidSMA,
    #[msg("Pyth oracle error")]
    PythError,
    #[msg("Stale price data")]
    StalePrice,
    #[msg("Invalid price value")]
    InvalidPrice,
    #[msg("High confidence interval - unreliable data")]
    HighConfidence,
}