import { MongoClient } from "mongodb";

const uri = process.env.MONGODB_URI;
const client = new MongoClient(uri);

export async function getSignals() {
  try {
    await client.connect();
    const database = client.db("forex_signals");
    const signals = database.collection("signals");
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
