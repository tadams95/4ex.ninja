import { MongoClient } from 'mongodb';

const MONGODB_URI = process.env.MONGO_CONNECTION_STRING;
const MONGODB_DB = '4ex_users'; // Updated to the correct database name

if (!MONGODB_URI) {
  throw new Error('Please define the MONGODB_URI environment variable');
}

let cachedClient = null;
let cachedDb = null;

export async function connectToDatabase() {
  // If we have a cached connection, use it
  if (cachedClient && cachedDb) {
    return { client: cachedClient, db: cachedDb };
  }

  // Create a new connection
  const client = await MongoClient.connect(MONGODB_URI);

  const db = client.db(MONGODB_DB);

  // Cache the connection
  cachedClient = client;
  cachedDb = db;

  return { client, db };
}

export async function getSignals() {
  const { client, db } = await connectToDatabase();
  try {
    const signals = db.collection("signals");
    const result = await signals
      .find({})
      .sort({ timestamp: -1 })
      .limit(10)
      .toArray();
    return result;
  } finally {
    await client.close();
  }
}
