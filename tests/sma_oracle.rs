#[cfg(test)]
mod tests {
    use super::*;
    use anchor_lang::prelude::*;
    use anchor_lang::solana_program::program::invoke_signed;
    use anchor_lang::system_program;
    use pyth_sdk_solana::{Price, PriceFeed};
    use solana_program_test::*;
    use solana_sdk::account::Account;
    use solana_sdk::instruction::Instruction;
    use solana_sdk::signature::Keypair;
    use solana_sdk::transaction::Transaction;

    async mut test_setup() -> (ProgramTestContext, Pubkey, Pubkey) {
        let mut program_test = ProgramTest::new(
            "sma_oracle",
            id(),
            processor!(process_instruction),
        );

        let mut context = program_test.start_with_context().await;

        // Create oracle_state PDA (assume simple seed for test)
        let (oracle_state_pda, bump) = Pubkey::find_program_address(&[b"oracle"], &id());
        let create_ix = Instruction::new_with_bytes(
            system_program::id(),
            &system_instruction::create_account(
                &context.payer.pubkey(),
                &oracle_state_pda,
                context.banks_client.get_rent().await.unwrap().minimum_balance(OracleState::LEN),
                OracleState::LEN as u64,
                &id(),
            ).data,
            &[&context.payer, &Keypair::new()],  // Dummy keypair for PDA creation
        );
        let tx = Transaction::new_signed_with_payer(
            &[create_ix],
            Some(&context.payer.pubkey()),
            &[&context.payer],
            context.last_blockhash,
        );
        context.banks_client.process_transaction(tx).await.unwrap();

        // Mock Pyth account
        let pyth_key = Keypair::new();
        program_test.add_account(
            pyth_key.pubkey(),
            Account {
                lamports: 1_000_000,
                data: vec![0u8; 256],  // Placeholder; fill with serialized feed in test
                owner: system_program::id(),
                executable: false,
                rent_epoch: 0,
            },
        );

        (context, oracle_state_pda, pyth_key.pubkey())
    }

    #[tokio::test]
    async mut test_update_sma_success() {
        let (mut context, oracle_state_pda, pyth_pda) = test_setup().await;

        // Mock valid PriceFeed
        let price_feed = PriceFeed::new(Price { price: 100000, conf: 50, expo: -3, publish_time: context.warp_to_slot(1).unwrap() as i64 });
        let serialized_feed = price_feed.to_bytes();  // Simplified; use actual serialization
        let mut pyth_account = context.banks_client.get_account(pyth_pda).await.unwrap().unwrap();
        pyth_account.data = serialized_feed;
        context.set_account(&pyth_pda, &Rc::new(pyth_account));

        let ix = Instruction::new_with_borsh(
            id(),
            &SmaOracleInstruction::UpdateSma { new_sma: 95000 },
            vec![
                AccountMeta::new(oracle_state_pda, false),
                AccountMeta::new_readonly(pyth_pda, false),
                AccountMeta::new_readonly(context.payer.pubkey(), true),
            ],
        );
        let tx = Transaction::new_signed_with_payer(
            &[ix],
            Some(&context.payer.pubkey()),
            &[&context.payer],
            context.last_blockhash,
        );
        context.banks_client.process_transaction(tx).await.unwrap();

        // Verify state
        let state = context.banks_client.get_account(oracle_state_pda).await.unwrap().unwrap();
        let oracle_state: OracleState = OracleState::try_deserialize(&mut state.data.as_slice()).unwrap();
        assert_eq!(oracle_state.sma_1000, 95000);
    }

    #[tokio::test]
    async mut test_update_sma_stale() {
        let (mut context, oracle_state_pda, pyth_pda) = test_setup().await;

        // Mock stale PriceFeed (old publish_time)
        let price_feed = PriceFeed::new(Price { price: 100000, conf: 50, expo: -3, publish_time: 0 });
        let serialized_feed = price_feed.to_bytes();
        let mut pyth_account = context.banks_client.get_account(pyth_pda).await.unwrap().unwrap();
        pyth_account.data = serialized_feed;
        context.set_account(&pyth_pda, &Rc::new(pyth_account));

        let ix = Instruction::new_with_borsh(
            id(),
            &SmaOracleInstruction::UpdateSma { new_sma: 95000 },
            vec![
                AccountMeta::new(oracle_state_pda, false),
                AccountMeta::new_readonly(pyth_pda, false),
                AccountMeta::new_readonly(context.payer.pubkey(), true),
            ],
        );
        let tx = Transaction::new_signed_with_payer(
            &[ix],
            Some(&context.payer.pubkey()),
            &[&context.payer],
            context.last_blockhash,
        );
        let err = context.banks_client.process_transaction(tx).await.unwrap_err();
        assert_eq!(err.unwrap_program_error().unwrap(), ErrorCode::StalePrice.into());  // Assert StalePrice error
    }

    // Add similar tests for HighConfidence, InvalidPrice, InvalidSMA
    #[tokio::test]
    async mut test_update_sma_high_conf() {
        // Mock with high conf (conf > abs_price / 1000)
        // Assert ErrorCode::HighConfidence
    }

    #[tokio::test]
    async mut test_update_sma_invalid_price() {
        // Mock with negative price
        // Assert ErrorCode::InvalidPrice
    }

    #[tokio::test]
    async mut test_update_sma_invalid_sma() {
        // Mock valid price, but new_sma out of range (e.g., 0 or very high)
        // Assert ErrorCode::InvalidSMA
    }
}

#[derive(BorshSerialize, BorshDeserialize)]
enum SmaOracleInstruction {
    UpdateSma { new_sma: u64 },
}