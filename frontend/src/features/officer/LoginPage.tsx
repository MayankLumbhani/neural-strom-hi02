import { ArrowLeft } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { Button, Card, Input } from "@/components/ui";
import { loginStaff, type LoginResponse } from "@/lib/api";
import { getOfficerMessages } from "@/lib/officer-i18n";
import type { UiLanguage } from "@/lib/i18n";

interface LoginPageProps {
  language: UiLanguage;
  onLogin: (session: LoginResponse) => void;
}

/** Authenticate staff and open the protected officer dashboard. */
export function LoginPage({ language, onLogin }: LoginPageProps) {
  const copy = getOfficerMessages(language);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setIsLoading(true);
    setHasError(false);
    try {
      onLogin(await loginStaff(username.trim(), password));
    } catch {
      setHasError(true);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-ink">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex w-full max-w-page items-center justify-between gap-4 px-4 py-4">
          <p className="text-heading font-semibold">
            {copy.serviceName}
          </p>
          <Link
            className="inline-flex min-h-touch items-center gap-2 text-small font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
            to="/"
          >
            <ArrowLeft aria-hidden="true" className="icon" />
            {copy.backToChat}
          </Link>
        </div>
      </header>
      <main
        className="mx-auto grid w-full max-w-page flex-1 content-center px-4 py-8"
        lang={language}
      >
        <Card className="mx-auto grid w-full max-w-chat gap-6">
          <header className="grid gap-2">
            <h1 className="text-title font-semibold text-ink">{copy.loginTitle}</h1>
            <p className="text-body text-ink-muted">{copy.loginDescription}</p>
          </header>
          <form className="grid gap-4" onSubmit={(event) => void handleSubmit(event)}>
            <Input
              autoComplete="username"
              label={copy.username}
              onChange={(event) => setUsername(event.target.value)}
              required
              value={username}
            />
            <Input
              autoComplete="current-password"
              label={copy.password}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
            {hasError ? (
              <p className="text-small text-danger" role="alert">
                {copy.loginError}
              </p>
            ) : null}
            <Button disabled={!username.trim() || !password} loading={isLoading} type="submit">
              {isLoading ? copy.loggingIn : copy.login}
            </Button>
          </form>
        </Card>
      </main>
    </div>
  );
}
