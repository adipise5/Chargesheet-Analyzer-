/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#12263a', navy: '#0b1f33', canvas: '#f3f6f8', line: '#d9e1e7',
      },
      boxShadow: { panel: '0 1px 2px rgb(15 23 42 / 6%), 0 8px 28px rgb(15 23 42 / 5%)' },
    },
  },
  plugins: [],
}
