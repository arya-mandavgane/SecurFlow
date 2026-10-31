/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aicte: {
          blue: '#0d3b66',
          navy: '#001e3d',
          gold: '#e09f3e',
          light: '#f4f7fb',
          accent: '#1976d2'
        }
      }
    },
  },
  plugins: [],
}
