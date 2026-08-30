import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        mist: "#f5f7fb",
        accent: "#3857e8",
      },
    },
  },
  plugins: [],
};

export default config;
