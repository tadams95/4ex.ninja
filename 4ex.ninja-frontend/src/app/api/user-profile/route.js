import { MongoClient } from 'mongodb';
import { NextResponse } from 'next/server';

export async function GET(request) {
  try {
    // Get wallet address from query parameters
    const { searchParams } = new URL(request.url);
    const walletAddress = searchParams.get('walletAddress');

    if (!walletAddress) {
      return NextResponse.json({ error: 'Wallet address is required' }, { status: 401 });
    }

    const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);

    try {
      await client.connect();
      const db = client.db('users');
      const usersCollection = db.collection('subscribers');

      // Find user by wallet address
      const user = await usersCollection.findOne({
        walletAddress: walletAddress,
      });

      if (!user) {
        return NextResponse.json({ error: 'User not found' }, { status: 404 });
      }

      // Return user profile data (excluding sensitive information)
      const profileData = {
        id: user._id.toString(),
        walletAddress: user.walletAddress,
        name: user.name || '',
        email: user.email || '',
        createdAt: user.createdAt,
        updatedAt: user.updatedAt,
      };

      return NextResponse.json(profileData);
    } finally {
      await client.close();
    }
  } catch (error) {
    console.error('Error fetching user profile:', error);
    return NextResponse.json({ error: 'Failed to fetch profile data' }, { status: 500 });
  }
}
