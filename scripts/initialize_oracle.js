const { Connection, PublicKey, Keypair } = require('@solana/web3.js');
const { Program, AnchorProvider, web3 } = require('@project-serum/anchor');
const fs = require('fs');

// Load your keypair
const keypairFile = require('os').homedir() + '/.config/solana/id.json';
const secretKey = new Uint8Array(JSON.parse(fs.readFileSync(keypairFile, 'utf8')));
const keypair = Keypair.fromSecretKey(secretKey);

// Connect to devnet
const connection = new Connection('https://api.devnet.solana.com', 'confirmed');
const provider = new AnchorProvider(connection, new Wallet(keypair), { commitment: 'confirmed' });

// Your program ID
const PROGRAM_ID = new PublicKey('G7i3UNUsFpm3NSAvY2wWtVqSM3HQhoxUJ5NyWSPZQDoL');

async function initializeOracle() {
    try {
        // Find the oracle state PDA
        const [oracleStatePda] = PublicKey.findProgramAddressSync(
            [Buffer.from('oracle')],
            PROGRAM_ID
        );

        console.log('Oracle State PDA:', oracleStatePda.toString());

        // Create the initialize instruction
        const initializeIx = await program.methods
            .initialize()
            .accounts({
                oracleState: oracleStatePda,
                authority: keypair.publicKey,
                systemProgram: web3.SystemProgram.programId,
            })
            .instruction();

        // Create and send transaction
        const transaction = new web3.Transaction().add(initializeIx);
        const signature = await provider.sendAndConfirm(transaction, [keypair]);
        
        console.log('Oracle initialized successfully!');
        console.log('Transaction signature:', signature);
        console.log('Oracle State address:', oracleStatePda.toString());
        
    } catch (error) {
        console.error('Error initializing oracle:', error);
    }
}

// Run the initialization
initializeOracle(); 