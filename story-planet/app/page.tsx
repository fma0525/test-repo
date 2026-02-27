"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import StoryCard from "@/components/StoryCard";
import { Story } from "@/lib/types";

export default function BookshelfPage() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/stories")
      .then((res) => res.json())
      .then((data) => {
        setStories(data.stories || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-lg mx-auto px-4 pb-24">
      {/* Header */}
      <header className="flex items-center justify-between py-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-primary)]">
            故事星球
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">StoryPlanet</p>
        </div>
        <Link
          href="/create"
          className="btn-primary text-sm px-5 py-2.5"
        >
          ✨ 新故事
        </Link>
      </header>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-4xl animate-pulse-glow">🌟</div>
        </div>
      ) : stories.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="text-6xl mb-4">🪐</div>
          <h2 className="text-lg font-bold text-gray-600 mb-2">
            還沒有故事
          </h2>
          <p className="text-sm text-gray-400 mb-6">
            來創作你的第一個有聲故事吧！
          </p>
          <Link href="/create" className="btn-primary">
            ✨ 開始創作
          </Link>
        </div>
      ) : (
        <>
          <section className="mb-6">
            <h2 className="text-sm font-semibold text-gray-500 mb-3">
              我的故事（{stories.length} 個）
            </h2>
            <div className="grid grid-cols-2 gap-4">
              {stories.map((story) => (
                <StoryCard key={story.id} story={story} />
              ))}
              {/* New story card */}
              <Link href="/create">
                <div className="story-card flex flex-col items-center justify-center aspect-square bg-gray-50 text-gray-400 hover:text-[var(--color-primary)] hover:bg-purple-50">
                  <span className="text-4xl mb-2">+</span>
                  <span className="text-sm font-medium">新故事</span>
                </div>
              </Link>
            </div>
          </section>
        </>
      )}

      {/* Mock mode banner */}
      <div className="fixed bottom-0 left-0 right-0 bg-amber-50 border-t border-amber-200 px-4 py-2 text-center text-xs text-amber-700">
        🧪 Mock 模式 — 使用內建假資料，設定 API Key 後可切換為 AI 生成
      </div>
    </div>
  );
}
