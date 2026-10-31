import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#19324a",
        navy: "#12344d",
        mist: "#f4f8fb",
        teal: "#087f8c",
        mint: "#e5f5f3",
        amber: "#a56708",
        urgent: "#c33b43",
      },
      boxShadow: {
        soft: "0 8px 30px rgba(24, 55, 78, 0.07)",
      },
    },
  },
  plugins: [],
};

export default config;
