/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: {
          50:  '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          800: '#1e293b',
          850: '#0f172a',
          900: '#020617',
          950: '#010409',
        },
        primary: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          400: '#312e81', // Deep PWD Blue
          500: '#1e1b4b', // Darker PWD Blue
          600: '#17153b',
        },
        gold: {
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
        },
        saffron: {
          400: '#fb923c',
          500: '#f97316',
          600: '#ea580c',
        },
        glass: {
          border: 'rgba(255,255,255,0.08)',
          bg:    'rgba(255,255,255,0.04)',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'mesh-dark': 'radial-gradient(at 40% 20%, hsla(228,100%,74%,0.08) 0px, transparent 50%), radial-gradient(at 80% 0%, hsla(189,100%,56%,0.06) 0px, transparent 50%), radial-gradient(at 0% 50%, hsla(355,100%,93%,0.04) 0px, transparent 50%)',
      },
      boxShadow: {
        glass: '0 4px 24px -1px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06)',
        'glass-lg': '0 8px 40px -4px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)',
        glow: '0 0 20px rgba(99,102,241,0.3)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
};
