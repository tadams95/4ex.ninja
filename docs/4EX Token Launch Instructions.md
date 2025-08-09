# Step-by-Step Instructions to Launch $4EX Token on Base Using Clanker

## Prerequisites
- **Farcaster Account**: Sign up on Warpcast (Farcaster client) with a reputable Neynar score (active engagement helps). Needed for Clanker’s social deployment. Alternatively, use clanker.world.
- **Coinbase Wallet**: Install Coinbase Wallet (browser extension or mobile). Fund with ~0.1 ETH on Base Mainnet for gas (~$2-5 at current rates). For testing, use Base Sepolia faucet (e.g., https://faucet.base.org).
- **Token Specs**:
  - Name: 4EX
  - Symbol: $4EX
  - Total/Circulating Supply: 100,000,000,000 (100B)
  - Decimals: 18 (standard for ERC-20)
- **Environment**: Node.js installed for local frontend updates. Your 4ex.ninja repo cloned locally.
- **Optional**: Coinbase Developer API key (https://portal.cdp.coinbase.com/) for OnchainKit integration (already in your frontend plan).

## Step 1: Set Up Wallet and Test Environment
1. **Install Coinbase Wallet**:
   - Download from https://www.coinbase.com/wallet or Chrome Web Store.
   - Create/import a wallet. Back up your seed phrase securely.
2. **Fund Wallet**:
   - Mainnet: Send ~0.1 ETH to your wallet address on Base (bridge via Coinbase Wallet or https://bridge.base.org if needed).
   - Testnet: Get test ETH from Base Sepolia faucet for practice runs.
3. **Switch to Base**:
   - In Coinbase Wallet, set network to Base Mainnet (or Base Sepolia for testing).
4. **Verify Farcaster**:
   - Log into Warpcast (https://warpcast.com). Post a few casts to build Neynar score (prevents bot restrictions). Check score via Neynar API if curious (optional).

## Step 2: Deploy Token with Clanker
1. **Choose Deployment Method**:
   - **Farcaster (Recommended)**: Fastest; leverages social virality.
   - **Web (clanker.world)**: Alternative if you prefer a UI.
2. **Via Farcaster**:
   - Open Warpcast. Create a cast:
     ```
     @clanker deploy 4EX $4EX 100000000000 total supply
     ```
   - Optionally attach a logo (JPEG/PNG, <1MB) for branding.
   - Post the cast. Clanker’s AI bot responds within minutes with:
     - Success: Link to clanker.world token page with contract address.
     - Clarification: If details are unclear, reply to Clanker’s questions.
     - Failure: If Neynar score is low or limit reached (1 token/day/account).
3. **Via Web (Alternative)**:
   - Visit https://clanker.world.
   - Connect Coinbase Wallet (Base network).
   - Fill out:
     - Token Name: 4EX
     - Symbol: $4EX
     - Total Supply: 100,000,000,000
     - Image: Upload logo (optional).
   - Click “Deploy”. Approve transaction in wallet (~$0.01-0.10 gas).
4. **Output**:
   - Clanker deploys an ERC-20 contract on Base.
   - Initial mint: Tokens sent to your wallet.
   - Uniswap V4 pool created with ~$30k starting market cap (adjustable).
   - Liquidity locked until ~2100 (Unix timestamp 4132317178) for trust.
5. **Record Contract Address**:
   - Find on clanker.world or Basescan.org (search your wallet address for recent transactions).
   - Example: `0xYourTokenAddress`.

## Step 3: Verify and Secure Token
1. **Verify on Basescan**:
   - Go to https://basescan.org.
   - Search your token address. Clanker auto-verifies contracts, but confirm details (name, symbol, supply).
2. **Check Liquidity**:
   - Visit Uniswap V4 (https://app.uniswap.org) on Base.
   - Search for $4EX/ETH or $4EX/USDC pair. Ensure pool exists and liquidity is locked.
3. **Optional Security**:
   - Renounce ownership (if fair launch) via Clanker’s interface or contract interaction.
   - Announce lock/renunciation on X/Farcaster for community trust.

## Step 4: Integrate with 4ex.ninja Frontend
1. **Update Token Address**:
   - In your Next.js repo, update `TOKEN_ADDRESS` in your token-gating component (e.g., `app/page.tsx`):
     ```tsx
     const TOKEN_ADDRESS = '0xYourTokenAddress'; // From Clanker
     ```
2. **Test Gating**:
   - Run `npm run dev` locally.
   - Connect Coinbase Wallet, mint test tokens (Sepolia), or use Mainnet tokens.
   - Verify gating works (e.g., requires ≥1 $4EX).
3. **Add Buy Button**:
   - Add a link to Uniswap V4 for users to buy $4EX:
     ```tsx
     <a href="https://app.uniswap.org/#/swap?outputCurrency=0xYourTokenAddress" target="_blank">
       Buy $4EX
     </a>
     ```
4. **Push to Vercel**:
   - Commit: `git add . && git commit -m "Add $4EX token gating" && git push`.
   - Vercel auto-deploys. Test live site.

## Step 5: Bootstrap Liquidity and Trading
1. **Crowdfund Liquidity (Optional)**:
   - Use Clanker’s crowdfund feature (if available) to pool ETH from community.
   - Allocate 10-20% of supply (10-20B $4EX) to Uniswap pool for stability.
2. **Manual Liquidity (If Needed)**:
   - Go to Uniswap V4, add $4EX/ETH pair.
   - Deposit tokens + ETH (e.g., 10B $4EX + 0.5 ETH).
   - Lock LP tokens via Clanker or third-party locker.
3. **Enable Trading**:
   - Uniswap pool auto-enables trading.
   - Promote on X/Farcaster: “$4EX live on Uniswap! Buy to access 4ex.ninja exclusive features.”

## Step 6: Marketing and Community Engagement
1. **Announce Launch**:
   - Post on X/Farcaster: “$4EX launched on Base! Powering 4ex.ninja’s token-gated platform. Buy on Uniswap: [link].”
   - Tag @clanker for visibility.
2. **Airdrop**:
   - Use Clanker’s airdrop tool to distribute 1-5% of supply (1-5B $4EX) to early users or Farcaster followers.
   - Example: 100M $4EX to first 1,000 wallet connectors on 4ex.ninja.
3. **Listings**:
   - Submit to CoinGecko/CoinMarketCap (free, needs contract details).
   - Add to Base Ecosystem page (https://base.org/ecosystem).
4. **Engage Community**:
   - Create a Farcaster channel (/4ex) or X Spaces for updates.
   - Share frontend features (e.g., gated analytics, forex tools from your prior bot work).

## Step 7: Monitor and Optimize
1. **Track Metrics**:
   - Use Basescan for token transfers/holders.
   - Dune Analytics (https://dune.com) for trading volume.
2. **Claim Fees**:
   - Clanker’s 1% swap fees split: 60% to Clanker, 40% to you (claimable via clanker.world post-upgrade, ETA post-11/29/2024).
3. **Prevent Snipers**:
   - Monitor Uniswap for bot activity. Clanker’s anti-bot features help.
4. **Update Frontend**:
   - Add real-time price via OnchainKit’s `useBalance` or Coinbase API:
     ```tsx
     const { data: price } = useBalance({ token: TOKEN_ADDRESS, chainId: base.id });
     ```

## Timeline
- **Day 1**: Wallet setup, Farcaster account, test deployment (Sepolia).
- **Day 2**: Mainnet launch via Clanker, liquidity setup.
- **Day 3**: Frontend integration, Vercel deploy, marketing push.
- **Ongoing**: Airdrops, listings, community engagement.

## Notes
- **Gas Costs**: ~$2-10 for deployment/liquidity (Base’s low fees).
- **Risks**: Bot snipers, low initial liquidity. Mitigate with locked LP and transparent communication.
- **Next Steps**: If you share your token contract (post-launch) or repo snippet, I can refine frontend code or add analytics.