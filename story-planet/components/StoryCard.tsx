"use client";

import Link from "next/link";
import { Story, STYLE_INFO } from "@/lib/types";

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const STYLE_GRADIENTS: Record<string, string> = {
  goodnight: "from-indigo-400 via-purple-400 to-blue-500",
  adventure: "from-orange-400 via-red-400 to-yellow-500",
  funny: "from-green-400 via-teal-400 to-cyan-500",
};

export default function StoryCard({ story }: { story: Story }) {
  const styleInfo = STYLE_INFO[story.style];
  const gradient = STYLE_GRADIENTS[story.style] || STYLE_GRADIENTS.adventure;

  return (
    <Link href={`/story/${story.id}`}>
      <div className="story-card">
        {story.cover_image_url ? (
          <img
            src={story.cover_image_url}
            alt={story.title}
            className="w-full aspect-square object-cover"
          />
        ) : (
          <div
            className={`cover-placeholder aspect-square bg-gradient-to-br ${gradient}`}
          >
            <span className="text-5xl">{styleInfo.emoji}</span>
          </div>
        )}
        <div className="p-3">
          <h3 className="font-bold text-sm leading-tight line-clamp-2">
            {story.title}
          </h3>
          <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
            <span>{styleInfo.emoji} {styleInfo.label}</span>
            <span>{formatDuration(story.duration)}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
