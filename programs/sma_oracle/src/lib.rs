use anchor_lang::prelude::*;
use pyth_sdk_solana::load_price_account;

declare_id!("YourProgramIdHere");  // Update with actual ID after deployment

#[program]
pub mod sma_oracle {
    use super::*;

    #[account]
    pub struct OracleState {
        pub sma_1000: u64,  // Scaled price (e.g., USD cents)
        pub last_update: i64,
    }

    pub fn update_sma(ctx: Context<UpdateSMA>, new_sma: u64) -> Result<()> {
        let oracle_state = &mut ctx.accounts.oracle_state;

        // Validate against Pyth real-time feed
        let pyth_account = &ctx.accounts.pyth_price_account;
        let price_data = load_price_account(pyth_account.data.as_ref())?;
        let current_price = price_data.get_current_price()?.price as u64;  // Adjust for scaling

        // Sanity check: SMA within 50% of current
        require!(new_sma > current_price / 2 && new_sma < current_price * 2, ErrorCode::InvalidSMA);

        oracle_state.sma_1000 = new_sma;
        oracle_state.last_update = Clock::get()?.unix_timestamp;

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
}
