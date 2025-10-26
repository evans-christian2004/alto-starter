import { NextResponse } from "next/server";
import fs from "fs/promises";
import path from "path";

export async function GET() {
  try {
    // Path to the calendar modifications file in the Python backend
    const modificationsPath = path.join(
      process.cwd(),
      "..",
      "app",
      "data",
      "calendar_modifications.json"
    );

    try {
      const data = await fs.readFile(modificationsPath, "utf-8");
      const modifications = JSON.parse(data);
      return NextResponse.json(modifications);
    } catch (error) {
      // File doesn't exist or is empty - return empty modifications
      return NextResponse.json({
        modifications: [],
        last_updated: null,
      });
    }
  } catch (error) {
    console.error("Error reading calendar modifications:", error);
    return NextResponse.json(
      { error: "Failed to read calendar modifications" },
      { status: 500 }
    );
  }
}

