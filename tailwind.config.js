// tailwind.config.js
const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // Extend fonts, spacing, colors, etc.
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
      },
      colors: {
        'wizard-green': '#00ff9d',
        'wizard-accent': '#00D884',
        'wizard-background': '#0A1512',
        'wizard-background-lighter': '#1A2522',
        'wizard-background-darker': '#081210',
        'wizard-neutral-light': '#2A3532',
        'wizard-neutral-dark': '#1C2522',
        'wizard-text-primary': '#ffffff',
        'wizard-text-secondary': '#B4C4BE',
        'wizard-text-muted': '#4D6B5D',
      },
    },
  },
  plugins: [],
}
