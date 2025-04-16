module.exports = {
  plugins: {
    'postcss-import': {},
    'postcss-nesting': {},
    'postcss-preset-env': {
      stage: 3,
      features: {
        'nesting-rules': true
      }
    },
    tailwindcss: {},
    autoprefixer: {},
  },
} 
