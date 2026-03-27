// frontend/src/components/ResultCard.jsx
import React, { useEffect, useState } from "react";

/**
 * ResultCard
 * Displays the prediction response from the backend.
 *
 * Props:
 *   result: {
 *     disease: string,
 *     confidence: number,   // 0.0 – 1.0
 *     symptoms: string,
 *     cure: string
 *   }
 */
export default function ResultCard({ result }) {
  const { disease, confidence, symptoms, cure } = result;

  // Animate the confidence bar from 0 → actual value on mount
  const [barWidth, setBarWidth] = useState(0);
  const confPct = Math.round(confidence * 100);
  const isHealthy = disease.toLowerCase().includes("healthy");

  useEffect(() => {
    // Small delay so the CSS transition is visible
    const timer = setTimeout(() => setBarWidth(confPct), 80);
    return () => clearTimeout(timer);
  }, [confPct]);

  /* ── Confidence colour ── */
  function barColor(pct) {
    if (pct >= 80) return "bg-[#0C3C01]";
    if (pct >= 60) return "bg-[#5B6D49]";
    return "bg-amber-500";
  }

  return (
    <div className="slide-up border border-[#5B6D49]/15 rounded-sm overflow-hidden">

      {/* ── Header ── */}
      <div className="bg-[#0C3C01] px-10 py-7 flex items-start justify-between gap-6">
        <div>
          <p className="text-[10px] tracking-[2.5px] uppercase text-[#A2AC82] mb-2 font-medium">
            Diagnosis result
          </p>
          <h2
            style={{ fontFamily: "Playfair Display, serif" }}
            className="text-[#F1F2ED] text-2xl font-bold leading-snug"
          >
            {disease}
          </h2>
        </div>

        {/* Confidence badge */}
        <div className="bg-[#2E2D1D] rounded-sm px-5 py-3 text-center flex-shrink-0">
          <span
            style={{ fontFamily: "Playfair Display, serif" }}
            className="block text-3xl font-bold text-[#F1F2ED] leading-none"
          >
            {confPct}%
          </span>
          <span className="text-[10px] tracking-[1.5px] uppercase text-[#A2AC82] mt-1 block">
            Confidence
          </span>
        </div>
      </div>

      {/* ── Confidence bar ── */}
      <div className="h-[3px] bg-[#0C3C01]/10">
        <div
          className={`h-full conf-bar ${barColor(confPct)}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>

      {/* ── Healthy plant banner ── */}
      {isHealthy && (
        <div className="bg-[#F1F2ED] border-b border-[#5B6D49]/10 px-10 py-4 flex items-center gap-3">
          <span className="text-[#0C3C01] text-lg">✓</span>
          <p className="text-sm text-[#5B6D49] font-light">
            No disease detected. Your plant appears to be in good health.
          </p>
        </div>
      )}

      {/* ── Info rows ── */}
      <div>
        <InfoRow label="Symptoms" value={symptoms} />
        <InfoRow label="Treatment" value={cure} isLast />
      </div>
    </div>
  );
}

/* ── InfoRow sub-component ── */
function InfoRow({ label, value, isLast = false }) {
  return (
    <div
      className={`
        px-10 py-7 grid grid-cols-[140px_1fr] gap-6 items-start
        ${isLast ? "" : "border-b border-[#5B6D49]/10"}
      `}
    >
      <span className="text-[10px] tracking-[2px] uppercase text-[#5B6D49] font-medium pt-0.5">
        {label}
      </span>
      <span className="text-[15px] text-[#2E2D1D] font-light leading-relaxed">
        {value}
      </span>
    </div>
  );
}