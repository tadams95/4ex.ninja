import { NextResponse } from "next/server";
import { MongoClient, ObjectId } from "mongodb";
import { getServerSession } from "next-auth/next";
import bcrypt from "bcryptjs";
import { authOptions } from "../auth/[...nextauth]/auth-options";

export async function POST(request) {
  try {
    // Get current session to verify user
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: "You must be logged in to update your profile" },
        { status: 401 }
      );
    }
    
    const { name, email, currentPassword, newPassword } = await request.json();
    
    // Validate input
    if (!name || !email) {
      return NextResponse.json(
        { error: "Name and email are required" },
        { status: 400 }
      );
    }
    
    // Check if attempting to change password
    const isPasswordChange = currentPassword && newPassword;
    
    const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);
    
    try {
      await client.connect();
      const db = client.db("users");
      const usersCollection = db.collection("subscribers");
      
      // Check if email exists for another user
      if (email !== session.user.email) {
        const existingUser = await usersCollection.findOne({ 
          email,
          _id: { $ne: new ObjectId(session.user.id) }
        });
        
        if (existingUser) {
          return NextResponse.json(
            { error: "Email is already in use" },
            { status: 400 }
          );
        }
      }
      
      // Get the current user
      const user = await usersCollection.findOne({ 
        _id: new ObjectId(session.user.id) 
      });
      
      if (!user) {
        return NextResponse.json(
          { error: "User not found" },
          { status: 404 }
        );
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
          return NextResponse.json(
            { error: "Current password is incorrect" },
            { status: 400 }
          );
        }
        
        // Hash the new password
        const hashedPassword = await bcrypt.hash(newPassword, 10);
        
        // Update user with new password
        await usersCollection.updateOne(
          { _id: new ObjectId(session.user.id) },
          { 
            $set: { 
              name,
              email,
              password: hashedPassword,
              updatedAt: new Date()
            } 
          }
        );
      } else {
        // Update user without changing password
        await usersCollection.updateOne(
          { _id: new ObjectId(session.user.id) },
          { 
            $set: { 
              name,
              email,
              updatedAt: new Date()
            } 
          }
        );
      }
      
      return NextResponse.json(
        { message: "Profile updated successfully" },
        { status: 200 }
      );
    } finally {
      await client.close();
    }
  } catch (error) {
    console.error("Profile update error:", error);
    return NextResponse.json(
      { error: "An unexpected error occurred" },
      { status: 500 }
    );
  }
}
