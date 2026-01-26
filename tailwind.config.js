/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3f3f3f',      // Dark gray - headers, text
        secondary: '#00bfc4',    // Cyan - accents, buttons
        tertiary: '#0089c6',     // Blue - links, secondary buttons
        accent: '#ffe600',       // Yellow - highlights, warnings
        neutral: '#9e9e9e',      // Gray - secondary text
        background: '#e5e5e5',   // Light gray - backgrounds
      },
    },
  },
  plugins: [],
}
