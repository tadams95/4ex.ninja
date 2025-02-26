import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";

// Use proper error handling for the connection string
const uri = process.env.MONGO_CONNECTION_STRING;

// Create MongoDB client with proper options
const client = new MongoClient(uri, {
  // Add these options to help with connection issues
  connectTimeoutMS: 5000,
  socketTimeoutMS: 45000,
  maxPoolSize: 10,
  retryWrites: true,
});

// Connection cache
let cachedClient = null;
let cachedDb = null;

async function connectToDatabase() {
  if (cachedClient && cachedDb) {
    return { client: cachedClient, db: cachedDb };
  }

  if (!uri) {
    throw new Error("MongoDB connection string is not defined");
  }

  try {
    await client.connect();
    const db = client.db("signals");

    cachedClient = client;
    cachedDb = db;

    return { client, db };
  } catch (error) {
    console.error("MongoDB connection error:", error);
    throw new Error(`Unable to connect to MongoDB: ${error.message}`);
  }
}

export async function GET(request) {
  try {
    // Extract query parameters
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get("limit") || "20");

    // Connect to MongoDB
    const { db } = await connectToDatabase();
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
      { error: "Failed to fetch signals from database" },
      { status: 500 }
    );
  }
}
