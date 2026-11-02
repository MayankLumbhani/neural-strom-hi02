import { BrowserRouter, Route, Routes } from "react-router-dom";
import { translate, type UiLanguage } from "@/lib/i18n";

function ScaffoldPage({ language }: { language: UiLanguage }) {
  return (
    <main lang={language}>
      <h1>{translate(language, "title")}</h1>
      <p>{translate(language, "description")}</p>
    </main>
  );
}

export function App({ language }: { language: UiLanguage }) {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<ScaffoldPage language={language} />} />
      </Routes>
    </BrowserRouter>
  );
}
