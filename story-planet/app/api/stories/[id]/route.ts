import { NextResponse } from "next/server";
import { getMockStory, isMockMode } from "@/lib/mock-data";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  if (isMockMode()) {
    const story = getMockStory(id);
    if (!story) {
      return NextResponse.json({ error: "Story not found" }, { status: 404 });
    }
    return NextResponse.json({ story });
  }

  // TODO: Replace with Supabase query
  const story = getMockStory(id);
  if (!story) {
    return NextResponse.json({ error: "Story not found" }, { status: 404 });
  }
  return NextResponse.json({ story });
}
