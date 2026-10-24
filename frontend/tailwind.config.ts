import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0d10",
        panel: "#12151b",
        line: "#232833",
        muted: "#8b93a7",
        accent: "#7c9cff",
      },
    },
  },
  plugins: [],
};

export default config;
