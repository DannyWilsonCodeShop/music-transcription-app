/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#3f3f3f',
        secondary: '#00bfc4',
      },
    },
  },
  plugins: [],
}
