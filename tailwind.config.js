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
        'wizard-green': 'var(--wizard-green)',
        'wizard-accent': 'var(--wizard-accent)',
        'wizard-background': 'var(--wizard-background)',
        'wizard-background-lighter': 'var(--wizard-background-lighter)',
        'wizard-background-darker': 'var(--wizard-background-darker)',
        'wizard-neutral-light': 'var(--wizard-neutral-light)',
        'wizard-neutral-dark': 'var(--wizard-neutral-dark)',
        'wizard-text-primary': 'var(--wizard-text-primary)',
        'wizard-text-secondary': 'var(--wizard-text-secondary)',
        'wizard-text-muted': 'var(--wizard-text-muted)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
    },
  },
  plugins: [],
}
