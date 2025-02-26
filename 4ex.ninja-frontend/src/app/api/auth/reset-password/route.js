import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";
import bcrypt from "bcryptjs";
import crypto from "crypto";

export async function POST(request) {
  try {
    const { token, email, password } = await request.json();

    if (!token || !email || !password) {
      return NextResponse.json(
        { error: "Missing required fields" },
        { status: 400 }
      );
    }

    // Connect to database
    const uri = process.env.MONGO_CONNECTION_STRING;
    const client = new MongoClient(uri);
    await client.connect();
    const db = client.db("4ex_users");

    // Hash the token to compare with the stored hash
    const hashedToken = crypto.createHash("sha256").update(token).digest("hex");

    // Find user with the reset token
    const user = await db.collection("users").findOne({
      email,
      resetPasswordToken: hashedToken,
      resetPasswordExpires: { $gt: new Date() },
    });

    if (!user) {
      await client.close();
      return NextResponse.json(
        { error: "Invalid or expired reset token" },
        { status: 400 }
      );
    }

    // Hash new password
    const salt = await bcrypt.genSalt(10);
    const hashedPassword = await bcrypt.hash(password, salt);

    // Update user with new password and remove reset token fields
    await db.collection("users").updateOne(
      { email },
      {
        $set: { password: hashedPassword },
        $unset: { resetPasswordToken: "", resetPasswordExpires: "" },
      }
    );

    await client.close();

    return NextResponse.json({
      success: true,
      message: "Password has been reset",
    });
  } catch (error) {
    console.error("Error in reset password:", error);
    return NextResponse.json(
      { error: "Failed to reset password" },
      { status: 500 }
    );
  }
}
