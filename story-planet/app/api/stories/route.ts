import { NextResponse } from "next/server";
import { getMockStories, isMockMode } from "@/lib/mock-data";

export async function GET() {
  if (isMockMode()) {
    return NextResponse.json({ stories: getMockStories() });
  }

  // TODO: Replace with Supabase query when API keys are configured
  // const { data, error } = await supabase
  //   .from('stories')
  //   .select('*')
  //   .order('created_at', { ascending: false });

  return NextResponse.json({ stories: getMockStories() });
}
