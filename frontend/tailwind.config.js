// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        "green-dark":  "#0C3C01",
        "green-mid":   "#5B6D49",
        "green-soft":  "#A2AC82",
        "cream":       "#F1F2ED",
        "bark":        "#2E2D1D",
      },
      fontFamily: {
        serif: ["Playfair Display", "Georgia", "serif"],
        sans:  ["DM Sans", "sans-serif"],
      },
    },
  },
  plugins: [],
};