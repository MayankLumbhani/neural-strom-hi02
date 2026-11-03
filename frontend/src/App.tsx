import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ChatPage } from "@/features/chat/ChatPage";
import { DesignPreviewPage } from "@/pages/DesignPreviewPage";
import type { UiLanguage } from "@/lib/i18n";
import type { ReactNode } from "react";

interface AppRoutesProps {
  language: UiLanguage;
  onLanguageChange: (language: UiLanguage) => void;
}

function AppRoutes({ language, onLanguageChange }: AppRoutesProps) {
  const routes: ReactNode[] = [];
  if (import.meta.env.DEV) {
    routes.push(<Route element={<DesignPreviewPage />} key="design" path="/design" />);
  }
  routes.push(
    <Route
      element={
        <ChatPage language={language} onLanguageChange={onLanguageChange} />
      }
      key="home"
      path="*"
    />,
  );

  return <Routes>{routes}</Routes>;
}

export function App({ language }: { language: UiLanguage }) {
  const [uiLanguage, setUiLanguage] = useState(language);

  useEffect(() => {
    document.documentElement.lang = uiLanguage;
  }, [uiLanguage]);

  return (
    <BrowserRouter>
      <AppRoutes
        language={uiLanguage}
        onLanguageChange={setUiLanguage}
      />
    </BrowserRouter>
  );
}
