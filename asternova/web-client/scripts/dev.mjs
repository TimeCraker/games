import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const extra = process.argv.slice(2);
const nextCli = path.join(projectRoot, "node_modules", "next", "dist", "bin", "next");

const wantsTurbopack =
  extra.includes("--turbopack") || extra.includes("--turbo");
const passthrough = extra.filter(
  (a) => a !== "--turbopack" && a !== "--turbo",
);
/** Turbopack 在本项目下会在首屏编译时 panic；默认用 Webpack，需要时再传 --turbopack */
const bundlerFlag = wantsTurbopack ? [] : ["--webpack"];

const env = {
  ...process.env,
  INIT_CWD: projectRoot,
  PWD: projectRoot,
  /** 强制 Next 项目根，避免多文件夹工作区把目录判成 Desktop（见 next-dev.js getProjectDir） */
  NEXT_PRIVATE_DEV_DIR: projectRoot,
};

const child = spawn(
  process.execPath,
  [nextCli, "dev", projectRoot, ...bundlerFlag, ...passthrough],
  {
    cwd: projectRoot,
    stdio: "inherit",
    shell: false,
    env,
  },
);

child.on("exit", (code) => process.exit(code ?? 0));
