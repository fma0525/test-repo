"use client";

interface Step {
  label: string;
  status: "done" | "loading" | "pending";
}

export default function GeneratingStatus({ steps }: { steps: Step[] }) {
  return (
    <div className="flex flex-col items-center gap-6 py-8">
      {/* Animated star */}
      <div className="text-6xl animate-pulse-glow">⭐</div>
      <h2 className="text-xl font-bold text-[var(--color-primary)]">
        故事正在誕生中...
      </h2>

      {/* Steps */}
      <div className="w-full max-w-xs space-y-3">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3">
            {step.status === "done" && (
              <span className="text-green-500 text-lg">✓</span>
            )}
            {step.status === "loading" && (
              <span className="text-lg animate-spin-slow">⏳</span>
            )}
            {step.status === "pending" && (
              <span className="text-gray-300 text-lg">○</span>
            )}
            <span
              className={
                step.status === "done"
                  ? "text-gray-500"
                  : step.status === "loading"
                  ? "text-[var(--color-primary)] font-semibold"
                  : "text-gray-300"
              }
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
