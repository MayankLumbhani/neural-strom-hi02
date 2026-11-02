export type UiMessageKey = "title" | "description";

const messages = {
  en: {
    title: "Furfuri Nagar Municipal Corporation",
    description: "The frontend scaffold is ready for the citizen service.",
  },
  hi: {
    title: "फुरफुरी नगर नगर निगम",
    description: "नागरिक सेवा के लिए फ्रंटएंड तैयार है।",
  },
  gu: {
    title: "ફુરફુરી નગર મહાનગરપાલિકા",
    description: "નાગરિક સેવા માટે ફ્રન્ટએન્ડ તૈયાર છે.",
  },
} satisfies Record<string, Record<UiMessageKey, string>>;

export type UiLanguage = keyof typeof messages;

export function resolveUiLanguage(browserLanguage: string): UiLanguage {
  const languageCode = browserLanguage.split("-")[0]?.toLowerCase();
  return isUiLanguage(languageCode) ? languageCode : "en";
}

export function translate(language: UiLanguage, key: UiMessageKey): string {
  return messages[language][key];
}

function isUiLanguage(languageCode: string | undefined): languageCode is UiLanguage {
  return languageCode !== undefined && Object.hasOwn(messages, languageCode);
}
