import { lazy, Suspense, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ChatPage } from "@/features/chat/ChatPage";
import { LoginPage } from "@/features/officer/LoginPage";
import { OfficerDashboard } from "@/features/officer/OfficerDashboard";
import { StatusPage } from "@/features/status/StatusPage";
import type { LoginResponse } from "@/lib/api";
import { getAnalyticsMessages } from "@/lib/analytics-i18n";
import { DesignPreviewPage } from "@/pages/DesignPreviewPage";
import type { ReactNode } from "react";
import type { UiLanguage } from "@/lib/i18n";

const AdminAnalyticsPage = lazy(() =>
  import("@/features/analytics/AdminAnalyticsPage").then((module) => ({
    default: module.AdminAnalyticsPage,
  })),
);

interface AppRoutesProps {
  language: UiLanguage;
  onLanguageChange: (language: UiLanguage) => void;
  session: LoginResponse | null;
  onLogin: (session: LoginResponse) => void;
  onLogout: () => void;
}

function AppRoutes({
  language,
  onLanguageChange,
  session,
  onLogin,
  onLogout,
}: AppRoutesProps) {
  const routes: ReactNode[] = [];
  if (import.meta.env.DEV) {
    routes.push(<Route element={<DesignPreviewPage />} key="design" path="/design" />);
  }
  routes.push(
    <Route
      element={
        session ? (
          <Navigate replace to="/dashboard" />
        ) : (
          <LoginPage language={language} onLogin={onLogin} />
        )
      }
      key="login"
      path="/login"
    />,
    <Route
      element={
        session ? (
          <OfficerDashboard
            language={language}
            onLogout={onLogout}
            session={session}
          />
        ) : (
          <Navigate replace to="/login" />
        )
      }
      key="dashboard"
      path="/dashboard"
    />,
    <Route
      element={
        session?.role === "ADMIN" ? (
          <Suspense
            fallback={
              <p className="p-6 text-body text-ink-muted" role="status">
                {getAnalyticsMessages(language).loading}
              </p>
            }
          >
            <AdminAnalyticsPage
              language={language}
              onLogout={onLogout}
              session={session}
            />
          </Suspense>
        ) : session ? (
          <Navigate replace to="/dashboard" />
        ) : (
          <Navigate replace to="/login" />
        )
      }
      key="analytics"
      path="/analytics"
    />,
    <Route
      element={<StatusPage language={language} />}
      key="status"
      path="/status"
    />,
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
  const [session, setSession] = useState<LoginResponse | null>(null);

  useEffect(() => {
    document.documentElement.lang = uiLanguage;
  }, [uiLanguage]);

  return (
    <BrowserRouter>
      <AppRoutes
        language={uiLanguage}
        onLanguageChange={setUiLanguage}
        onLogin={setSession}
        onLogout={() => setSession(null)}
        session={session}
      />
    </BrowserRouter>
  );
}
