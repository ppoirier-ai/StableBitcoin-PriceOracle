use anchor_lang::prelude::*;
use pyth_sdk_solana::{SolanaPriceAccount, Price, PriceFeed};

declare_id!("FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa");  // Replace with actual ID

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

        // Corrected Pyth loading: Pass reference &pyth_account
        let price_feed: PriceFeed = SolanaPriceAccount::account_info_to_feed(&pyth_account)
            .map_err(|e| error!(ErrorCode::PythError { inner: e }))?;  // Map PythError for better tracing

        let clock = Clock::get()?;
        let max_age = 60u64;  // Staleness threshold
        let current_price_opt: Option<Price> = price_feed.get_price_no_older_than(clock.unix_timestamp as u64, max_age);

        let price: Price = current_price_opt.ok_or(ErrorCode::StalePrice)?;

        // Stricter confidence check (e.g., <0.1% of price; adjust for BTC volatility)
        require!(price.conf < price.price.abs() / 1000, ErrorCode::HighConfidence);

        // Convert i64 to u64, assuming positive BTC price
        let current_price: u64 = price.price.try_into().map_err(|_| ErrorCode::InvalidPrice)?;

        // Sanity check
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
    pub pyth_price_account: AccountInfo<'info>,
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
    #[msg("Pyth oracle error: {inner}")]
    PythError { inner: pyth_sdk_solana::PythError },  // Enhanced with inner error
    #[msg("Stale price data")]
    StalePrice,
    #[msg("Invalid price value")]
    InvalidPrice,
    #[msg("High confidence interval - unreliable data")]
    HighConfidence,
}