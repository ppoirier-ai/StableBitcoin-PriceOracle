use anchor_lang::prelude::*;
use pyth_sdk_solana::{Price, PriceFeed, PythError};
use pyth_sdk_solana::state::SolanaPriceAccount;

declare_id!("FtDpp1TsamUskkz2AS7NTuRGqyB3j4dpP7mj9ATHbDoa");

#[program]
pub mod sma_oracle {
    use super::*;

    #[account]
    pub struct OracleState {
        pub trend_value: u64,
        pub last_update: i64,
    }

    #[account]
    pub struct Datapoint {
        pub timestamp: i64,
        pub sbtc_value: u64, // SBTC value in cents
        pub btc_price: u64,  // BTC price at time of computation in cents
        pub data_points_used: u32, // Number of historical data points used
    }

    pub fn update_trend(ctx: Context<UpdateTrend>, new_trend: u64) -> Result<()> {
        let pyth_account = &ctx.accounts.pyth_price_account;

        let price_feed: PriceFeed = SolanaPriceAccount::account_info_to_feed(pyth_account)
            .map_err(|e: PythError| {
                msg!("Pyth error: {:?}", e);
                ErrorCode::PythError
            })?;

        let clock = Clock::get()?;
        let current_time = clock.unix_timestamp;
        let max_age = 60u64;

        let current_price_opt: Option<Price> = price_feed.get_price_no_older_than(current_time, max_age);

        let price: Price = current_price_opt.ok_or(ErrorCode::StalePrice)?;

        // Confidence check - ensure confidence is reasonable
        require!(price.conf < price.price.unsigned_abs() / 1000u64, ErrorCode::HighConfidence);

        // Convert price to u64 (Pyth prices are in base units)
        let current_price: u64 = if price.price >= 0 {
            // Convert from Pyth's base units to cents
            let price_in_cents = (price.price as u64) / (10u64.pow((-price.expo) as u32 - 2));
            price_in_cents
        } else {
            return Err(anchor_lang::error::Error::from(ErrorCode::InvalidPrice));
        };

        // Trend validation: should be within reasonable bounds of current price
        require!(new_trend > current_price / 10 && new_trend < current_price * 10, ErrorCode::InvalidTrend);

        let oracle_state = &mut ctx.accounts.oracle_state;
        oracle_state.trend_value = new_trend;
        oracle_state.last_update = clock.unix_timestamp;

        msg!("Updated trend value: {} cents (current BTC price: {} cents)", new_trend, current_price);

        Ok(())
    }

    pub fn get_trend(ctx: Context<GetTrend>) -> Result<u64> {
        Ok(ctx.accounts.oracle_state.trend_value)
    }

    pub fn store_datapoint(ctx: Context<StoreDatapoint>, sbtc_value: u64, btc_price: u64, data_points_used: u32) -> Result<()> {
        let clock = Clock::get()?;
        let current_time = clock.unix_timestamp;

        let datapoint = &mut ctx.accounts.datapoint;
        datapoint.timestamp = current_time;
        datapoint.sbtc_value = sbtc_value;
        datapoint.btc_price = btc_price;
        datapoint.data_points_used = data_points_used;

        msg!("Stored datapoint: timestamp={}, sbtc_value={}, btc_price={}, data_points={}", 
             current_time, sbtc_value, btc_price, data_points_used);

        Ok(())
    }

    pub fn get_last_datapoint(ctx: Context<GetLastDatapoint>) -> Result<Datapoint> {
        let datapoint = &ctx.accounts.datapoint;
        Ok(Datapoint {
            timestamp: datapoint.timestamp,
            sbtc_value: datapoint.sbtc_value,
            btc_price: datapoint.btc_price,
            data_points_used: datapoint.data_points_used,
        })
    }

    pub fn get_datapoint_batch(ctx: Context<GetDatapointBatch>, start_timestamp: i64, end_timestamp: i64) -> Result<Vec<Datapoint>> {
        // For now, return a single datapoint. In a full implementation, you'd query multiple accounts
        // or use a more sophisticated storage mechanism
        let datapoint = &ctx.accounts.datapoint;
        if datapoint.timestamp >= start_timestamp && datapoint.timestamp <= end_timestamp {
            Ok(vec![Datapoint {
                timestamp: datapoint.timestamp,
                sbtc_value: datapoint.sbtc_value,
                btc_price: datapoint.btc_price,
                data_points_used: datapoint.data_points_used,
            }])
        } else {
            Ok(vec![])
        }
    }
}

#[derive(Accounts)]
pub struct UpdateTrend<'info> {
    #[account(mut)]
    pub oracle_state: Account<'info, sma_oracle::OracleState>,
    /// CHECK: This is a Pyth price account that we validate through the Pyth SDK
    /// Pyth Network BTC/USD price feed: 8SXvChNYFh3qEi4J6tK1wQREu5x6YdE3C6HmZzThoG6E
    pub pyth_price_account: AccountInfo<'info>,
    #[account(signer)]
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct GetTrend<'info> {
    pub oracle_state: Account<'info, sma_oracle::OracleState>,
}

#[derive(Accounts)]
pub struct StoreDatapoint<'info> {
    #[account(init, payer = authority, space = 8 + 8 + 8 + 8 + 4)]
    pub datapoint: Account<'info, sma_oracle::Datapoint>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct GetLastDatapoint<'info> {
    pub datapoint: Account<'info, sma_oracle::Datapoint>,
}

#[derive(Accounts)]
pub struct GetDatapointBatch<'info> {
    pub datapoint: Account<'info, sma_oracle::Datapoint>,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid trend value")]
    InvalidTrend,
    #[msg("Pyth oracle error")]
    PythError,
    #[msg("Stale price data")]
    StalePrice,
    #[msg("Invalid price value")]
    InvalidPrice,
    #[msg("High confidence interval - unreliable data")]
    HighConfidence,
    #[msg("Invalid datapoint timestamp")]
    InvalidTimestamp,
    #[msg("Datapoint not found")]
    DatapointNotFound,
}

pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    let oracle_state = &mut ctx.accounts.oracle_state;
    oracle_state.trend_value = 0;
    oracle_state.last_update = 0;
    Ok(())
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(init, payer = authority, space = 8 + 8 + 8, seeds = [b"oracle"], bump)]
    pub oracle_state: Account<'info, OracleState>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}