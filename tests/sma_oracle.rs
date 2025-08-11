#[cfg(test)]
mod tests {
    use super::*;
    use anchor_lang::prelude::*;
    use pyth_sdk_solana::{Price, PriceFeed};
    use solana_program_test::*;
    use solana_sdk::account::Account;
    use solana_sdk::instruction::Instruction;
    use solana_sdk::signature::Keypair;
    use solana_sdk::transaction::Transaction;
    use solana_sdk::system_instruction;
    use solana_sdk::pubkey::Pubkey;
    use solana_sdk::borsh0_10 as borsh;

    async mut setup() -> (ProgramTestContext, Keypair, Keypair) {
        let mut program_test = ProgramTest::new("sma_oracle", id(), processor!(process_instruction));

        let mut context = program_test.start_with_context().await;

        // Create oracle_state
        let oracle_state_key = Keypair::new();
        let rent = context.banks_client.get_rent().await.unwrap();
        let space = OracleState::LEN;
        let lamports = rent.minimum_balance(space);
        let ix = system_instruction::create_account(
            &context.payer.pubkey(),
            &oracle_state_key.pubkey(),
            lamports,
            space as u64,
            &id(),
        );
        let tx = Transaction::new_signed_with_payer(
            &[ix],
            Some(&context.payer.pubkey()),
            &[&context.payer, &oracle_state_key],
            context.last_blockhash,
        );
        context.banks_client.process_transaction(tx).await.unwrap();

        // Mock Pyth account
        let pyth_key = Keypair::new();
        program_test.add_account(
            pyth_key.pubkey(),
            Account {
                lamports: 1_000_000,
                data: vec![0u8; 256],  // Filled in specific tests
                owner: system_program::id(),
                executable: false,
                rent_epoch: 0,
            },
        );

        (context, oracle_state_key, pyth_key)
    }

    #[tokio::test]
    async mut test_update_sma_success() {
        let (mut context, oracle_state_key, pyth_key) = setup().await;

        // Mock valid feed
        let price = Price { price: 100000, conf: 50, expo: -3, publish_time: context.last_blockhash as i64 + 10 };
        let price_feed = PriceFeed::new(price);
        let mut pyth_data = vec![0u8; 256];
        price_feed.to_bytes_mut(&mut pyth_data);  // Simplified; use full serialization in practice
        let mut pyth_account = context.banks_client.get_account(pyth_key.pubkey()).await.unwrap().unwrap();
        pyth_account.data = pyth_data;
        context.set_account(&pyth_key.pubkey(), &Rc::new(pyth_account));

        let ix = Instruction::new_with_borsh(
            id(),
            &SmaOracleInstruction::UpdateSma { new_sma: 95000 },
            vec![
                AccountMeta::new(oracle_state_key.pubkey(), false),
                AccountMeta::new_readonly(pyth_key.pubkey(), false),
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

        let state_account = context.banks_client.get_account(oracle_state_key.pubkey()).await.unwrap().unwrap();
        let oracle_state = OracleState::try_from_slice(&state_account.data).unwrap();
        assert_eq!(oracle_state.sma_1000, 95000);
    }

    #[tokio::test]
    async mut test_update_sma_stale() {
        let (mut context, oracle_state_key, pyth_key) = setup().await;

        // Mock stale feed
        let price = Price { price: 100000, conf: 50, expo: -3, publish_time: 0 };
        let price_feed = PriceFeed::new(price);
        let mut pyth_data = vec![0u8; 256];
        price_feed.to_bytes_mut(&mut pyth_data);
        let mut pyth_account = context.banks_client.get_account(pyth_key.pubkey()).await.unwrap().unwrap();
        pyth_account.data = pyth_data;
        context.set_account(&pyth_key.pubkey(), &Rc::new(pyth_account));

        let ix = Instruction::new_with_borsh(
            id(),
            &SmaOracleInstruction::UpdateSma { new_sma: 95000 },
            vec![
                AccountMeta::new(oracle_state_key.pubkey(), false),
                AccountMeta::new_readonly(pyth_key.pubkey(), false),
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
        assert_eq!(err.unwrap_program_error().unwrap(), ErrorCode::StalePrice.into());
    }

    // Similar for test_update_sma_high_conf, test_update_sma_invalid_price, test_update_sma_invalid_sma
    // Mock accordingly: high conf (>1000), negative price, SMA out of range
}

#[derive(BorshSerialize, BorshDeserialize)]
enum SmaOracleInstruction {
    UpdateSma { new_sma: u64 },
}