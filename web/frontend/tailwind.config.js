/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        chorus: {
          primary: '#f4b183',    // warm orange/peach
          secondary: '#c87137',  // darker orange
          accent: '#ffcc99',     // light peach
          dark: '#2d2d2d',       // very dark gray
          medium: '#5d5d5d',     // medium gray
          light: '#f0f0f0',      // light text
        },
        nova: {
          light: '#22d3ee',  // Brighter cyan for dark mode
          DEFAULT: '#06b6d4',
          dark: '#0891b2',
        },
        atlas: {
          light: '#fbbf24',  // Amber/yellow
          DEFAULT: '#f59e0b',
          dark: '#d97706',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'thinking': 'thinking 2s ease-in-out infinite',
      },
      keyframes: {
        thinking: {
          '0%, 100%': { opacity: '0.5' },
          '50%': { opacity: '1' },
        }
      }
    },
  },
  plugins: [],
}
