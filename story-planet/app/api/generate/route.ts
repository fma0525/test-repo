import { NextRequest, NextResponse } from "next/server";
import { addMockStory, isMockMode } from "@/lib/mock-data";
import { GenerateRequest, ArtStyle, ART_STYLE_INFO } from "@/lib/types";

export async function POST(request: NextRequest) {
  const body = (await request.json()) as GenerateRequest;
  const { keywords, style } = body;

  if (!keywords || keywords.length === 0) {
    return NextResponse.json(
      { error: "至少需要一個關鍵字" },
      { status: 400 }
    );
  }

  if (isMockMode()) {
    // Simulate AI generation delay (1.5 seconds)
    await new Promise((resolve) => setTimeout(resolve, 1500));
    const story = addMockStory(keywords, style || "adventure");
    return NextResponse.json({ story });
  }

  // === Real AI Pipeline (when API keys are configured) ===
  try {
    // Step 1: Generate story text with Claude
    const storyData = await generateStoryText(keywords, style);

    // Step 2: Generate cover image + voice in parallel
    // TODO: artStyle should come from user account settings
    const artStyle: ArtStyle = "koreanGouache";
    const [coverUrl, audioUrl] = await Promise.all([
      generateCoverImage(storyData.cover_prompt, artStyle),
      generateVoice(storyData.full_text),
    ]);

    // Step 3: Save to database (TODO: Supabase)
    const story = {
      id: `story-${Date.now()}`,
      title: storyData.title,
      keywords,
      style,
      full_text: storyData.full_text,
      cover_image_url: coverUrl,
      audio_url: audioUrl,
      duration: 180, // TODO: get actual duration from TTS
      created_at: new Date().toISOString(),
    };

    return NextResponse.json({ story });
  } catch (err: unknown) {
    console.error("Generation error:", err);
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json(
      { error: `生成失敗：${message}` },
      { status: 500 }
    );
  }
}

// === AI Service Functions ===

async function generateStoryText(
  keywords: string[],
  style: string
): Promise<{
  title: string;
  full_text: string;
  cover_prompt: string;
}> {
  const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;
  if (!ANTHROPIC_API_KEY) throw new Error("ANTHROPIC_API_KEY not configured");

  const styleGuide: Record<string, string> = {
    goodnight: "晚安溫柔風：語氣輕柔，適合睡前，結尾導向安靜",
    adventure: "冒險精彩風：情節緊湊，有挑戰和驚喜",
    funny: "趣味歡笑風：搞笑誇張，充滿擬聲詞",
  };

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 2000,
      messages: [
        {
          role: "user",
          content: `你是兒童有聲書作家，為 3-6 歲孩子創作故事。

根據關鍵字「${keywords.join("、")}」，以「${styleGuide[style] || styleGuide.adventure}」風格創作故事。

要求：
1. 300-600 字，2-4 分鐘朗讀時間
2. 2-3 個角色，簡單句型
3. 正向結局
4. 禁止暴力、恐怖內容

請以 JSON 格式回覆（不要 markdown code block，直接輸出 JSON）：
{
  "title": "故事標題",
  "full_text": "完整故事文字（段落間用\\n\\n分隔）",
  "cover_prompt": "English image generation prompt describing a scene with all characters, children's book cartoon style, bright colors, cute characters"
}`,
        },
      ],
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Claude API error: ${errorText}`);
  }

  const result = await response.json();
  const text = result.content[0].text;

  // Parse JSON from response
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error("Failed to parse Claude response as JSON");

  return JSON.parse(jsonMatch[0]);
}

async function generateCoverImage(
  prompt: string,
  artStyle: ArtStyle = "softCartoon"
): Promise<string> {
  const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
  if (!OPENAI_API_KEY) throw new Error("OPENAI_API_KEY not configured");

  const stylePrompt = ART_STYLE_INFO[artStyle].prompt;

  const response = await fetch(
    "https://api.openai.com/v1/images/generations",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "dall-e-3",
        prompt: `${stylePrompt}. Scene: ${prompt}`,
        n: 1,
        size: "1024x1024",
        quality: "standard",
      }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`DALL-E API error: ${errorText}`);
  }

  const result = await response.json();
  return result.data[0].url;
}

async function generateVoice(text: string): Promise<string> {
  const ELEVENLABS_API_KEY = process.env.ELEVENLABS_API_KEY;
  if (!ELEVENLABS_API_KEY) {
    // Fallback: return empty if no TTS key
    console.warn("ELEVENLABS_API_KEY not configured, skipping voice generation");
    return "";
  }

  // Use a default Chinese-capable voice
  const voiceId = "21m00Tcm4TlvDq8ikWAM"; // Rachel - replace with Chinese voice

  const response = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY,
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_multilingual_v2",
        voice_settings: {
          stability: 0.75,
          similarity_boost: 0.75,
        },
      }),
    }
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`ElevenLabs API error: ${errorText}`);
  }

  // For MVP: return a data URL from the audio buffer
  // In production: upload to Supabase Storage and return URL
  const audioBuffer = await response.arrayBuffer();
  const base64 = Buffer.from(audioBuffer).toString("base64");
  return `data:audio/mpeg;base64,${base64}`;
}
