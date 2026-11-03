import { Building2, LoaderCircle, Send } from "lucide-react";
import { Link } from "react-router-dom";
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import {
  ChatBubble,
  QuickReply,
  Textarea,
  TicketCard,
} from "@/components/ui";
import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import {
  ApiError,
  getBackendReadiness,
  sendChatMessage,
  type ChatTicketSummary,
} from "@/lib/api";
import { getChatMessages } from "@/lib/chat-i18n";
import { loadFontsForText } from "@/lib/fonts";
import type { UiLanguage } from "@/lib/i18n";

const WAKE_MESSAGE_DELAY_MS = 3000;
const READINESS_RETRY_DELAYS_MS = [500, 1000, 2000] as const;

interface ChatEntry {
  id: string;
  sender: "citizen" | "bot";
  text: string;
  language: string;
  languageTier?: number;
  quickReplies?: string[];
  ticket?: ChatTicketSummary;
}

type ChatErrorKind = "tooLong" | "rateLimited" | "generic";

interface ChatPageProps {
  language: UiLanguage;
  onLanguageChange: (language: UiLanguage) => void;
}

/** Render the multilingual complaint flow and its persisted conversation. */
export function ChatPage({ language, onLanguageChange }: ChatPageProps) {
  const copy = getChatMessages(language);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [wakingUp, setWakingUp] = useState(false);
  const [errorKind, setErrorKind] = useState<ChatErrorKind | null>(null);
  const [fontError, setFontError] = useState(false);
  const messageListRef = useRef<HTMLDivElement>(null);
  const serviceReadyRef = useRef(false);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  useEffect(() => {
    const messageList = messageListRef.current;
    if (messageList) {
      messageList.scrollTo({ top: messageList.scrollHeight });
    }
  }, [messages.length, sending]);

  function requestFonts(text: string): void {
    void loadFontsForText(text).catch(() => {
      setFontError(true);
    });
  }

  async function submitMessage(text: string): Promise<void> {
    const complaint = text.trim();
    if (!complaint || sending) {
      return;
    }

    setDraft(complaint);
    setSending(true);
    setWakingUp(false);
    setErrorKind(null);
    setMessages((currentMessages) =>
      currentMessages.map((entry) =>
        entry.sender === "bot" ? { ...entry, quickReplies: [] } : entry,
      ),
    );
    const wakeTimer = window.setTimeout(
      () => setWakingUp(true),
      WAKE_MESSAGE_DELAY_MS,
    );

    try {
      if (!serviceReadyRef.current) {
        await waitForBackendReadiness();
        serviceReadyRef.current = true;
      }

      const response = await sendChatMessage({
        text: complaint,
        conversation_id: conversationId,
      });
      if (!response.language || !response.reply.text) {
        throw new Error("The chat response is missing its language or reply.");
      }

      setConversationId(
        response.state === "TICKET_CREATED" ? null : response.conversation_id,
      );
      setDraft("");
      requestFonts(`${complaint} ${response.reply.text}`);
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: crypto.randomUUID(),
          sender: "citizen",
          text: complaint,
          language: response.language,
        },
        {
          id: crypto.randomUUID(),
          sender: "bot",
          text: response.reply.text,
          language: response.language,
          languageTier: response.language_tier,
          quickReplies: response.reply.quick_replies,
          ticket: response.state === "TICKET_CREATED" ? response.ticket ?? undefined : undefined,
        },
      ]);
    } catch (error: unknown) {
      setErrorKind(getSubmissionErrorKind(error));
    } finally {
      window.clearTimeout(wakeTimer);
      setSending(false);
      setWakingUp(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void submitMessage(draft);
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>): void {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      void submitMessage(draft);
    }
  }

  function chooseExample(text: string): void {
    setDraft(text);
    void submitMessage(text);
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-ink">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex w-full max-w-page flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <Building2 aria-hidden="true" className="icon text-primary" />
            <div className="min-w-0">
              <p className="text-heading font-semibold text-ink">
                {copy.serviceName}
              </p>
              <p className="text-small text-ink-muted">
                {copy.serviceDescription}
              </p>
            </div>
          </div>
          <LanguageSwitcher
            language={language}
            label={copy.languageLabel}
            onLanguageChange={onLanguageChange}
          />
          <Link
            className="min-h-touch content-center text-small font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
            to="/status"
          >
            {copy.statusLink}
          </Link>
          <Link
            className="min-h-touch content-center text-small font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
            to="/login"
          >
            {copy.staffLogin}
          </Link>
        </div>
      </header>

      <main
        className="mx-auto flex w-full max-w-page flex-1 flex-col gap-6 px-4 py-6"
        lang={language}
      >
        {messages.length === 0 ? (
          <section aria-labelledby="chat-welcome-title" className="grid gap-3">
            <h1
              className="text-display font-bold text-ink"
              id="chat-welcome-title"
            >
              {copy.welcomeTitle}
            </h1>
            <p className="max-w-chat text-body text-ink-muted">
              {copy.welcomeDescription}
            </p>
            <div className="grid gap-3">
              <h2 className="text-small font-semibold text-ink">
                {copy.examplesLabel}
              </h2>
              <div className="grid gap-3 sm:grid-cols-3">
                {copy.examples.map((example) => (
                  <Button
                    className="h-auto justify-start whitespace-normal text-start"
                    disabled={sending}
                    key={example.label}
                    onClick={() => chooseExample(example.text)}
                    type="button"
                    variant="secondary"
                  >
                    <span className="grid gap-1">
                      <span className="text-small font-semibold">
                        {example.label}
                      </span>
                      <span
                        className="font-normal"
                        lang={example.language}
                      >
                        {example.text}
                      </span>
                    </span>
                  </Button>
                ))}
              </div>
            </div>
          </section>
        ) : null}

        <div
          aria-live="polite"
          aria-relevant="additions text"
          className="flex flex-1 flex-col gap-4 overflow-y-auto"
          ref={messageListRef}
          role="log"
          aria-label={copy.serviceDescription}
        >
          {messages.map((entry) => (
            <div className="grid gap-2" key={entry.id}>
              <ChatBubble
                language={entry.language}
                message={entry.text}
                sender={entry.sender}
              />
              {entry.sender === "bot" &&
              entry.languageTier === 2 ? (
                <p className="text-small text-ink-muted" lang={language}>
                  {copy.experimentalNote}
                </p>
              ) : null}
              {entry.sender === "bot" && entry.quickReplies?.length ? (
                <div className="flex flex-wrap gap-2">
                  {entry.quickReplies.map((reply) => (
                    <QuickReply
                      disabled={sending}
                      key={reply}
                      label={reply}
                      onSelect={(selectedReply) =>
                        void submitMessage(selectedReply)
                      }
                    />
                  ))}
                </div>
              ) : null}
              {entry.ticket ? (
                <TicketCard
                  department={entry.ticket.department}
                  labels={{
                    title: copy.ticketTitle,
                    department: copy.department,
                    location: copy.location,
                    filedAt: copy.filedAt,
                    copyId: copy.copyId,
                    copied: copy.copied,
                    copyFailed: copy.copyFailed,
                  }}
                  status="Filed"
                  statusLabel={entry.ticket.status}
                  ticketId={entry.ticket.ticket_id}
                />
              ) : null}
            </div>
          ))}
          {sending ? (
            <div className="flex items-center gap-2 text-small text-ink-muted">
              <span aria-hidden="true" className="flex items-center gap-1">
                <span className="chat-typing-dot h-2 w-2 rounded-full bg-ink-muted" />
                <span className="chat-typing-dot h-2 w-2 rounded-full bg-ink-muted" />
                <span className="chat-typing-dot h-2 w-2 rounded-full bg-ink-muted" />
              </span>
              <span role="status">{copy.typing}</span>
            </div>
          ) : null}
          <div aria-hidden="true" />
        </div>

        {wakingUp ? (
          <p
            className="flex items-center gap-2 rounded-sm border border-border bg-surface-muted p-3 text-small text-ink"
            role="status"
          >
            <LoaderCircle aria-hidden="true" className="icon animate-spin" />
            {copy.wakingUp}
          </p>
        ) : null}
        {errorKind ? (
          <p className="text-small text-danger" role="alert">
            <span className="font-semibold">{copy.errorTitle}. </span>
            {getChatErrorCopy(errorKind, copy)}
          </p>
        ) : null}
        {fontError ? (
          <p className="text-small text-ink-muted" role="status">
            {copy.fontError}
          </p>
        ) : null}
      </main>

      <footer className="sticky bottom-0 border-t border-border bg-surface">
        <form
          className="mx-auto flex w-full max-w-page flex-col gap-3 px-4 py-3 sm:flex-row sm:items-end"
          onSubmit={handleSubmit}
        >
          <div className="min-w-0 flex-1">
            <Textarea
              autoComplete="off"
              label={copy.composerLabel}
              onChange={(event) => {
                setDraft(event.currentTarget.value);
                setErrorKind(null);
              }}
              onKeyDown={handleComposerKeyDown}
              placeholder={copy.placeholder}
              rows={2}
              value={draft}
            />
          </div>
          <Button
            disabled={sending || !draft.trim()}
            type="submit"
          >
            <Send aria-hidden="true" className="icon" />
            {copy.send}
          </Button>
        </form>
      </footer>
    </div>
  );
}

async function waitForBackendReadiness(): Promise<void> {
  for (let attempt = 0; ; attempt += 1) {
    try {
      await getBackendReadiness();
      return;
    } catch (error: unknown) {
      const retryDelay = READINESS_RETRY_DELAYS_MS[attempt];
      if (retryDelay === undefined || !isTransientReadinessError(error)) {
        throw error;
      }
      await new Promise<void>((resolve) => {
        window.setTimeout(resolve, retryDelay);
      });
    }
  }
}

function isTransientReadinessError(error: unknown): boolean {
  return (
    error instanceof TypeError ||
    (error instanceof ApiError && error.status >= 500)
  );
}

function getSubmissionErrorKind(error: unknown): ChatErrorKind {
  if (error instanceof ApiError && error.status === 413) {
    return "tooLong";
  }
  if (error instanceof ApiError && error.status === 429) {
    return "rateLimited";
  }
  return "generic";
}

function getChatErrorCopy(
  errorKind: ChatErrorKind,
  copy: ReturnType<typeof getChatMessages>,
): string {
  switch (errorKind) {
    case "tooLong":
      return copy.tooLongError;
    case "rateLimited":
      return copy.rateLimitError;
    case "generic":
      return copy.genericError;
  }
}
