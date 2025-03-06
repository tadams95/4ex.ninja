import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";

// Use proper error handling for the connection string
const uri = process.env.MONGO_CONNECTION_STRING;

// Create MongoDB client with proper options
let client = null;
let cachedClient = null;
let cachedDb = null;

async function connectToDatabase() {
  // Check for cached connection first
  if (cachedClient && cachedDb) {
    return { client: cachedClient, db: cachedDb };
  }

  // Validate connection string
  if (!uri) {
    // Instead of throwing an error, return a helpful response
    return { error: "MongoDB connection string is not defined" };
  }

  try {
    // Initialize client only if not already initialized
    if (!client) {
      client = new MongoClient(uri, {
        connectTimeoutMS: 5000,
        socketTimeoutMS: 45000,
        maxPoolSize: 10,
        retryWrites: true,
      });
    }

    await client.connect();
    const db = client.db("crossovers");

    cachedClient = client;
    cachedDb = db;

    return { client, db };
  } catch (error) {
    console.error("MongoDB connection error:", error);
    return { error: `Unable to connect to MongoDB: ${error.message}` };
  }
}

export async function GET(request) {
  try {
    // Extract query parameters
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get("limit") || "20");

    // Connect to MongoDB - handle connection errors
    const connection = await connectToDatabase();
    if (connection.error) {
      console.error("Connection error:", connection.error);
      return NextResponse.json(
        {
          crossovers: [],
          error: connection.error,
          message: "Database connection issue",
          isEmpty: true,
        },
        { status: 500 }
      );
    }

    const { db } = connection;
    const collection = db.collection("ma_crossovers");

    // Check if collection exists and has documents
    const count = await collection.countDocuments({});
    console.log(`Found ${count} documents in ma_crossovers collection`);

    if (count === 0) {
      return NextResponse.json({
        crossovers: [],
        message: "No crossovers available in database",
        isEmpty: true,
      });
    }

    // Fetch latest crossovers
    const crossovers = await collection
      .find({})
      .sort({ time: -1 })
      .limit(limit)
      .toArray();

    // Map MongoDB document to frontend format based on the actual structure
    const formattedCrossovers = crossovers.map((crossover) => ({
      _id: crossover._id.toString(),
      pair: crossover.pair,
      crossoverType: crossover.signal === "Buy" ? "BULLISH" : "BEARISH",
      timeframe: crossover.timeframe,
      fastMA: crossover.fast_ma,
      slowMA: crossover.slow_ma,
      price: crossover.close?.toFixed(5),
      timestamp: crossover.time,
    }));

    return NextResponse.json({ crossovers: formattedCrossovers });
  } catch (error) {
    console.error("Database Error:", error);
    return NextResponse.json(
      {
        crossovers: [],
        error: error.message,
        message: "Failed to fetch crossovers from database",
        isEmpty: true,
      },
      { status: 500 }
    );
  }
}
