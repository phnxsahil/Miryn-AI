// Next.js requires NODE_ENV=development for `next dev`. If the shell already
// exports NODE_ENV=production, Next skips the PostCSS/Tailwind pipeline, so
// `@tailwind` reaches css-loader raw and every route returns 500. Pin it here
// for the dev command only; build and start keep their own NODE_ENV.
import { spawn } from "node:child_process";

const child = spawn(
  process.execPath,
  [
    "--max-old-space-size=8192",
    "./node_modules/next/dist/bin/next",
    "dev",
    ...process.argv.slice(2),
  ],
  { stdio: "inherit", env: { ...process.env, NODE_ENV: "development" } },
);

child.on("exit", (code, signal) => {
  process.exit(signal ? 1 : code ?? 0);
});
