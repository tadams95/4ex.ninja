import { MongoClient, ObjectId } from 'mongodb';
import { getServerSession } from 'next-auth/next';
import { NextResponse } from 'next/server';
import { authOptions } from '../auth/[...nextauth]/auth-options';

export async function GET(request) {
  try {
    // Get current session to verify user
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'You must be logged in to view your profile' },
        { status: 401 }
      );
    }

    const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);

    try {
      await client.connect();
      const db = client.db('users');
      const usersCollection = db.collection('subscribers');

      // Find user by ID
      const user = await usersCollection.findOne({
        _id: new ObjectId(session.user.id),
      });

      if (!user) {
        return NextResponse.json({ error: 'User not found' }, { status: 404 });
      }

      // Return user profile data (excluding sensitive information)
      const profileData = {
        id: user._id.toString(),
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
