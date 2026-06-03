/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ocean: {
          900: '#0a1628',
          800: '#0f2744',
          700: '#163656',
        },
      },
    },
  },
  plugins: [],
}
