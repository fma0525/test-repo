"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import GeneratingStatus from "@/components/GeneratingStatus";
import {
  StoryStyle,
  STYLE_INFO,
  INSPIRATION_TAGS,
  GenerateRequest,
} from "@/lib/types";

type GeneratingStep = "idle" | "text" | "image" | "voice" | "done";

export default function CreateStoryPage() {
  const router = useRouter();
  const [selectedStyle, setSelectedStyle] = useState<StoryStyle>("adventure");
  const [keywordInput, setKeywordInput] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [generating, setGenerating] = useState<GeneratingStep>("idle");
  const [error, setError] = useState<string | null>(null);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const allKeywords = [
    ...selectedTags,
    ...keywordInput
      .split(/[,，、\s]+/)
      .map((s) => s.trim())
      .filter(Boolean),
  ];

  const canSubmit = allKeywords.length > 0 && generating === "idle";

  const handleGenerate = async () => {
    if (!canSubmit) return;
    setError(null);

    // Simulate step progression
    setGenerating("text");

    try {
      const body: GenerateRequest = {
        keywords: allKeywords,
        style: selectedStyle,
      };

      // Start generation
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error("生成失敗，請稍後再試");
      }

      const data = await res.json();
      setGenerating("done");

      // Navigate to story after a brief delay
      setTimeout(() => {
        router.push(`/story/${data.story.id}`);
      }, 800);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "生成失敗";
      setError(message);
      setGenerating("idle");
    }
  };

  const steps = [
    {
      label: "📝 故事文字",
      status:
        generating === "text"
          ? ("loading" as const)
          : generating === "idle"
          ? ("pending" as const)
          : ("done" as const),
    },
    {
      label: "🎨 繪製封面",
      status:
        generating === "image"
          ? ("loading" as const)
          : generating === "text" || generating === "idle"
          ? ("pending" as const)
          : ("done" as const),
    },
    {
      label: "🔊 語音合成",
      status:
        generating === "voice"
          ? ("loading" as const)
          : generating === "done"
          ? ("done" as const)
          : ("pending" as const),
    },
  ];

  if (generating !== "idle") {
    return (
      <div className="max-w-lg mx-auto px-4 py-8">
        <GeneratingStatus steps={steps} />
        {generating === "done" && (
          <p className="text-center text-green-600 font-semibold mt-4">
            完成！正在跳轉...
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto px-4 pb-8">
      {/* Header */}
      <header className="flex items-center py-6">
        <Link
          href="/"
          className="text-[var(--color-primary)] font-medium text-sm"
        >
          ← 返回
        </Link>
      </header>

      <h1 className="text-xl font-bold mb-6">建立新故事</h1>

      {/* Style selection */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold text-gray-500 mb-3">
          今天想聽什麼樣的故事？
        </h2>
        <div className="space-y-3">
          {(Object.entries(STYLE_INFO) as [StoryStyle, typeof STYLE_INFO[StoryStyle]][]).map(
            ([key, info]) => (
              <button
                key={key}
                className={`style-btn w-full ${
                  selectedStyle === key ? "selected" : ""
                }`}
                onClick={() => setSelectedStyle(key)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{info.emoji}</span>
                  <div>
                    <div className="font-bold text-sm">{info.label}</div>
                    <div className="text-xs text-gray-400">
                      {info.description}
                    </div>
                  </div>
                  {selectedStyle === key && (
                    <span className="ml-auto text-[var(--color-primary)]">
                      ✓
                    </span>
                  )}
                </div>
              </button>
            )
          )}
        </div>
      </section>

      {/* Inspiration tags */}
      <section className="mb-6">
        <h2 className="text-sm font-semibold text-gray-500 mb-3">
          選擇靈感
        </h2>
        <div className="flex flex-wrap gap-2">
          {INSPIRATION_TAGS.map((tag) => (
            <button
              key={tag.label}
              className={`tag ${
                selectedTags.includes(tag.label) ? "selected" : ""
              }`}
              onClick={() => toggleTag(tag.label)}
            >
              {tag.emoji} {tag.label}
            </button>
          ))}
        </div>
      </section>

      {/* Keyword input */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-gray-500 mb-3">
          或輸入自己的關鍵字
        </h2>
        <input
          type="text"
          value={keywordInput}
          onChange={(e) => setKeywordInput(e.target.value)}
          placeholder="例如：恐龍、太空、友誼"
          className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-[var(--color-primary)] focus:outline-none text-sm"
        />
      </section>

      {/* Selected keywords preview */}
      {allKeywords.length > 0 && (
        <div className="mb-6 text-sm text-gray-500">
          已選關鍵字：
          <span className="font-semibold text-[var(--color-primary)]">
            {allKeywords.join("、")}
          </span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        className="btn-primary w-full text-center"
        disabled={!canSubmit}
        onClick={handleGenerate}
      >
        ✨ 開始創作！
      </button>
    </div>
  );
}
