use anchor_lang::prelude::*;
use pyth_sdk_solana::{Price, PriceFeed};
use pyth_sdk_solana::state::SolanaPriceAccount;  // Remove PythError if not logging

declare_id!("FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa");

#[program]
pub mod sma_oracle {
    use super::*;

    #[account]
    pub struct OracleState {
        pub sma_1000: u64,
        pub last_update: i64,
    }

    pub fn update_sma(ctx: Context<UpdateSMA>, new_sma: u64) -> Result<()> {
        let pyth_account = &ctx.accounts.pyth_price_account;

        let price_feed: PriceFeed = SolanaPriceAccount::account_info_to_feed(pyth_account)
            .map_err(|_| ErrorCode::PythError.into())?;  // Simplified map_err; add logging if needed

        let clock = Clock::get()?;
        let current_time = clock.unix_timestamp;
        let max_age = 60u64;

        let current_price_opt: Option<Price> = price_feed.get_price_no_older_than(current_time, max_age);

        let price: Price = current_price_opt.ok_or(ErrorCode::StalePrice.into())?;

        require!(price.conf < (price.price.abs() as u64) / 1000, ErrorCode::HighConfidence.into());

        let current_price: u64 = if price.price >= 0 {
            price.price.try_into().map_err(|_| ErrorCode::InvalidPrice.into())?
        } else {
            return Err(ErrorCode::InvalidPrice.into());
        };

        require!(new_sma > current_price / 2 && new_sma < current_price * 2, ErrorCode::InvalidSMA.into());

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
    #[msg("Pyth oracle error")]
    PythError,
    #[msg("Stale price data")]
    StalePrice,
    #[msg("Invalid price value")]
    InvalidPrice,
    #[msg("High confidence interval - unreliable data")]
    HighConfidence,
}