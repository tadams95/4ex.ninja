# Onchain Migration Plan: From Stripe to Token-Gated Access

## Executive Summary

This document outlines a comprehensive migration strategy to transition 4ex.ninja from a traditional Stripe-based subscription model to a modern onchain token-gating system using Coinbase's Onchain Kit. This migration will enable:

- **Decentralized Access Control**: Token-based feature gates instead of centralized subscription management
- **Enhanced User Experience**: Web3-native authentication and payment flows
- **Reduced Infrastructure Costs**: Elimination of Stripe fees and webhook complexity
- **Future-Proof Architecture**: Foundation for DeFi integration and token utility expansion

---

## Current State Analysis

### Existing Stripe Infrastructure

**Payment Flow:**
- Stripe Checkout Sessions (`/api/create-checkout-session`)
- Webhook handling for subscription events (`/api/webhook/stripe`)
- Subscription status management (`/api/subscription-status`)
- Subscription cancellation (`/api/cancel-subscription`)

**User Management:**
- MongoDB-based user storage with Stripe customer IDs
- NextAuth.js authentication with subscription checks
- Protected routes with `requireSubscription` parameter
- Subscription verification API (`/api/verify-subscription`)

**Feature Gating:**
- Database field `isSubscribed` boolean checks
- Trial period management (30-day default)
- Plan-based access (Basic/Premium tiers)

### Current Dependencies to Replace

```typescript
// Current Stripe dependencies
- stripe: "^14.x.x"
- Stripe webhooks infrastructure
- MongoDB subscription status fields
- Stripe-specific API routes (8 endpoints)
- Custom checkout flow integration
```

---

## Target Onchain Architecture

### Core Components

**1. Coinbase Onchain Kit Integration**
```typescript
// New onchain dependencies
- @coinbase/onchainkit: "^0.x.x"
- wagmi: "^2.x.x"
- viem: "^2.x.x"
- @rainbow-me/rainbowkit: "^2.x.x" (optional wallet connector)
```

**2. Token-Gating Strategy**
- **Access Tokens**: ERC-20 tokens for feature access
- **NFT Memberships**: ERC-721 for premium tiers
- **Multi-Chain Support**: Base (primary), Ethereum mainnet
- **Token Utility**: Staking, governance, and feature unlocks

**3. Smart Contract Architecture**
```solidity
// Core contracts needed
- AccessToken.sol (ERC-20)
- MembershipNFT.sol (ERC-721)
- FeatureGate.sol (Access control)
- TokenVesting.sol (For team/early users)
```

---

## Migration Phases

### Phase 1: Foundation Setup (Week 1-2)
**Goal**: Establish onchain infrastructure without disrupting current users

#### 1.1 Smart Contract Deployment
```solidity
// AccessToken.sol - ERC-20 for feature access
contract ForexNinjaToken {
    string public name = "4ex.ninja Access Token";
    string public symbol = "FOREX";
    uint8 public decimals = 18;
    
    // Minimum tokens required for premium access
    uint256 public constant PREMIUM_THRESHOLD = 1000 * 10**18;
    
    // Features unlocked by token holdings
    mapping(address => uint256) public lastFeatureAccess;
}

// MembershipNFT.sol - ERC-721 for premium tiers
contract ForexNinjaMembership {
    enum MembershipTier { BASIC, PREMIUM, LIFETIME }
    
    struct Membership {
        MembershipTier tier;
        uint256 expiryDate;
        bool active;
    }
    
    mapping(uint256 => Membership) public memberships;
}
```

#### 1.2 Onchain Kit Setup
```typescript
// lib/onchain-config.ts
import { OnchainKitProvider } from '@coinbase/onchainkit';

export const onchainConfig = {
  apiKey: process.env.COINBASE_API_KEY,
  chain: base, // Base network as primary
  schemaId: '0x...', // Attestation schema for memberships
};

// components/providers/OnchainProvider.tsx
export function OnchainProvider({ children }: { children: React.ReactNode }) {
  return (
    <OnchainKitProvider
      apiKey={onchainConfig.apiKey}
      chain={onchainConfig.chain}
      schemaId={onchainConfig.schemaId}
    >
      <WagmiProvider config={wagmiConfig}>
        {children}
      </WagmiProvider>
    </OnchainKitProvider>
  );
}
```

#### 1.3 Parallel Authentication System
```typescript
// New authentication hooks alongside existing
// hooks/useOnchainAuth.ts
export function useOnchainAuth() {
  const { address, isConnected } = useAccount();
  const [tokenBalance, setTokenBalance] = useState<bigint>(0n);
  const [hasAccess, setHasAccess] = useState(false);
  
  // Check token balance for access
  useEffect(() => {
    if (address && isConnected) {
      checkTokenAccess(address);
    }
  }, [address, isConnected]);
  
  const checkTokenAccess = async (userAddress: string) => {
    // Implementation for checking ERC-20 balance
    const balance = await readContract({
      address: FOREX_TOKEN_ADDRESS,
      abi: forexTokenABI,
      functionName: 'balanceOf',
      args: [userAddress],
    });
    
    setTokenBalance(balance);
    setHasAccess(balance >= PREMIUM_THRESHOLD);
  };
  
  return { address, tokenBalance, hasAccess, isConnected };
}
```

### Phase 2: User Migration Infrastructure (Week 3-4)
**Goal**: Create seamless migration path for existing Stripe subscribers

#### 2.1 Migration API Endpoints
```typescript
// api/migrate/stripe-to-onchain/route.ts
export async function POST(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  
  // Check existing Stripe subscription
  const user = await getUserFromDB(session.user.email);
  if (!user.isSubscribed) {
    return NextResponse.json({ error: 'No active subscription' }, { status: 400 });
  }
  
  // Generate migration token claim
  const migrationCode = generateMigrationCode(user);
  
  return NextResponse.json({
    migrationCode,
    tokenAmount: calculateMigrationTokens(user),
    instructions: 'Connect wallet and claim your tokens',
  });
}

// api/claim-migration-tokens/route.ts
export async function POST(request: Request) {
  const { migrationCode, walletAddress } = await request.json();
  
  // Verify migration code
  const isValid = await verifyMigrationCode(migrationCode);
  if (!isValid) {
    return NextResponse.json({ error: 'Invalid migration code' }, { status: 400 });
  }
  
  // Mint tokens to user's wallet
  await mintMigrationTokens(walletAddress, migrationCode);
  
  // Update user record with wallet address
  await linkWalletToUser(migrationCode, walletAddress);
  
  return NextResponse.json({ success: true });
}
```

#### 2.2 Migration UI Components
```typescript
// components/migration/MigrationWizard.tsx
export function MigrationWizard() {
  const { isSubscribed } = useAuth();
  const { address, isConnected } = useAccount();
  const [migrationData, setMigrationData] = useState(null);
  
  const steps = [
    {
      title: 'Check Eligibility',
      component: <EligibilityCheck />,
      completed: isSubscribed,
    },
    {
      title: 'Connect Wallet',
      component: <WalletConnection />,
      completed: isConnected,
    },
    {
      title: 'Claim Tokens',
      component: <TokenClaim />,
      completed: migrationData?.claimed,
    },
  ];
  
  return (
    <div className="migration-wizard">
      <h2>Migrate to Onchain Access</h2>
      <div className="steps">
        {steps.map((step, index) => (
          <MigrationStep key={index} {...step} />
        ))}
      </div>
    </div>
  );
}
```

### Phase 3: Feature Migration (Week 5-6)
**Goal**: Replace Stripe-based feature gates with token-based access

#### 3.1 Enhanced Protected Route System
```typescript
// components/ProtectedRoute.tsx (Updated)
interface ProtectedRouteProps {
  requireSubscription?: boolean; // Legacy support
  requireTokens?: bigint; // New token-based access
  requireNFT?: boolean; // NFT membership access
  children: React.ReactNode;
}

export function ProtectedRoute({
  requireSubscription = false,
  requireTokens,
  requireNFT = false,
  children,
}: ProtectedRouteProps) {
  const { isAuthenticated } = useAuth(); // Legacy auth
  const { address, tokenBalance, hasAccess } = useOnchainAuth(); // New onchain auth
  const [accessGranted, setAccessGranted] = useState(false);
  
  useEffect(() => {
    // During migration period, check both systems
    const legacyAccess = isAuthenticated && requireSubscription;
    const tokenAccess = requireTokens ? tokenBalance >= requireTokens : hasAccess;
    const nftAccess = requireNFT ? checkNFTOwnership(address) : true;
    
    // Grant access if either legacy or onchain criteria are met
    setAccessGranted(legacyAccess || (tokenAccess && nftAccess));
  }, [isAuthenticated, tokenBalance, address]);
  
  if (!accessGranted) {
    return <AccessDenied />;
  }
  
  return children;
}
```

#### 3.2 Feature-Specific Token Gates
```typescript
// services/tokenGating.ts
export class TokenGatingService {
  // Premium trading features
  static async checkAdvancedCharts(address: string): Promise<boolean> {
    const balance = await this.getTokenBalance(address);
    return balance >= ADVANCED_CHARTS_THRESHOLD;
  }
  
  // API access limits
  static async getAPIRateLimit(address: string): Promise<number> {
    const balance = await this.getTokenBalance(address);
    
    if (balance >= PREMIUM_THRESHOLD) return 1000; // Premium: 1000 calls/hour
    if (balance >= BASIC_THRESHOLD) return 100;    // Basic: 100 calls/hour
    return 10; // Free: 10 calls/hour
  }
  
  // Real-time data access
  static async checkRealtimeAccess(address: string): Promise<boolean> {
    // Check for NFT membership or sufficient tokens
    const hasNFT = await this.checkMembershipNFT(address);
    const hasTokens = await this.getTokenBalance(address) >= REALTIME_THRESHOLD;
    
    return hasNFT || hasTokens;
  }
  
  private static async getTokenBalance(address: string): Promise<bigint> {
    return await readContract({
      address: FOREX_TOKEN_ADDRESS,
      abi: forexTokenABI,
      functionName: 'balanceOf',
      args: [address],
    });
  }
}
```

### Phase 4: Payment System Replacement (Week 7-8)
**Goal**: Replace Stripe checkout with onchain token purchase

#### 4.1 Token Purchase Interface
```typescript
// components/purchase/TokenPurchase.tsx
export function TokenPurchase() {
  const { address } = useAccount();
  const [purchaseAmount, setPurchaseAmount] = useState('1000');
  const [isLoading, setIsLoading] = useState(false);
  
  const handlePurchase = async () => {
    setIsLoading(true);
    
    try {
      // Use Coinbase Onchain Kit for purchase
      const transaction = await writeContract({
        address: FOREX_TOKEN_ADDRESS,
        abi: forexTokenABI,
        functionName: 'mint',
        args: [address, parseEther(purchaseAmount)],
        value: parseEther((Number(purchaseAmount) * TOKEN_PRICE).toString()),
      });
      
      await waitForTransaction({ hash: transaction.hash });
      
      // Update user access immediately
      await refreshTokenBalance();
      
    } catch (error) {
      console.error('Purchase failed:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="token-purchase">
      <h3>Purchase Access Tokens</h3>
      <TokenPriceCalculator 
        amount={purchaseAmount}
        onChange={setPurchaseAmount}
      />
      <PurchaseButton 
        onClick={handlePurchase}
        loading={isLoading}
        disabled={!address}
      />
    </div>
  );
}
```

#### 4.2 NFT Membership Minting
```typescript
// components/purchase/NFTMembership.tsx
export function NFTMembership() {
  const membershipTiers = [
    {
      name: 'Basic',
      price: parseEther('0.1'), // 0.1 ETH
      duration: 30, // 30 days
      features: ['Real-time signals', 'Basic charts'],
    },
    {
      name: 'Premium',
      price: parseEther('0.5'), // 0.5 ETH
      duration: 365, // 1 year
      features: ['All Basic features', 'Advanced analytics', 'API access'],
    },
    {
      name: 'Lifetime',
      price: parseEther('2.0'), // 2 ETH
      duration: 0, // No expiry
      features: ['All features', 'Governance rights', 'Exclusive content'],
    },
  ];
  
  const mintMembership = async (tier: MembershipTier) => {
    const transaction = await writeContract({
      address: MEMBERSHIP_NFT_ADDRESS,
      abi: membershipNFTABI,
      functionName: 'mintMembership',
      args: [address, tier.name, tier.duration],
      value: tier.price,
    });
    
    await waitForTransaction({ hash: transaction.hash });
  };
  
  return (
    <div className="nft-membership">
      <h3>NFT Membership</h3>
      <div className="membership-tiers">
        {membershipTiers.map((tier) => (
          <MembershipCard
            key={tier.name}
            tier={tier}
            onMint={() => mintMembership(tier)}
          />
        ))}
      </div>
    </div>
  );
}
```

### Phase 5: Legacy System Sunset (Week 9-10)
**Goal**: Complete migration and remove Stripe dependencies

#### 5.1 Final Migration Push
```typescript
// api/migration/finalize/route.ts
export async function POST() {
  // Send final migration emails to remaining Stripe users
  const stripeUsers = await getActiveStripeUsers();
  
  for (const user of stripeUsers) {
    await sendMigrationUrgencyEmail(user.email, {
      deadline: '2024-12-31',
      tokenBonus: '20%', // Extra tokens for early migration
      supportContact: 'migration@4ex.ninja',
    });
  }
  
  // Cancel all Stripe subscriptions
  await cancelAllStripeSubscriptions();
  
  // Archive Stripe data for compliance
  await archiveStripeData();
  
  return NextResponse.json({ success: true });
}
```

#### 5.2 Cleanup and Optimization
```typescript
// Remove Stripe dependencies
// package.json changes:
{
  "dependencies": {
    // Remove:
    // "stripe": "^14.x.x"
    
    // Add:
    "@coinbase/onchainkit": "^0.x.x",
    "wagmi": "^2.x.x",
    "viem": "^2.x.x"
  }
}

// Delete Stripe-specific files:
// - api/create-checkout-session/
// - api/webhook/stripe/
// - api/cancel-subscription/
// - utils/checkout-helpers.js
// - utils/get-stripe.js
```

---

## Technical Implementation Details

### Smart Contract Specifications

#### AccessToken.sol (ERC-20)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ForexNinjaToken is ERC20, Ownable {
    uint256 public constant PREMIUM_THRESHOLD = 1000 * 10**18;
    uint256 public constant BASIC_THRESHOLD = 100 * 10**18;
    
    // Feature gates
    mapping(address => uint256) public lastFeatureAccess;
    mapping(string => uint256) public featureThresholds;
    
    constructor() ERC20("4ex.ninja Access Token", "FOREX") {
        // Initialize feature thresholds
        featureThresholds["realtime"] = 500 * 10**18;
        featureThresholds["advanced_charts"] = 250 * 10**18;
        featureThresholds["api_access"] = 100 * 10**18;
    }
    
    function hasFeatureAccess(address user, string memory feature) 
        external view returns (bool) {
        return balanceOf(user) >= featureThresholds[feature];
    }
    
    function mint(address to, uint256 amount) external payable {
        require(msg.value >= amount / 1000, "Insufficient payment");
        _mint(to, amount);
    }
}
```

#### MembershipNFT.sol (ERC-721)
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract ForexNinjaMembership is ERC721, Ownable {
    enum MembershipTier { BASIC, PREMIUM, LIFETIME }
    
    struct Membership {
        MembershipTier tier;
        uint256 mintDate;
        uint256 expiryDate;
        bool active;
    }
    
    mapping(uint256 => Membership) public memberships;
    uint256 public nextTokenId = 1;
    
    // Pricing in wei
    uint256 public constant BASIC_PRICE = 0.1 ether;
    uint256 public constant PREMIUM_PRICE = 0.5 ether;
    uint256 public constant LIFETIME_PRICE = 2 ether;
    
    constructor() ERC721("4ex.ninja Membership", "FOREX-NFT") {}
    
    function mintMembership(
        address to,
        MembershipTier tier,
        uint256 duration
    ) external payable {
        uint256 price = tier == MembershipTier.BASIC ? BASIC_PRICE :
                       tier == MembershipTier.PREMIUM ? PREMIUM_PRICE :
                       LIFETIME_PRICE;
        
        require(msg.value >= price, "Insufficient payment");
        
        uint256 tokenId = nextTokenId++;
        _mint(to, tokenId);
        
        memberships[tokenId] = Membership({
            tier: tier,
            mintDate: block.timestamp,
            expiryDate: duration == 0 ? 0 : block.timestamp + (duration * 1 days),
            active: true
        });
    }
    
    function hasActiveMemebership(address user) external view returns (bool) {
        uint256 balance = balanceOf(user);
        for (uint256 i = 0; i < balance; i++) {
            uint256 tokenId = tokenOfOwnerByIndex(user, i);
            Membership memory membership = memberships[tokenId];
            
            if (membership.active && 
                (membership.expiryDate == 0 || membership.expiryDate > block.timestamp)) {
                return true;
            }
        }
        return false;
    }
}
```

### Database Schema Changes

#### User Model Updates
```typescript
// Old Stripe-based user model
interface UserStripe {
  _id: ObjectId;
  email: string;
  name: string;
  password: string;
  isSubscribed: boolean;
  subscriptionId?: string;
  customerStripeId?: string;
  subscriptionEnds?: Date;
  subscriptionStatus?: string;
}

// New onchain user model
interface UserOnchain {
  _id: ObjectId;
  email: string;
  name: string;
  password: string;
  
  // Onchain data
  walletAddress?: string;
  tokenBalance?: string; // Cached for performance
  nftMemberships?: Array<{
    tokenId: string;
    tier: 'BASIC' | 'PREMIUM' | 'LIFETIME';
    expiryDate?: Date;
    active: boolean;
  }>;
  
  // Migration data
  migratedFromStripe?: boolean;
  migrationDate?: Date;
  stripeMigrationCode?: string;
  
  // Legacy support (during transition)
  isSubscribed?: boolean; // Deprecated
  subscriptionEnds?: Date; // Deprecated
}
```

### API Route Transformations

#### Before: Stripe Subscription Check
```typescript
// api/subscription-status/route.ts (OLD)
export async function GET() {
  const session = await getServerSession(authOptions);
  const user = await getUserFromDB(session.user.id);
  
  return NextResponse.json({
    isSubscribed: user.isSubscribed,
    subscriptionStatus: user.subscriptionStatus,
    subscriptionEnds: user.subscriptionEnds,
  });
}
```

#### After: Onchain Access Check
```typescript
// api/access-status/route.ts (NEW)
export async function GET() {
  const session = await getServerSession(authOptions);
  const user = await getUserFromDB(session.user.id);
  
  let hasAccess = false;
  let accessLevel = 'free';
  
  if (user.walletAddress) {
    // Check onchain token balance
    const tokenBalance = await getTokenBalance(user.walletAddress);
    const hasNFT = await checkNFTMembership(user.walletAddress);
    
    if (hasNFT) {
      hasAccess = true;
      accessLevel = 'premium';
    } else if (tokenBalance >= PREMIUM_THRESHOLD) {
      hasAccess = true;
      accessLevel = 'premium';
    } else if (tokenBalance >= BASIC_THRESHOLD) {
      hasAccess = true;
      accessLevel = 'basic';
    }
  }
  
  // Legacy support during migration
  if (!hasAccess && user.isSubscribed) {
    hasAccess = true;
    accessLevel = 'legacy';
  }
  
  return NextResponse.json({
    hasAccess,
    accessLevel,
    tokenBalance: user.tokenBalance,
    walletAddress: user.walletAddress,
  });
}
```

---

## Migration Timeline

### Pre-Migration (2 weeks before)
- [ ] Deploy smart contracts to Base testnet
- [ ] Complete frontend integration testing
- [ ] Prepare migration communications
- [ ] Set up monitoring and analytics

### Week 1-2: Foundation
- [ ] Deploy production smart contracts
- [ ] Launch onchain authentication system
- [ ] Begin user education campaign
- [ ] Enable parallel access systems

### Week 3-4: User Migration
- [ ] Launch migration wizard
- [ ] Send migration invitation emails
- [ ] Provide migration support
- [ ] Monitor user adoption metrics

### Week 5-6: Feature Migration
- [ ] Update all protected routes
- [ ] Launch token purchase interface
- [ ] Deploy NFT membership system
- [ ] Migrate premium features

### Week 7-8: Payment Replacement
- [ ] Disable new Stripe subscriptions
- [ ] Launch token-based purchasing
- [ ] Implement staking rewards
- [ ] Add governance features

### Week 9-10: Legacy Sunset
- [ ] Final migration push
- [ ] Cancel remaining Stripe subscriptions
- [ ] Remove Stripe dependencies
- [ ] Archive legacy data

---

## Risk Mitigation

### Technical Risks

**Smart Contract Vulnerabilities**
- **Mitigation**: Comprehensive audits, formal verification, bug bounty program
- **Contingency**: Emergency pause functionality, upgrade mechanisms

**Network Congestion**
- **Mitigation**: Multi-chain deployment (Base + Ethereum), gas optimization
- **Contingency**: Dynamic gas pricing, Layer 2 fallbacks

**Wallet Integration Issues**
- **Mitigation**: Multiple wallet connector support, extensive testing
- **Contingency**: Email-based backup authentication during transition

### User Experience Risks

**Migration Complexity**
- **Mitigation**: Step-by-step wizard, video tutorials, live support
- **Contingency**: Extended parallel system operation, assisted migration

**Wallet Adoption Barriers**
- **Mitigation**: Embedded wallet solutions, educational content
- **Contingency**: Custodial wallet option for users

### Business Risks

**Revenue Disruption**
- **Mitigation**: Gradual transition, token pre-sales, NFT launch events
- **Contingency**: Extended Stripe operation, emergency rollback plan

**User Churn**
- **Mitigation**: Migration incentives, enhanced features, community building
- **Contingency**: Win-back campaigns, legacy access extension

---

## Success Metrics

### Technical KPIs
- [ ] 95%+ smart contract uptime
- [ ] <2 second transaction confirmation times
- [ ] Zero critical security incidents
- [ ] 99.9% wallet connection success rate

### User Adoption KPIs
- [ ] 80%+ user migration rate within 60 days
- [ ] 90%+ user satisfaction score
- [ ] <5% support ticket volume increase
- [ ] 50%+ reduction in authentication-related issues

### Business KPIs
- [ ] Revenue neutrality maintained during migration
- [ ] 25% reduction in payment processing costs
- [ ] 40% improvement in user acquisition cost
- [ ] 60% increase in user lifetime value

---

## Post-Migration Opportunities

### Enhanced Features
- **Staking Rewards**: Users earn tokens for platform engagement
- **Governance Participation**: Token holders vote on platform features
- **DeFi Integration**: Yield farming with platform tokens
- **Cross-Platform Utility**: Token use across partner platforms

### Community Building
- **DAO Formation**: Community-governed feature development
- **Trading Competitions**: Token-incentivized contests
- **Educational Content**: Learn-to-earn programs
- **Referral Systems**: Token rewards for user growth

### Revenue Diversification
- **NFT Marketplace**: Secondary market for memberships
- **Premium Analytics**: Advanced features for institutional users
- **API Monetization**: Token-based API access tiers
- **Consulting Services**: Professional trading advisory

---

## Conclusion

This migration from Stripe to Coinbase Onchain Kit represents a strategic transformation that will:

1. **Reduce Operational Costs**: Eliminate 2.9% Stripe fees and complex webhook infrastructure
2. **Enhance User Experience**: Provide seamless Web3-native authentication and payments
3. **Enable Innovation**: Foundation for DeFi features, governance, and community ownership
4. **Future-Proof Platform**: Position 4ex.ninja as a leader in onchain finance applications

The phased approach ensures minimal disruption while maximizing the benefits of decentralized access control. With proper execution, this migration will strengthen 4ex.ninja's market position and open new revenue opportunities in the rapidly growing Web3 ecosystem.

**Next Steps**: 
1. Stakeholder approval for migration plan
2. Smart contract development initiation
3. User communication strategy finalization
4. Technical team resource allocation

---

*This document should be reviewed and updated regularly throughout the migration process to reflect changing requirements and discovered optimizations.*
