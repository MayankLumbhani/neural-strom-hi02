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
const scriptMatchers = new Map(
  (Object.keys(fontFamiliesByScript) as RegistryScript[]).map((script) => [
    script,
    new RegExp(String.raw`\p{Script=${script}}`, "u"),
  ]),
);
const pendingFonts = new Map<RegistryScript, Promise<void>>();

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

/** Load any supported script fonts needed by the supplied text. */
export function loadFontsForText(text: string): Promise<void[]> {
  const requests = Array.from(scriptMatchers, ([script, matcher]) =>
    matcher.test(text) ? loadScriptFont(script) : undefined,
  ).filter((request): request is Promise<void> => request !== undefined);
  return Promise.all(requests);
}
