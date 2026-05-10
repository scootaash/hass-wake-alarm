import nodeResolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import typescript from "@rollup/plugin-typescript";
import terser from "@rollup/plugin-terser";

export default {
  input: "src/wake-alarm-card.ts",
  output: {
    file: "../custom_components/wake_alarm/www/wake-alarm-card.js",
    format: "es",
    sourcemap: false,
    inlineDynamicImports: true,
  },
  plugins: [
    nodeResolve(),
    commonjs(),
    typescript({
      tsconfig: "./tsconfig.json",
      outDir: "../custom_components/wake_alarm/www",
      declaration: false,
    }),
    terser({
      format: { comments: false },
    }),
  ],
};
