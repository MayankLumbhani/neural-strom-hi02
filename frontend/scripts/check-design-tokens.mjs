import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const frontendDirectory = path.resolve(scriptDirectory, "..");
const sourceDirectory = path.join(frontendDirectory, "src");
const tokenFile = path.join(sourceDirectory, "styles", "tokens.css");
const scannedExtensions = new Set([".ts", ".tsx", ".css", ".html"]);
const forbiddenPatterns = [
  {
    description: "hex colors or RGB colors",
    expression: /#[\da-f]{3,8}(?![\da-f])|\brgba?\s*\(/i,
  },
  {
    description: "default Tailwind palette classes",
    expression:
      /(?:^|[^a-z\d_-])(?:bg|text|border|ring|from|via|to|fill|stroke)-(?:slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}(?:$|[^a-z\d_-])/im,
  },
  {
    description: "arbitrary Tailwind values",
    expression:
      /(?:^|[^a-z\d_-])(?:bg|text|border|ring|w|h|min-w|min-h|max-w|max-h|p|px|py|m|mx|my|gap|rounded|shadow)-\[[^\]]+\]/im,
  },
];

async function collectSourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const paths = await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        return collectSourceFiles(entryPath);
      }

      if (scannedExtensions.has(path.extname(entry.name))) {
        return [entryPath];
      }
      return [];
    }),
  );
  return paths.flat();
}

async function main() {
  const tokenStats = await stat(tokenFile).catch(() => undefined);
  if (!tokenStats?.isFile()) {
    throw new Error(`Design token source is missing: ${tokenFile}`);
  }

  const sourceFiles = [
    ...(await collectSourceFiles(sourceDirectory)),
    path.join(frontendDirectory, "index.html"),
  ].filter((filePath) => filePath !== tokenFile);

  for (const { description, expression } of forbiddenPatterns) {
    const violations = [];
    for (const filePath of sourceFiles) {
      const contents = await readFile(filePath, "utf8");
      contents.split(/\r?\n/).forEach((line, index) => {
        if (expression.test(line)) {
          violations.push(
            `${path.relative(frontendDirectory, filePath)}:${index + 1}: ${line.trim()}`,
          );
        }
        expression.lastIndex = 0;
      });
    }

    if (violations.length > 0) {
      throw new Error(
        `Forbidden ${description} found outside tokens.css:\n${violations.join("\n")}`,
      );
    }
  }

  console.log("Design token check passed.");
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
