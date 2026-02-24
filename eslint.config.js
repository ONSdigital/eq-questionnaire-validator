import neostandard from "neostandard";
import * as jsonParser from "jsonc-eslint-parser";
import globals from "globals";

const jsConfigs = neostandard({}).map((config) => ({
  ...config,
  files: ["**/*.js", "**/*.cjs", "**/*.mjs"],
}));

export default [
  ...jsConfigs,

  // Your custom rule overrides
  {
    files: ["**/*.js", "**/*.cjs", "**/*.mjs"],
    rules: {
      "consistent-return": "warn",
      indent: ["error", 2, { SwitchCase: 1 }],
      "comma-dangle": "off",
      "new-cap": "error",
      "no-alert": "warn",
      "no-console": "error",
      "no-dupe-class-members": "off",
      "no-unused-expressions": "off",
      "no-var": "error",
      "prefer-arrow-callback": ["error", { allowNamedFunctions: false }],

      // ⚠ stylistic rules must use @stylistic prefix in ESLint 9
      "@stylistic/quotes": [
        "error",
        "double",
        {
          avoidEscape: true,
          allowTemplateLiterals: true,
        },
      ],
      "@stylistic/semi": ["error", "always"],
      "@stylistic/space-before-function-paren": "off",
      "@stylistic/padded-blocks": ["error", { blocks: "never" }],
    },
  },

  // Mocha test files
  {
    files: ["**/*.test.js", "**/tests/**/*.js"],
    languageOptions: {
      globals: {
        ...globals.mocha, // adds describe, it, before, etc.
      },
    },
  },

  {
    files: ["**/*.json", "**/*.json5"], // JSON files or JSON5 if needed
    languageOptions: {
      parser: jsonParser, // parser object
    },
    rules: {}, // JSON rules go here if needed
  },
];
