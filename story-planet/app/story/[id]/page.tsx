"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AudioPlayer from "@/components/AudioPlayer";
import { Story, STYLE_INFO } from "@/lib/types";

const STYLE_GRADIENTS: Record<string, string> = {
  goodnight: "from-indigo-400 via-purple-400 to-blue-500",
  adventure: "from-orange-400 via-red-400 to-yellow-500",
  funny: "from-green-400 via-teal-400 to-cyan-500",
};

export default function StoryPlayerPage() {
  const params = useParams();
  const id = params.id as string;
  const [story, setStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/stories/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("找不到故事");
        return res.json();
      })
      .then((data) => {
        setStory(data.story);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className="max-w-lg mx-auto px-4 flex items-center justify-center min-h-dvh">
        <div className="text-4xl animate-pulse-glow">🌟</div>
      </div>
    );
  }

  if (error || !story) {
    return (
      <div className="max-w-lg mx-auto px-4 py-8 text-center">
        <div className="text-6xl mb-4">😢</div>
        <p className="text-gray-500 mb-4">{error || "找不到故事"}</p>
        <Link href="/" className="text-[var(--color-primary)] font-medium">
          ← 返回書架
        </Link>
      </div>
    );
  }

  const styleInfo = STYLE_INFO[story.style];
  const gradient =
    STYLE_GRADIENTS[story.style] || STYLE_GRADIENTS.adventure;

  // Split full_text into paragraphs for display
  const paragraphs = story.full_text
    .split("\n")
    .map((p) => p.trim())
    .filter(Boolean);

  return (
    <div className="max-w-lg mx-auto px-4 pb-8">
      {/* Header */}
      <header className="flex items-center justify-between py-4">
        <Link
          href="/"
          className="text-[var(--color-primary)] font-medium text-sm"
        >
          ← 返回書架
        </Link>
        <span className="text-xs text-gray-400">
          {styleInfo.emoji} {styleInfo.label}
        </span>
      </header>

      {/* Cover image */}
      <div className="mb-6 rounded-2xl overflow-hidden shadow-lg">
        {story.cover_image_url ? (
          <img
            src={story.cover_image_url}
            alt={story.title}
            className="w-full aspect-[4/3] object-cover"
          />
        ) : (
          <div
            className={`cover-placeholder aspect-[4/3] bg-gradient-to-br ${gradient} flex-col gap-2`}
          >
            <span className="text-7xl">{styleInfo.emoji}</span>
            <span className="text-white/80 text-sm font-medium">
              封面圖將在連接 AI 後生成
            </span>
          </div>
        )}
      </div>

      {/* Title */}
      <h1 className="text-xl font-bold mb-1">{story.title}</h1>
      <p className="text-xs text-gray-400 mb-6">
        關鍵字：{story.keywords.join("、")}
      </p>

      {/* Audio player */}
      <div className="mb-6">
        <AudioPlayer audioUrl={story.audio_url} duration={story.duration} />
      </div>

      {/* Story text */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 mb-3">故事內容</h2>
        <div className="story-text bg-white rounded-2xl p-5 shadow-sm space-y-4 max-h-[60vh] overflow-y-auto">
          {paragraphs.map((p, i) => {
            // Detect dialogue lines (start with 「 or contain direct speech)
            const isDialogue = p.startsWith("「") || p.startsWith("『");
            return (
              <p
                key={i}
                className={`text-[15px] leading-relaxed ${
                  isDialogue
                    ? "text-[var(--color-primary)] font-medium pl-2 border-l-3 border-[var(--color-primary-light)]"
                    : "text-gray-700"
                }`}
              >
                {p}
              </p>
            );
          })}
        </div>
      </section>
    </div>
  );
}
