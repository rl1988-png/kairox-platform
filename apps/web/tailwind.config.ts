import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        kairox: {
          pink: '#fc81b9',
          'pink-dark': '#e85a9d',
        },
        bg: {
          primary: '#0b1220',
          secondary: '#121a2b',
          tertiary: '#0d1424',
        },
        border: '#243049',
        text: {
          primary: '#e8eefc',
          muted: '#9aa8c7',
        },
        link: '#8eb4ff',
        success: '#3dd68c',
        warning: '#ffcc66',
        danger: '#ff6b7a',
        overlay: '#051134',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'Consolas', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(252, 129, 185, 0.15)',
        card: '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
};

export default config;
