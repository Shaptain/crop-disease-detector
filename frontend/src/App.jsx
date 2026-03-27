// frontend/src/App.jsx
import React from "react";
import Home from "./pages/Home";

/**
 * App
 * Root shell: persistent nav + footer wrapping the Home page.
 */
export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Navigation ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0C3C01] flex items-center justify-between px-10 h-16">
        {/* Brand */}
        <span
          style={{ fontFamily: "Playfair Display, serif" }}
          className="text-[#F1F2ED] text-xl tracking-tight"
        >
          Crop<span className="italic text-[#A2AC82]">Scan</span>
        </span>

        {/* Nav links */}
        <div className="hidden md:flex items-center gap-8 text-[#F1F2ED] text-sm font-light tracking-wide">
          <a href="#upload" className="hover:text-[#A2AC82] transition-colors">Diagnose</a>
          <a href="#how" className="hover:text-[#A2AC82] transition-colors">How it works</a>
        </div>

        {/* CTA */}
        <a
          href="#upload"
          className="bg-[#2E2D1D] hover:bg-[#4a4535] text-[#F1F2ED] text-xs font-medium uppercase tracking-[2px] px-5 py-2.5 rounded-sm transition-colors"
        >
          Get Started
        </a>
      </nav>

      {/* ── Page content ── */}
      <main className="flex-1 pt-16">
        <Home />
      </main>

      {/* ── Footer ── */}
      <footer className="bg-[#2E2D1D] text-[#F1F2ED]/40 text-xs text-center py-6 tracking-wide">
        © {new Date().getFullYear()} CropScan · AI Plant Disease Detection ·
        For agricultural guidance only
      </footer>
    </div>
  );
}