import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";
import bcrypt from "bcryptjs";

export async function POST(request) {
  try {
    const { name, email, password } = await request.json();
    
    // Validate input
    if (!name || !email || !password) {
      return NextResponse.json(
        { error: "Missing required fields" },
        { status: 400 }
      );
    }
    
    // Connect to database
    const uri = "mongodb+srv://tyrelle:dcvsniTYFG9ojCgn@cluster0.6h6fdf2.mongodb.net/?retryWrites=true&w=majority";
    const client = new MongoClient(uri);
    await client.connect();
    const db = client.db("4ex_users"); // Changed to a dedicated users database
    
    // Check if user already exists
    const existingUser = await db.collection("users").findOne({ email });
    if (existingUser) {
      await client.close();
      return NextResponse.json(
        { error: "Email already registered" },
        { status: 409 }
      );
    }
    
    // Hash password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);
    
    // Create user
    const result = await db.collection("users").insertOne({
      name,
      email,
      password: hashedPassword,
      isSubscribed: false,
      createdAt: new Date(),
    });
    
    await client.close();
    
    return NextResponse.json({ 
      id: result.insertedId,
      success: true 
    });
  } catch (error) {
    console.error("Error creating user:", error);
    return NextResponse.json(
      { error: error.message || "Failed to create user" },
      { status: 500 }
    );
  }
}