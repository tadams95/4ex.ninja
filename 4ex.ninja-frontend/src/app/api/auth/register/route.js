import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";
import bcrypt from "bcryptjs";

const uri = process.env.MONGO_CONNECTION_STRING;

export async function POST(request) {
  try {
    const { name, email, password } = await request.json();

    // Input validation
    if (!email || !password || !name) {
      return NextResponse.json(
        { error: "Missing required fields" },
        { status: 400 }
      );
    }

    const client = new MongoClient(uri);

    try {
      await client.connect();
      const db = client.db("users");
      const usersCollection = db.collection("subscribers");

      // Check if user already exists
      const existingUser = await usersCollection.findOne({ email });
      if (existingUser) {
        return NextResponse.json(
          { error: "User already exists" },
          { status: 400 }
        );
      }

      // Hash the password for security
      const hashedPassword = await bcrypt.hash(password, 10);

      // Set subscription end date to 30 days from now (for free trial)
      const subscriptionEnds = new Date();
      subscriptionEnds.setDate(subscriptionEnds.getDate() + 30);

      // Create new user document
      const newUser = {
        name,
        email,
        password: hashedPassword,
        subscriptionStatus: "active", // Set to active by default for the free trial
        subscriptionEnds,
        createdAt: new Date(),
      };

      // Insert the new user
      const result = await usersCollection.insertOne(newUser);

      console.log("User registered successfully:", {
        id: result.insertedId,
        email: email,
      });

      return NextResponse.json(
        { message: "Registration successful" },
        { status: 201 }
      );
    } finally {
      await client.close();
    }
  } catch (error) {
    console.error("Registration error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}