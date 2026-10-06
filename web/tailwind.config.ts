import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0b0d10",
        panel: "#13171d",
        panel2: "#1a1f27",
        line: "#252b35",
        muted: "#a2aab7",
        text: "#e6e9ee",
        buy: "#22c55e",
        watch: "#eab308",
        skip: "#94a3b8",
        err: "#ef4444",
        accent: "#3b82f6",
        rise: "#f87171",
        fall: "#4ade80",
      },
    },
  },
  plugins: [],
};
export default config;
