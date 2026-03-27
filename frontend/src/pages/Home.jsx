// frontend/src/pages/Home.jsx
import React, { useState, useCallback } from "react";
import UploadZone from "../components/UploadZone";
import ResultCard from "../components/ResultCard";
import LoadingSpinner from "../components/LoadingSpinner";
import { detectDisease } from "../api/detect";

/**
 * Home
 * Orchestrates the full upload → analyse → result flow.
 * All application state lives here and is passed down as props.
 */
export default function Home() {
  const [file, setFile]       = useState(null);    // selected File object
  const [preview, setPreview] = useState(null);    // object URL for <img>
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);    // API response
  const [error, setError]     = useState(null);    // user-facing error string

  /* ── Handle file selection from UploadZone ── */
  const handleFileSelect = useCallback((selectedFile, validationError) => {
    if (validationError) {
      setError(validationError);
      return;
    }
    // Revoke previous object URL to avoid memory leaks
    if (preview) URL.revokeObjectURL(preview);

    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError(null);
  }, [preview]);

  /* ── Clear everything and start over ── */
  const handleReset = useCallback(() => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
  }, [preview]);

  /* ── Submit image to backend ── */
  const handleSubmit = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await detectDisease(file);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [file]);

  return (
    <>
      {/* ── HERO ── */}
      <section className="relative bg-[#0C3C01] hero-texture px-10 md:px-20 pt-20 pb-16 overflow-hidden">
        <p className="text-[11px] tracking-[2.5px] uppercase text-[#A2AC82] font-medium mb-5">
          AI-powered plant health
        </p>
        <h1
          style={{ fontFamily: "Playfair Display, serif" }}
          className="text-[#F1F2ED] text-5xl md:text-6xl lg:text-7xl font-bold leading-[1.05] max-w-2xl mb-6"
        >
          Diagnose your crops{" "}
          <em className="italic text-[#A2AC82]">instantly.</em>
        </h1>
        <p className="text-[#F1F2ED]/60 text-base font-light max-w-md leading-relaxed mb-8">
          Upload a photo of any leaf and get a disease diagnosis, symptoms,
          and cure recommendations in seconds — powered by machine learning.
        </p>
        <a
          href="#upload"
          className="inline-flex items-center gap-2 bg-[#2E2D1D] hover:bg-[#4a4535] text-[#F1F2ED] text-xs uppercase tracking-[2px] font-medium px-6 py-3.5 rounded-sm transition-colors"
        >
          Start Scanning →
        </a>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how" className="bg-white border-b border-[#5B6D49]/10 px-10 md:px-20 py-14">
        <div className="max-w-3xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-10">
          {[
            { step: "01", title: "Upload", body: "Take a clear photo of the affected leaf and upload it as a JPG or PNG." },
            { step: "02", title: "Analyse", body: "Our MobileNetV2 model classifies the image against 38 plant disease classes." },
            { step: "03", title: "Treat", body: "Receive the disease name, confidence score, symptoms, and cure recommendations." },
          ].map(({ step, title, body }) => (
            <div key={step}>
              <p className="text-[11px] tracking-[2px] uppercase text-[#A2AC82] font-medium mb-3">
                Step {step}
              </p>
              <h3
                style={{ fontFamily: "Playfair Display, serif" }}
                className="text-[#0C3C01] text-xl font-bold mb-2"
              >
                {title}
              </h3>
              <p className="text-sm text-[#5B6D49] font-light leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── UPLOAD + RESULT ── */}
      <section id="upload" className="max-w-2xl mx-auto px-6 py-16 space-y-6">

        {/* Upload card */}
        <div className="bg-white border border-[#5B6D49]/15 rounded-sm p-10">
          <p className="text-[11px] tracking-[2px] uppercase text-[#5B6D49] font-medium mb-3">
            Step 01
          </p>
          <h2
            style={{ fontFamily: "Playfair Display, serif" }}
            className="text-[#0C3C01] text-2xl font-bold mb-1"
          >
            Upload a leaf image
          </h2>
          <p className="text-sm text-[#5B6D49] font-light leading-relaxed mb-8">
            Best results with clear, well-lit close-ups of the affected leaf
            against a plain background.
          </p>

          {/* Error banner */}
          {error && (
            <div className="mb-6 px-5 py-4 bg-red-50 border border-red-100 border-l-4 border-l-red-400 rounded-sm text-sm text-red-700 leading-relaxed">
              {error}
            </div>
          )}

          {/* Drop zone or preview */}
          {!preview ? (
            <UploadZone onFileSelect={handleFileSelect} disabled={loading} />
          ) : (
            <div className="relative mb-6 rounded-sm overflow-hidden border border-[#5B6D49]/20">
              <img
                src={preview}
                alt="Leaf preview"
                className="w-full max-h-72 object-cover"
              />
              {/* Overlay badges */}
              <span className="absolute top-3 left-3 bg-[#0C3C01] text-[#F1F2ED] text-[10px] uppercase tracking-[1.5px] px-3 py-1.5 rounded-sm">
                Ready
              </span>
              <button
                onClick={handleReset}
                disabled={loading}
                className="absolute top-3 right-3 bg-[#F1F2ED]/90 hover:bg-[#F1F2ED] text-[#2E2D1D] text-xs font-medium px-3 py-1.5 rounded-sm backdrop-blur-sm transition-colors disabled:opacity-50"
              >
                Change image
              </button>
            </div>
          )}

          {/* File name pill */}
          {file && (
            <p className="text-[12px] text-[#5B6D49] font-light mb-5 truncate">
              📎 {file.name} &nbsp;·&nbsp; {(file.size / 1024).toFixed(0)} KB
            </p>
          )}

          {/* Submit button */}
          <button
            onClick={handleSubmit}
            disabled={!file || loading}
            className="
              w-full flex items-center justify-center gap-3
              bg-[#0C3C01] hover:bg-[#0e4a01] active:scale-[0.99]
              disabled:bg-[#5B6D49] disabled:cursor-not-allowed disabled:opacity-70
              text-[#F1F2ED] text-[13px] uppercase tracking-[2px] font-medium
              py-4 rounded-sm
              transition-all duration-200
            "
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" />
                Analysing leaf…
              </>
            ) : (
              "Analyse Image →"
            )}
          </button>
        </div>

        {/* Result card — only shown after a successful response */}
        {result && <ResultCard result={result} />}

        {/* Scan another button after result */}
        {result && (
          <div className="text-center">
            <button
              onClick={handleReset}
              className="text-sm text-[#5B6D49] hover:text-[#0C3C01] underline underline-offset-4 font-light transition-colors"
            >
              ← Scan another leaf
            </button>
          </div>
        )}
      </section>
    </>
  );
}