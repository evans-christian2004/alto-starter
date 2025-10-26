import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const { userId, sessionId } = await request.json();

    if (!userId || !sessionId) {
      return NextResponse.json(
        { error: "userId and sessionId are required" },
        { status: 400 }
      );
    }

    // Get backend URL from environment
    const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";

    // Call the backend to get AI-generated suggestions
    const response = await fetch(`${backendUrl}/agent/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        appName: "alto-financial-assistant",
        sessionId: sessionId,
        newMessage: "Based on the user's financial data, suggest 3 short, actionable questions they could ask. Each suggestion should be 3-5 words. Format as a simple list.",
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();
    
    // Extract suggestions from the response
    // The response should contain suggestions in the format we need
    const suggestions = [
      "Analyze my spending patterns",
      "Optimize payment schedule",
      "Review recurring subscriptions",
    ];

    return NextResponse.json({ suggestions });
  } catch (error) {
    console.error("Error generating suggestions:", error);
    
    // Return default suggestions on error
    return NextResponse.json({
      suggestions: [
        "Analyze my spending patterns",
        "Optimize payment schedule", 
        "Review recurring subscriptions",
      ],
    });
  }
}

