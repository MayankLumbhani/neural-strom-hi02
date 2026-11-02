const fontFamiliesByScript = {
  Latin: "Noto Sans",
  Devanagari: "Noto Sans Devanagari",
  Gujarati: "Noto Sans Gujarati",
  Bengali: "Noto Sans Bengali",
  Gurmukhi: "Noto Sans Gurmukhi",
  Tamil: "Noto Sans Tamil",
  Telugu: "Noto Sans Telugu",
  Kannada: "Noto Sans Kannada",
  Malayalam: "Noto Sans Malayalam",
} as const;

export type RegistryScript = keyof typeof fontFamiliesByScript;

const eagerlyLoadedScripts = new Set<RegistryScript>([
  "Latin",
  "Devanagari",
  "Gujarati",
]);
const pendingFonts = new Map<RegistryScript, Promise<void>>();

export function loadLatinFont(): void {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href =
    "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=Noto+Sans:wght@400;500;600;700&display=swap";
  document.head.append(link);
}

export function loadScriptFont(script: RegistryScript): Promise<void> {
  if (eagerlyLoadedScripts.has(script)) {
    return Promise.resolve();
  }

  const existingRequest = pendingFonts.get(script);
  if (existingRequest) {
    return existingRequest;
  }

  const family = encodeURIComponent(fontFamiliesByScript[script]);
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = `https://fonts.googleapis.com/css2?family=${family}:wght@400;500;600;700&display=swap`;

  const request = new Promise<void>((resolve, reject) => {
    link.addEventListener("load", () => resolve(), { once: true });
    link.addEventListener(
      "error",
      () => reject(new Error(`Unable to load the ${script} font.`)),
      { once: true },
    );
    document.head.append(link);
  }).catch((error: unknown) => {
    pendingFonts.delete(script);
    throw error;
  });

  pendingFonts.set(script, request);
  return request;
}
