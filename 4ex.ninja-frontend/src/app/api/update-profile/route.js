import bcrypt from 'bcryptjs';
import { MongoClient } from 'mongodb';
import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    // Get wallet address from request headers or body
    const { walletAddress, name, email, currentPassword, newPassword } = await request.json();

    if (!walletAddress) {
      return NextResponse.json({ error: 'Wallet address is required' }, { status: 401 });
    }

    // Validate input
    if (!name || !email) {
      return NextResponse.json({ error: 'Name and email are required' }, { status: 400 });
    }

    // Check if attempting to change password
    const isPasswordChange = currentPassword && newPassword;

    const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);

    try {
      await client.connect();
      const db = client.db('users');
      const usersCollection = db.collection('subscribers');

      // Check if email exists for another user
      if (email !== user.email) {
        const existingUser = await usersCollection.findOne({
          email,
          walletAddress: { $ne: walletAddress },
        });

        if (existingUser) {
          return NextResponse.json({ error: 'Email is already in use' }, { status: 400 });
        }
      }

      // Get the current user
      const user = await usersCollection.findOne({
        walletAddress: walletAddress,
      });

      if (!user) {
        return NextResponse.json({ error: 'User not found' }, { status: 404 });
      }

      // If updating password, verify current password
      if (isPasswordChange) {
        let passwordValid;

        // Check if password is stored as hash
        if (user.password.startsWith('$2a$') || user.password.startsWith('$2b$')) {
          passwordValid = await bcrypt.compare(currentPassword, user.password);
        } else {
          // Plain text comparison (legacy support)
          passwordValid = user.password === currentPassword;
        }

        if (!passwordValid) {
          return NextResponse.json({ error: 'Current password is incorrect' }, { status: 400 });
        }

        // Hash the new password
        const hashedPassword = await bcrypt.hash(newPassword, 10);

        // Update user with new password
        await usersCollection.updateOne(
          { walletAddress: walletAddress },
          {
            $set: {
              name,
              email,
              password: hashedPassword,
              updatedAt: new Date(),
            },
          }
        );
      } else {
        // Update user without changing password
        await usersCollection.updateOne(
          { walletAddress: walletAddress },
          {
            $set: {
              name,
              email,
              updatedAt: new Date(),
            },
          }
        );
      }

      return NextResponse.json({ message: 'Profile updated successfully' }, { status: 200 });
    } finally {
      await client.close();
    }
  } catch (error) {
    console.error('Profile update error:', error);
    return NextResponse.json({ error: 'An unexpected error occurred' }, { status: 500 });
  }
}
