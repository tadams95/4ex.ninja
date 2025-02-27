import { NextResponse } from "next/server";
import { MongoClient } from "mongodb";

export async function GET(request) {
  // Authorization check - add your own auth logic here
  // This is a simplified example - in production add proper authentication
  const authHeader = request.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.DEBUG_API_KEY}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  
  let client;
  try {
    // Check MongoDB connection
    const uri = process.env.MONGO_CONNECTION_STRING;
    client = new MongoClient(uri, {
      connectTimeoutMS: 5000,
      socketTimeoutMS: 5000,
    });
    
    await client.connect();
    
    // Check database and collection
    const db = client.db("users");
    const collection = db.collection("subscribers");
    const count = await collection.countDocuments();
    
    // Test user without revealing sensitive data
    const testUserEmail = request.nextUrl.searchParams.get("email");
    let userCheck = { found: false };
    
    if (testUserEmail) {
      const user = await collection.findOne(
        { email: testUserEmail },
        { projection: { 
          _id: 1, 
          email: 1, 
          name: 1, 
          subscriptionStatus: 1, 
          passwordType: { $cond: [
            { $regexMatch: { input: "$password", regex: /^\$2[ab]\$/ } },
            "bcrypt",
            "plain"
          ]}
        }}
      );
      
      if (user) {
        userCheck = {
          found: true,
          email: user.email,
          name: user.name,
          subscriptionStatus: user.subscriptionStatus,
          passwordType: user.passwordType
        };
      }
    }
    
    // Create diagnostic info
    const diagnostics = {
      environment: process.env.NODE_ENV,
      mongoConnected: true,
      databaseStats: {
        usersCount: count,
      },
      nextAuthConfig: {
        nextAuthUrl: process.env.NEXTAUTH_URL,
        nextPublicUrl: process.env.NEXT_PUBLIC_URL,
        hasSecret: !!process.env.NEXTAUTH_SECRET,
      },
      userCheck,
      vercelRegion: process.env.VERCEL_REGION || 'unknown',
    };
    
    return NextResponse.json(diagnostics);
  } catch (error) {
    return NextResponse.json({
      error: error.message,
      mongoConnected: false,
      environment: process.env.NODE_ENV,
      nextAuthConfig: {
        nextAuthUrl: process.env.NEXTAUTH_URL,
        nextPublicUrl: process.env.NEXT_PUBLIC_URL,
        hasSecret: !!process.env.NEXTAUTH_SECRET,
      },
      vercelRegion: process.env.VERCEL_REGION || 'unknown',
    }, { status: 500 });
  } finally {
    if (client) {
      await client.close();
    }
  }
}
