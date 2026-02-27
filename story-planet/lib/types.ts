export type StoryStyle = "goodnight" | "adventure" | "funny";

export interface Story {
  id: string;
  title: string;
  keywords: string[];
  style: StoryStyle;
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
