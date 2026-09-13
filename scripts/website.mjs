import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath, URL } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const vite = fileURLToPath(new URL("../node_modules/vite/bin/vite.js", import.meta.url));
const [action, ...options] = process.argv.slice(2);
if (!["dev", "preview"].includes(action) || options.some(option => option !== "--no-open")) {
  console.error("Usage: node scripts/website.mjs <dev|preview> [--no-open]");
  process.exit(1);
}
if (!existsSync(vite)) {
  console.error("Website dependencies are missing. Install them with corepack pnpm install first.");
  process.exit(1);
}

function run(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [vite, ...args], { cwd: root, stdio: "inherit" });
    // Both processes receive terminal signals; keep the parent alive until Vite exits.
    const stop = () => child.kill("SIGTERM");
    process.on("SIGINT", stop);
    process.on("SIGTERM", stop);
    child.on("error", reject);
    child.on("exit", (code) => {
      process.off("SIGINT", stop);
      process.off("SIGTERM", stop);
      resolve(code ?? 1);
    });
  });
}

try {
  if (action === "preview") {
    console.log("Building the production website before previewing it...");
    const code = await run(["build"]);
    if (code !== 0) process.exit(code);
  }
  console.log("Keep this window open. Press Ctrl+C to stop the local website.");
  const args = action === "preview" ? ["preview"] : [];
  if (!options.includes("--no-open")) args.push("--open", "/CGL-Record-Book/");
  process.exitCode = await run(args);
} catch (error) {
  console.error(`Could not start the website: ${error.message}`);
  process.exitCode = 1;
}
