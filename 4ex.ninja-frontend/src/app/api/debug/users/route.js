import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";

// IMPORTANT: Only enable this in development!
const isDevelopment = process.env.NODE_ENV === "development";

export async function GET(request) {
  // Only allow in development mode
  if (!isDevelopment) {
    return NextResponse.json({ error: "Not available in production" }, { status: 403 });
  }

  const client = new MongoClient(process.env.MONGO_CONNECTION_STRING);

  try {
    await client.connect();
    const db = client.db("users");
    const users = await db.collection("subscribers")
      .find({}, { projection: { password: 0 } }) // Exclude passwords
      .limit(10)
      .toArray();

    return NextResponse.json({ users });
  } catch (error) {
    console.error("Debug endpoint error:", error);
    return NextResponse.json({ error: "Error fetching data" }, { status: 500 });
  } finally {
    await client.close();
  }
}
