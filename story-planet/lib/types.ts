export type StoryStyle = "goodnight" | "adventure" | "funny";

export interface Story {
  id: string;
  title: string;
  keywords: string[];
  style: StoryStyle;
  artStyle?: ArtStyle;
  full_text: string;
  cover_image_url: string;
  audio_url: string;
  duration: number; // seconds
  created_at: string; // ISO date string
}

export interface GenerateRequest {
  keywords: string[];
  style: StoryStyle;
}

export interface GenerateResponse {
  story: Story;
}

export const STYLE_INFO: Record<
  StoryStyle,
  { label: string; emoji: string; description: string }
> = {
  goodnight: {
    label: "晚安溫柔風",
    emoji: "🌙",
    description: "輕輕柔柔，適合睡前聽",
  },
  adventure: {
    label: "冒險精彩風",
    emoji: "⚡",
    description: "刺激有趣，充滿驚喜！",
  },
  funny: {
    label: "趣味歡笑風",
    emoji: "😄",
    description: "哈哈大笑，開心一整天",
  },
};

// === 畫風系統 ===

export type ArtStyle = "softCartoon" | "watercolor" | "crayon" | "koreanGouache";

export const ART_STYLE_INFO: Record<
  ArtStyle,
  { label: string; emoji: string; description: string; prompt: string }
> = {
  softCartoon: {
    label: "柔和卡通風",
    emoji: "🧸",
    description: "圓潤線條、明亮色彩，可愛又溫暖",
    prompt:
      "Soft cartoon children's book illustration style, rounded shapes, bright cheerful colors, cute characters with simple outlines, friendly and warm atmosphere",
  },
  watercolor: {
    label: "水彩繪本風",
    emoji: "🎨",
    description: "柔美手繪感，適合溫馨故事",
    prompt:
      "Watercolor children's book illustration, soft washes of color, gentle hand-painted feel, delicate brushstrokes, warm and dreamy atmosphere",
  },
  crayon: {
    label: "蠟筆塗鴉風",
    emoji: "🖍️",
    description: "童趣十足，像孩子自己畫的",
    prompt:
      "Crayon drawing style children's illustration, childlike and playful, textured crayon strokes, bold simple shapes, colorful and joyful",
  },
  koreanGouache: {
    label: "韓系水彩手繪風",
    emoji: "🌿",
    description: "溫柔細膩的自然繪本，像走進秘密花園",
    prompt:
      "Soft watercolor and gouache children's book illustration in the style of Korean picture books. Warm, muted pastel color palette with earthy tones — soft greens, warm yellows, dusty pinks, and gentle oranges. Delicate and detailed nature scenes with tiny cute anthropomorphic animals (field mice, ladybugs, sparrows, frogs). Whimsical miniature world perspective, as if viewing a secret garden from a small creature's eye level. Lush botanical details — flowers, leaves, grasses rendered with fine brushwork. Cozy, gentle atmosphere with soft natural lighting. Slightly textured paper feel. No harsh outlines, blending soft edges. Storybook charm with a sense of seasonal beauty and warmth.",
  },
};

export const INSPIRATION_TAGS = [
  { label: "動物", emoji: "🐻" },
  { label: "太空", emoji: "🚀" },
  { label: "精靈", emoji: "🧚" },
  { label: "海洋", emoji: "🌊" },
  { label: "恐龍", emoji: "🦕" },
  { label: "森林", emoji: "🌲" },
  { label: "生日", emoji: "🎂" },
  { label: "友誼", emoji: "💕" },
];
