import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Manrope"', '"Segoe UI"', 'sans-serif'],
        display: ['"Space Grotesk"', '"Segoe UI"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        ink: '#152028',
        sky: '#d9f2ff',
        surf: '#f6fbff',
        coral: '#ff7043',
        mint: '#16a085',
      },
      boxShadow: {
        panel: '0 10px 30px rgba(21, 32, 40, 0.08)',
      },
    },
  },
  plugins: [],
} satisfies Config
