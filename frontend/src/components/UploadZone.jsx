// frontend/src/components/UploadZone.jsx
import React, { useRef, useState, useCallback } from "react";

/**
 * UploadZone
 * Drag-and-drop + click-to-browse image uploader.
 *
 * Props:
 *   onFileSelect(file: File) — called when a valid file is chosen
 *   disabled: boolean        — disables interaction while submitting
 */
export default function UploadZone({ onFileSelect, disabled = false }) {
  const inputRef        = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  /* ── Validation ── */
  const ALLOWED_TYPES = ["image/jpeg", "image/jpg", "image/png"];
  const MAX_BYTES     = 10 * 1024 * 1024; // 10 MB

  function validate(file) {
    if (!ALLOWED_TYPES.includes(file.type))
      return "Only JPEG and PNG images are supported.";
    if (file.size > MAX_BYTES)
      return "Image must be smaller than 10 MB.";
    return null;
  }

  function handleFile(file) {
    if (!file || disabled) return;
    const err = validate(file);
    if (err) { onFileSelect(null, err); return; }
    onFileSelect(file, null);
  }

  /* ── Event handlers ── */
  const onInputChange = (e) => handleFile(e.target.files[0]);

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    if (!disabled) setDragOver(true);
  }, [disabled]);

  const onDragLeave = useCallback(() => setDragOver(false), []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  }, [disabled]);

  const openBrowser = () => {
    if (!disabled) inputRef.current?.click();
  };

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Upload leaf image"
      onClick={openBrowser}
      onKeyDown={(e) => e.key === "Enter" && openBrowser()}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      className={`
        relative flex flex-col items-center justify-center
        border-[1.5px] border-dashed rounded-sm
        py-14 px-6 text-center
        transition-all duration-200 select-none
        ${disabled
          ? "opacity-50 cursor-not-allowed border-[#A2AC82]"
          : "cursor-pointer hover:border-[#0C3C01] hover:bg-[#0C3C01]/[0.03]"
        }
        ${dragOver
          ? "border-[#0C3C01] bg-[#0C3C01]/[0.05] scale-[1.005]"
          : "border-[#5B6D49]/40 bg-[#F1F2ED]"
        }
      `}
    >
      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/jpg,image/png"
        className="sr-only"
        onChange={onInputChange}
        disabled={disabled}
        aria-hidden="true"
      />

      {/* Upload icon */}
      <div className="w-12 h-12 rounded-full border border-[#5B6D49]/40 flex items-center justify-center mb-4">
        <svg
          className="w-5 h-5 stroke-[#5B6D49]"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
          />
        </svg>
      </div>

      <p className="text-[15px] font-medium text-[#2E2D1D] mb-1.5">
        {dragOver ? "Release to upload" : "Drop your leaf image here"}
      </p>
      <p className="text-[13px] text-[#5B6D49] font-light">
        or <span className="underline underline-offset-2">click to browse</span>
        &nbsp;— JPG, PNG up to 10 MB
      </p>
    </div>
  );
}