import { cpSync, existsSync, mkdirSync } from "node:fs";

const standaloneRoot = ".next/standalone";
const staticSource = ".next/static";
const publicSource = "public";

if (!existsSync(standaloneRoot)) {
  throw new Error("Next.js standalone output is missing");
}

mkdirSync(`${standaloneRoot}/.next`, { recursive: true });
cpSync(staticSource, `${standaloneRoot}/.next/static`, { recursive: true });

if (existsSync(publicSource)) {
  cpSync(publicSource, `${standaloneRoot}/public`, { recursive: true });
}
