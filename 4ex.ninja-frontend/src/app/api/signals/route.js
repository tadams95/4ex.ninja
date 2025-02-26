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
    const db = client.db("signals");

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
          signals: [],
          error: connection.error,
          message: "Database connection issue",
          isEmpty: true,
        },
        { status: 500 }
      );
    }

    const { db } = connection;
    const collection = db.collection("trades");

    // Check if collection exists and has documents
    const count = await collection.countDocuments({});
    console.log(`Found ${count} documents in collection`);

    if (count === 0) {
      return NextResponse.json({
        signals: [],
        message: "No signals available in database",
        isEmpty: true,
      });
    }

    // Fetch latest signals
    const signals = await collection
      .find({})
      .sort({ time: -1 })
      .limit(limit)
      .toArray();

    // Map MongoDB document to frontend format
    const formattedSignals = signals.map((signal) => ({
      _id: signal._id.toString(),
      pair: signal.instrument,
      type: signal.signal === 1 ? "BUY" : "SELL",
      timeframe: signal.timeframe,
      entry: signal.close?.toFixed(5),
      stopLoss: signal.stop_loss?.toFixed(5),
      takeProfit: signal.take_profit?.toFixed(5),
      slPips: signal.sl_pips?.toFixed(1),
      tpPips: signal.tp_pips?.toFixed(1),
      riskRewardRatio: signal.risk_reward_ratio?.toFixed(2),
      timestamp: signal.time,
    }));

    return NextResponse.json({ signals: formattedSignals });
  } catch (error) {
    console.error("Database Error:", error);
    return NextResponse.json(
      {
        signals: [],
        error: error.message,
        message: "Failed to fetch signals from database",
        isEmpty: true,
      },
      { status: 500 }
    );
  }
}
