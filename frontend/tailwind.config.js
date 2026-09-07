export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0c4a6e",
        steel: "#475569",
        mint: "#15803d",
        coral: "#dc2626",
        cloud: "#f0f9ff",
        navy: "#0369a1",
        accent: "#0369a1",
        muted: "#475569",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "none",
      },
      borderRadius: {
        "4xl": "1.75rem",
      },
    },
  },
  plugins: [],
};
