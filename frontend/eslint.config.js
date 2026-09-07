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
      "react/react-in-jsx-scope": "off",
    },
  },
];
