export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: { 800: '#1a1f3a', 900: '#0f1225', 950: '#090b18' },
        cyber: { cyan: '#06b6d4', emerald: '#10b981', amber: '#f59e0b', red: '#ef4444', purple: '#8b5cf6' },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      backdropBlur: { xs: '2px' },
    },
  },
  plugins: [],
}
