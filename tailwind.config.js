/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
    './static/js/**/*.js',
    './*/views.py',
    './*/forms.py',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Arial', 'Helvetica', 'sans-serif'],
      },
      colors: {
        brand: {
          blue: {
            50: '#eef4ff',
            100: '#d9e6ff',
            200: '#b7cfff',
            300: '#8bb0ff',
            400: '#5c8bff',
            500: '#3366ff',
            600: '#1f4fe0',
            700: '#1a3fb3',
            800: '#173690',
            900: '#152f74',
            950: '#0d1b47',
          },
          green: {
            50: '#eafff5',
            100: '#c9ffe5',
            200: '#94ffcb',
            300: '#57f2ab',
            400: '#28d98d',
            500: '#0fbf76',
            600: '#0a9c60',
            700: '#0a7b4e',
            800: '#0c6140',
            900: '#0b4f36',
            950: '#063a27',
          },
          orange: {
            50: '#fff5eb',
            100: '#ffe6cc',
            200: '#ffc999',
            300: '#ffa85c',
            400: '#ff8c2e',
            500: '#f9740c',
            600: '#e05f00',
            700: '#b84a00',
            800: '#8f3900',
            900: '#742e00',
            950: '#421900',
          },
        },
      },
    },
  },
  plugins: [],
}
