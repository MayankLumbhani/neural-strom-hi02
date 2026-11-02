import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "@/App";
import { loadLatinFont } from "@/lib/fonts";
import { resolveUiLanguage } from "@/lib/i18n";
import "@/index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("The frontend root element is missing.");
}

loadLatinFont();
const language = resolveUiLanguage(navigator.language);
document.documentElement.lang = language;

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App language={language} />
  </React.StrictMode>,
);
