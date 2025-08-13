import { TOKEN_CONFIG } from '@/lib/token';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const walletAddress = searchParams.get('address');

  if (!walletAddress) {
    return NextResponse.json({ error: 'Wallet address is required' }, { status: 400 });
  }

  // Validate wallet address format
  if (!/^0x[a-fA-F0-9]{40}$/.test(walletAddress)) {
    return NextResponse.json({ error: 'Invalid wallet address format' }, { status: 400 });
  }

  try {
    // ERC20 balanceOf function selector: 0x70a08231
    // Encode the wallet address (remove 0x prefix and pad to 32 bytes)
    const paddedAddress = walletAddress.slice(2).toLowerCase().padStart(64, '0');
    const data = `0x70a08231${paddedAddress}`;

    const rpcPayload = {
      jsonrpc: '2.0',
      method: 'eth_call',
      params: [
        {
          to: TOKEN_CONFIG.address,
          data: data,
        },
        'latest',
      ],
      id: 1,
    };

    // Try multiple RPC endpoints
    const rpcEndpoints = [
      'https://mainnet.base.org',
      'https://base.llamarpc.com',
      'https://1rpc.io/base',
      'https://base.blockpi.network/v1/rpc/public',
    ];

    let lastError: Error | null = null;

    for (const endpoint of rpcEndpoints) {
      try {
        console.log(`API: Trying RPC endpoint: ${endpoint}`);

        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(rpcPayload),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.error) {
          throw new Error(`RPC Error: ${result.error.message || result.error}`);
        }

        if (!result.result) {
          throw new Error('No result returned from RPC call');
        }

        // Convert hex result to string (we'll handle BigInt conversion client-side)
        const balanceHex = result.result;
        console.log(`API: Success with ${endpoint}: Balance = ${balanceHex}`);

        return NextResponse.json({
          success: true,
          balance: balanceHex,
          endpoint: endpoint,
          address: walletAddress,
          contract: TOKEN_CONFIG.address,
        });
      } catch (error) {
        console.warn(`API: RPC endpoint ${endpoint} failed:`, error);
        lastError = error as Error;
        continue;
      }
    }

    // If all endpoints failed
    console.error('API: All RPC endpoints failed', lastError);
    return NextResponse.json(
      {
        error: 'All RPC endpoints failed to fetch token balance',
        details: lastError?.message || 'Unknown error',
        endpoints: rpcEndpoints,
      },
      { status: 503 }
    );
  } catch (error) {
    console.error('API: Unexpected error:', error);
    return NextResponse.json(
      {
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
