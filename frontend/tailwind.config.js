/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        court: "#0f0f10",
        surface: "#1a1a1b",
        border: "#2a2a2b",
        accent: "var(--team-accent, #552583)", // Default fallback (e.g. Lakers purple)
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontWeight: {
        normal: '400',
        semibold: '600',
        bold: '700',
        extrabold: '800',
      }
    },
  },
  plugins: [],
}
