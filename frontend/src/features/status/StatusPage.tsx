import { ArrowLeft, CircleDot } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  Button,
  EmptyState,
  ErrorState,
  Input,
  Skeleton,
  TicketCard,
} from "@/components/ui";
import { ApiError, getTicketStatus, type PublicTicketResponse } from "@/lib/api";
import { getStatusMessages } from "@/lib/status-i18n";
import type { UiLanguage } from "@/lib/i18n";
import type { TicketStatus } from "@/components/ui/ticket-status";

type LookupState = "idle" | "loading" | "notFound" | "error";

const DATE_LOCALES: Record<UiLanguage, string> = {
  en: "en-IN",
  hi: "hi-IN",
  gu: "gu-IN",
};
const DISPLAY_STATUSES: Record<
  PublicTicketResponse["status_code"],
  TicketStatus
> = {
  FILED: "Filed",
  ASSIGNED: "Assigned",
  IN_PROGRESS: "In Progress",
  RESOLVED: "Resolved",
  ESCALATED: "Escalated",
};

interface StatusPageProps {
  language: UiLanguage;
}

/** Look up a ticket and show its public status history. */
export function StatusPage({ language }: StatusPageProps) {
  const copy = getStatusMessages(language);
  const [ticketId, setTicketId] = useState("");
  const [ticket, setTicket] = useState<PublicTicketResponse | null>(null);
  const [lookupState, setLookupState] = useState<LookupState>("idle");

  async function lookupStatus(id: string): Promise<void> {
    const normalizedId = id.trim().toUpperCase();
    if (!normalizedId) {
      return;
    }

    setTicketId(normalizedId);
    setTicket(null);
    setLookupState("loading");

    try {
      setTicket(await getTicketStatus(normalizedId));
      setLookupState("idle");
    } catch (error: unknown) {
      setLookupState(
        error instanceof ApiError && error.status === 404 ? "notFound" : "error",
      );
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    void lookupStatus(ticketId);
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-ink">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex w-full max-w-page flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div>
            <p className="text-heading font-semibold text-ink">
              {copy.serviceName}
            </p>
            <p className="text-small text-ink-muted">
              {copy.serviceDescription}
            </p>
          </div>
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
        className="mx-auto grid w-full max-w-page flex-1 content-start gap-6 px-4 py-6"
        lang={language}
      >
        <section className="grid gap-3" aria-labelledby="status-title">
          <h1 className="text-display font-bold text-ink" id="status-title">
            {copy.title}
          </h1>
          <p className="max-w-chat text-body text-ink-muted">
            {copy.description}
          </p>
          <form
            className="grid items-end gap-3 sm:grid-cols-[1fr_auto]"
            onSubmit={handleSubmit}
          >
            <Input
              autoComplete="off"
              label={copy.ticketIdLabel}
              onChange={(event) => setTicketId(event.target.value)}
              placeholder={copy.ticketIdPlaceholder}
              required
              value={ticketId}
            />
            <Button
              disabled={!ticketId.trim()}
              loading={lookupState === "loading"}
              type="submit"
            >
              {lookupState === "loading"
                ? copy.checkingStatus
                : copy.checkStatus}
            </Button>
          </form>
        </section>

        {lookupState === "loading" ? (
          <section aria-label={copy.checkingStatus} className="grid gap-4">
            <Skeleton className="w-full" lines={3} />
            <Skeleton className="w-full" lines={2} />
          </section>
        ) : null}

        {lookupState === "notFound" ? (
          <ErrorState
            message={copy.notFoundMessage}
            onRetry={() => void lookupStatus(ticketId)}
            retryLabel={copy.retry}
            title={copy.notFoundTitle}
          />
        ) : null}

        {lookupState === "error" ? (
          <ErrorState
            message={copy.errorMessage}
            onRetry={() => void lookupStatus(ticketId)}
            retryLabel={copy.retry}
            title={copy.errorTitle}
          />
        ) : null}

        {ticket ? (
          <section className="grid gap-6" aria-live="polite">
            <TicketCard
              department={ticket.department}
              filedAt={formatDate(ticket.created_at, language)}
              labels={{
                title: copy.resultTitle,
                department: copy.department,
                location: copy.location,
                filedAt: copy.filedAt,
                copyId: copy.copyId,
                copied: copy.copied,
                copyFailed: copy.copyFailed,
              }}
              location={ticket.location}
              status={DISPLAY_STATUSES[ticket.status_code]}
              statusLabel={ticket.status}
              ticketId={ticket.public_id}
              valueLanguage={ticket.language}
            />
            <p className="text-small text-ink-muted" lang={language}>
              {copy.updatedAt}: {formatDate(ticket.updated_at, language)}
            </p>

            <section className="grid gap-3" aria-labelledby="ticket-timeline">
              <h2
                className="text-title font-semibold text-ink"
                id="ticket-timeline"
              >
                {copy.timeline}
              </h2>
              {ticket.public_events.length > 0 ? (
                <ol className="grid gap-0">
                  {ticket.public_events.map((event, index) => (
                    <li
                      className="grid grid-cols-[auto_1fr] gap-x-3"
                      key={`${event.created_at}-${index}`}
                      lang={ticket.language}
                    >
                      <div className="flex flex-col items-center">
                        <CircleDot
                          aria-hidden="true"
                          className="icon text-primary"
                        />
                        {index < ticket.public_events.length - 1 ? (
                          <span
                            aria-hidden="true"
                            className="min-h-8 flex-1 border-s border-border"
                          />
                        ) : null}
                      </div>
                      <div className="grid gap-1 pb-5">
                        <p className="font-semibold text-ink">
                          {event.to_status}
                        </p>
                        <time
                          className="text-small text-ink-muted"
                          dateTime={event.created_at}
                        >
                          {formatDate(event.created_at, language)}
                        </time>
                        {event.note ? (
                          <p className="break-words text-body text-ink">
                            {event.note}
                          </p>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <EmptyState
                  description={copy.noEventsDescription}
                  title={copy.noEventsTitle}
                />
              )}
            </section>
          </section>
        ) : null}

        {lookupState === "idle" && !ticket ? (
          <EmptyState
            description={copy.emptyDescription}
            title={copy.emptyTitle}
          />
        ) : null}
      </main>
    </div>
  );
}

function formatDate(value: string, language: UiLanguage): string {
  return new Intl.DateTimeFormat(DATE_LOCALES[language], {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
