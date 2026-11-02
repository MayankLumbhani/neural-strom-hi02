import { BrowserRouter, Route, Routes } from "react-router-dom";
import { DesignPreviewPage } from "@/pages/DesignPreviewPage";
import { getDesignMessages, type UiLanguage } from "@/lib/i18n";
import type { ReactNode } from "react";

function ScaffoldPage({ language }: { language: UiLanguage }) {
  const messages = getDesignMessages(language);

  return (
    <main lang={language}>
      <h1>{messages.title}</h1>
      <p>{messages.description}</p>
    </main>
  );
}

function AppRoutes({ language }: { language: UiLanguage }) {
  const routes: ReactNode[] = [];
  if (import.meta.env.DEV) {
    routes.push(<Route element={<DesignPreviewPage />} key="design" path="/design" />);
  }
  routes.push(<Route element={<ScaffoldPage language={language} />} key="home" path="*" />);

  return <Routes>{routes}</Routes>;
}

export function App({ language }: { language: UiLanguage }) {
  return (
    <BrowserRouter>
      <AppRoutes language={language} />
    </BrowserRouter>
  );
}
