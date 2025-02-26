import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";
import crypto from "crypto";
import nodemailer from "nodemailer";

export async function POST(request) {
  try {
    const { email } = await request.json();

    if (!email) {
      return NextResponse.json({ error: "Email is required" }, { status: 400 });
    }

    // Connect to database
    const uri = process.env.MONGO_CONNECTION_STRING;
    const client = new MongoClient(uri);
    await client.connect();
    const db = client.db("4ex_users");

    // Check if user exists
    const user = await db.collection("users").findOne({ email });

    // Even if user doesn't exist, we don't reveal that information
    if (!user) {
      // Log internally but don't tell the user
      console.log(`Password reset requested for non-existent email: ${email}`);

      // Return success anyway to prevent email enumeration
      return NextResponse.json({
        success: true,
        message:
          "If this account exists, we've sent password reset instructions",
      });
    }

    // Generate reset token and expiry
    const resetToken = crypto.randomBytes(32).toString("hex");
    const resetTokenExpiry = new Date(Date.now() + 3600000); // 1 hour

    // Hash token for storage (only store hashed version in DB)
    const hashedToken = crypto
      .createHash("sha256")
      .update(resetToken)
      .digest("hex");

    // Save token to user
    await db.collection("users").updateOne(
      { email },
      {
        $set: {
          resetPasswordToken: hashedToken,
          resetPasswordExpires: resetTokenExpiry,
        },
      }
    );

    // Create reset URL
    const resetUrl = `${process.env.NEXT_PUBLIC_APP_URL}/reset-password?token=${resetToken}&email=${email}`;

    // Configure email transport (for production, use a proper email service)
    const transporter = nodemailer.createTransport({
      host: process.env.EMAIL_SERVER_HOST,
      port: process.env.EMAIL_SERVER_PORT,
      auth: {
        user: process.env.EMAIL_SERVER_USER,
        pass: process.env.EMAIL_SERVER_PASSWORD,
      },
      secure: true,
    });

    // Setup email content
    const mailOptions = {
      from: process.env.EMAIL_FROM,
      to: email,
      subject: "4ex.ninja Password Reset",
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #333;">Reset Your Password</h2>
          <p>You requested a password reset for your 4ex.ninja account.</p>
          <p>Click the button below to reset your password. This link is valid for 1 hour.</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="${resetUrl}" style="background-color: #10b981; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a>
          </div>
          <p style="color: #666; font-size: 14px;">If you didn't request this, please ignore this email.</p>
          <p style="color: #666; font-size: 14px;">If the button doesn't work, copy and paste this URL into your browser: ${resetUrl}</p>
        </div>
      `,
    };

    // Send email
    await transporter.sendMail(mailOptions);

    await client.close();

    return NextResponse.json({
      success: true,
      message: "Password reset email sent",
    });
  } catch (error) {
    console.error("Error in forgot password:", error);
    return NextResponse.json(
      { error: "Failed to process request" },
      { status: 500 }
    );
  }
}
