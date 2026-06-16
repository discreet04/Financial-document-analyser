/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101828",
        muted: "#667085",
        line: "#e4e7ec",
        brand: "#155EEF",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(16, 24, 40, 0.08)",
      },
    },
  },
  plugins: [],
};
