import react from "eslint-plugin-react";

export default [
  { ignores: ["dist/**", "node_modules/**"] },
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        document: "readonly",
        FormData: "readonly",
        import: "readonly",
        localStorage: "readonly",
        window: "readonly",
        AbortController: "readonly",
        AbortSignal: "readonly",
        Blob: "readonly",
        CustomEvent: "readonly",
        ResizeObserver: "readonly",
        TextEncoder: "readonly",
        URL: "readonly",
        URLSearchParams: "readonly",
        cancelAnimationFrame: "readonly",
        clearInterval: "readonly",
        clearTimeout: "readonly",
        crypto: "readonly",
        requestAnimationFrame: "readonly",
        sessionStorage: "readonly",
        setInterval: "readonly",
        setTimeout: "readonly",
        structuredClone: "readonly",
      },
    },
    plugins: { react },
    settings: {
      react: { version: "detect" },
    },
    rules: {
      ...react.configs.recommended.rules,
      "react/prop-types": "off",
      "no-unused-vars": "error",
      "no-undef": "error",
      "react/react-in-jsx-scope": "off",
    },
  },
  { files: ["src/**/*.test.js"], languageOptions: { globals: { setImmediate: "readonly" } } },
];
