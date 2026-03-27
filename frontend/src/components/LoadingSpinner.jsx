// frontend/src/components/LoadingSpinner.jsx
import React from "react";

/**
 * LoadingSpinner
 * A small CSS-only animated ring used inside the submit button and
 * optionally as a full-page overlay while the model runs inference.
 *
 * Props:
 *   size  — "sm" | "md" | "lg"  (default "sm")
 *   color — any Tailwind border color class (default "border-[#F1F2ED]")
 */
export default function LoadingSpinner({
  size = "sm",
  color = "border-[#F1F2ED]",
}) {
  const sizeMap = {
    sm: "w-4 h-4 border-2",
    md: "w-7 h-7 border-2",
    lg: "w-10 h-10 border-[3px]",
  };

  return (
    <span
      role="status"
      aria-label="Loading"
      className={`
        inline-block rounded-full
        ${sizeMap[size]}
        ${color}
        border-t-transparent
        animate-spin
        flex-shrink-0
      `}
    />
  );
}