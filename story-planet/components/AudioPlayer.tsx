"use client";

import { useRef, useState, useEffect, useCallback } from "react";

interface AudioPlayerProps {
  audioUrl: string;
  duration: number;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function AudioPlayer({ audioUrl, duration }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(duration);

  const togglePlay = useCallback(async () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      try {
        await audio.play();
      } catch {
        // Audio play failed (no src or user interaction required)
      }
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  }, []);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onDurationChange = () => {
      if (audio.duration && isFinite(audio.duration)) {
        setTotalDuration(audio.duration);
      }
    };
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("durationchange", onDurationChange);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("durationchange", onDurationChange);
      audio.removeEventListener("ended", onEnded);
    };
  }, []);

  const hasAudio = !!audioUrl;

  return (
    <div className="w-full">
      {hasAudio && <audio ref={audioRef} src={audioUrl} preload="metadata" />}
      {!hasAudio && <audio ref={audioRef} preload="none" />}

      {/* Progress bar */}
      <div className="mb-3">
        <input
          type="range"
          min={0}
          max={totalDuration}
          step={0.1}
          value={currentTime}
          onChange={handleSeek}
          className="progress-bar"
          disabled={!hasAudio}
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(totalDuration)}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-6">
        <button
          onClick={togglePlay}
          disabled={!hasAudio}
          className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl transition-transform hover:scale-110 active:scale-95 disabled:opacity-40"
          style={{
            background: "linear-gradient(135deg, #6C5CE7, #A29BFE)",
          }}
          aria-label={isPlaying ? "暫停" : "播放"}
        >
          {isPlaying ? "⏸" : "▶"}
        </button>
      </div>

      {!hasAudio && (
        <p className="text-center text-xs text-gray-400 mt-3">
          Mock 模式 — 語音功能需設定 API Key
        </p>
      )}
    </div>
  );
}
