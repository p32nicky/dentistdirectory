/** Tailwind build config — compiles web/templates classes to static CSS. */
module.exports = {
  content: ["./web/templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        primary: "#0d9488", primaryDark: "#0f766e", secondary: "#134e4a",
        gradient: "#155e75", accent: "#06b6d4",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
