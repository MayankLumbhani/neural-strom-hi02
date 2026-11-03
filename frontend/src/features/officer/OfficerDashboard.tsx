import { ArrowLeft, LogOut, Menu, RotateCw, X } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  Button,
  Drawer,
  EmptyState,
  Input,
  Skeleton,
  StatusBadge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Textarea,
} from "@/components/ui";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import {
  ApiError,
  getAdminTicket,
  getAdminTickets,
  updateAdminTicketStatus,
  type AdminTicket,
  type AdminTicketStatus,
  type AdminTicketSummary,
  type LoginResponse,
} from "@/lib/api";
import { getOfficerMessages } from "@/lib/officer-i18n";
import type { UiLanguage } from "@/lib/i18n";

const PAGE_SIZE = 20;
const STATUS_VALUES: AdminTicketStatus[] = [
  "FILED",
  "ASSIGNED",
  "IN_PROGRESS",
  "RESOLVED",
  "ESCALATED",
];
const NEXT_STATUSES: Record<AdminTicketStatus, AdminTicketStatus[]> = {
  FILED: ["ASSIGNED", "ESCALATED"],
  ASSIGNED: ["IN_PROGRESS", "ESCALATED"],
  IN_PROGRESS: ["RESOLVED", "ESCALATED"],
  RESOLVED: [],
  ESCALATED: ["IN_PROGRESS", "RESOLVED"],
};
const DISPLAY_STATUSES: Record<
  AdminTicketStatus,
  "Filed" | "Assigned" | "In Progress" | "Resolved" | "Escalated"
> = {
  FILED: "Filed",
  ASSIGNED: "Assigned",
  IN_PROGRESS: "In Progress",
  RESOLVED: "Resolved",
  ESCALATED: "Escalated",
};
const DATE_LOCALES: Record<UiLanguage, string> = {
  en: "en-IN",
  hi: "hi-IN",
  gu: "gu-IN",
};

interface OfficerDashboardProps {
  language: UiLanguage;
  onLanguageChange: (language: UiLanguage) => void;
  session: LoginResponse;
  onLogout: () => void;
}

/** Show a scoped ticket queue and let staff update ticket status. */
export function OfficerDashboard({
  language,
  onLanguageChange,
  session,
  onLogout,
}: OfficerDashboardProps) {
  const copy = getOfficerMessages(language);
  const [tickets, setTickets] = useState<AdminTicketSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<AdminTicketStatus | "">("");
  const [searchInput, setSearchInput] = useState("");
  const [dateFromInput, setDateFromInput] = useState("");
  const [dateToInput, setDateToInput] = useState("");
  const [filters, setFilters] = useState({ search: "", dateFrom: "", dateTo: "" });
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedTicket, setSelectedTicket] = useState<AdminTicket | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<AdminTicketSummary | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(false);
  const [nextStatus, setNextStatus] = useState<AdminTicketStatus | "">("");
  const [note, setNote] = useState("");
  const [isPublic, setIsPublic] = useState(true);
  const [saving, setSaving] = useState(false);
  const [updateError, setUpdateError] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  useEffect(() => {
    let active = true;
    void getAdminTickets(session.access_token, {
      status: statusFilter || undefined,
      search: filters.search || undefined,
      dateFrom: filters.dateFrom || undefined,
      dateTo: filters.dateTo || undefined,
      page,
      pageSize: PAGE_SIZE,
    })
      .then((result) => {
        if (active) {
          setTickets(result.items);
          setTotal(result.total);
        }
      })
      .catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 401) {
          onLogout();
          return;
        }
        if (active) {
          setLoadError(true);
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [filters, onLogout, page, refreshKey, session.access_token, statusFilter]);

  async function openTicket(summary: AdminTicketSummary): Promise<void> {
    setSelectedSummary(summary);
    setSelectedTicket(null);
    setDetailLoading(true);
    setDetailError(false);
    setUpdateError(false);
    setUpdateSuccess(false);
    setNote("");
    try {
      const ticket = await getAdminTicket(session.access_token, summary.public_id);
      setSelectedTicket(ticket);
      setNextStatus(NEXT_STATUSES[ticket.status][0] ?? "");
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout();
      } else {
        setDetailError(true);
      }
    } finally {
      setDetailLoading(false);
    }
  }

  function applyFilters(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    setLoading(true);
    setLoadError(false);
    setPage(1);
    setFilters({
      search: searchInput.trim(),
      dateFrom: dateFromInput,
      dateTo: dateToInput,
    });
  }

  async function saveUpdate(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!selectedTicket || !nextStatus || !note.trim()) {
      return;
    }
    setSaving(true);
    setUpdateError(false);
    setUpdateSuccess(false);
    try {
      const updated = await updateAdminTicketStatus(
        session.access_token,
        selectedTicket.public_id,
        { status: nextStatus, note: note.trim(), is_public: isPublic },
      );
      setSelectedTicket(updated);
      setSelectedSummary(updated);
      setNextStatus(NEXT_STATUSES[updated.status][0] ?? "");
      setNote("");
      setUpdateSuccess(true);
      setLoading(true);
      setRefreshKey((key) => key + 1);
    } catch (error: unknown) {
      if (error instanceof ApiError && error.status === 401) {
        onLogout();
      } else {
        setUpdateError(true);
      }
    } finally {
      setSaving(false);
    }
  }

  function closeDrawer(): void {
    setSelectedSummary(null);
    setSelectedTicket(null);
    setDetailError(false);
  }

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const canUpdate =
    selectedTicket !== null && NEXT_STATUSES[selectedTicket.status].length > 0;

  return (
    <div className="flex min-h-screen flex-col bg-background text-ink">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex w-full max-w-page flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div className="flex items-center gap-3">
            <Button
              aria-controls="officer-navigation"
              aria-expanded={sidebarOpen}
              aria-label={sidebarOpen ? copy.closeMenu : copy.menu}
              className="lg:hidden"
              onClick={() => setSidebarOpen((open) => !open)}
              variant="ghost"
            >
              {sidebarOpen ? (
                <X aria-hidden="true" className="icon" />
              ) : (
                <Menu aria-hidden="true" className="icon" />
              )}
            </Button>
            <p className="text-heading font-semibold">
              {copy.serviceName}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <LanguageSwitcher
              language={language}
              label={copy.languageLabel}
              onLanguageChange={onLanguageChange}
            />
            <Link
              className="inline-flex min-h-touch items-center gap-2 text-small font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
              to="/"
            >
              <ArrowLeft aria-hidden="true" className="icon" />
              {copy.backToChat}
            </Link>
          </div>
        </div>
      </header>

      <main
        className="mx-auto grid w-full max-w-page flex-1 content-start gap-6 px-4 py-6 lg:grid-cols-4"
        lang={language}
      >
        <aside
          className={`grid content-start gap-4 rounded-card border bg-surface p-4 lg:col-span-1 ${sidebarOpen ? "" : "max-lg:hidden"}`}
          id="officer-navigation"
        >
          <div className="grid gap-1">
            <p className="text-small text-ink-muted">{copy.signedInAs}</p>
            <p className="break-words font-semibold">
              {session.department ?? copy.administrator}
            </p>
          </div>
          <nav aria-label={copy.dashboardTitle} className="grid gap-2">
            <a
              className="min-h-touch content-center rounded-sm px-3 font-semibold text-primary hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
              href="#ticket-queue"
              onClick={() => setSidebarOpen(false)}
            >
              {copy.ticketQueue}
            </a>
            <Link
              className="min-h-touch content-center rounded-sm px-3 font-semibold text-primary hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
              onClick={() => setSidebarOpen(false)}
              to="/status"
            >
              {copy.statusPage}
            </Link>
            {session.role === "ADMIN" ? (
              <Link
                className="min-h-touch content-center rounded-sm px-3 font-semibold text-primary hover:bg-surface-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
                onClick={() => setSidebarOpen(false)}
                to="/analytics"
              >
                {copy.analytics}
              </Link>
            ) : null}
          </nav>
          <Button onClick={onLogout} variant="secondary">
            <LogOut aria-hidden="true" className="icon" />
            {copy.logout}
          </Button>
        </aside>

        <section className="grid content-start gap-6 lg:col-span-3">
          <h1 className="text-display font-bold text-ink">{copy.dashboardTitle}</h1>
          <form
            className="grid items-end gap-4 rounded-card border bg-surface p-4 md:grid-cols-2 lg:grid-cols-5"
            onSubmit={applyFilters}
          >
            <Input
              label={copy.search}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder={copy.searchPlaceholder}
              value={searchInput}
            />
            <label className="grid gap-2 font-semibold text-ink">
              <span>{copy.statusFilter}</span>
              <select
                className="min-h-touch w-full rounded-sm border border-strong bg-surface px-3 text-body text-ink focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
                onChange={(event) => {
                  setLoading(true);
                  setLoadError(false);
                  setStatusFilter(event.target.value as AdminTicketStatus | "");
                  setPage(1);
                }}
                value={statusFilter}
              >
                <option value="">{copy.allStatuses}</option>
                {STATUS_VALUES.map((status) => (
                  <option key={status} value={status}>
                    {copy.statuses[status]}
                  </option>
                ))}
              </select>
            </label>
            <Input
              label={copy.dateFrom}
              onChange={(event) => setDateFromInput(event.target.value)}
              type="date"
              value={dateFromInput}
            />
            <Input
              label={copy.dateTo}
              min={dateFromInput || undefined}
              onChange={(event) => setDateToInput(event.target.value)}
              type="date"
              value={dateToInput}
            />
            <Button type="submit">{copy.applyFilters}</Button>
          </form>

          {loading ? (
          <section aria-label={copy.loading} className="grid gap-3">
            <Skeleton className="w-full" lines={6} />
          </section>
        ) : loadError ? (
          <section className="grid justify-items-start gap-3 rounded-card border border-danger bg-surface p-4" role="alert">
            <p className="text-body text-ink">{copy.loadError}</p>
            <Button
              onClick={() => {
                setLoading(true);
                setLoadError(false);
                setRefreshKey((key) => key + 1);
              }}
              variant="secondary"
            >
              <RotateCw aria-hidden="true" className="icon" />
              {copy.retry}
            </Button>
          </section>
        ) : tickets.length === 0 ? (
          <EmptyState description={copy.emptyDescription} title={copy.emptyTitle} />
        ) : (
          <>
            <Table id="ticket-queue">
              <TableHeader>
                <TableRow>
                  <TableHead>{copy.ticket}</TableHead>
                  <TableHead>{copy.department}</TableHead>
                  <TableHead>{copy.status}</TableHead>
                  <TableHead>{copy.location}</TableHead>
                  <TableHead>{copy.filed}</TableHead>
                  <TableHead>{copy.escalation}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tickets.map((ticket) => (
                  <TableRow
                    className={ticket.status === "ESCALATED" ? "border-s-2 border-s-danger" : undefined}
                    key={ticket.public_id}
                  >
                    <TableCell>
                      <button
                        aria-label={`${copy.openDetails}: ${ticket.public_id}`}
                        className="min-h-touch font-mono font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
                        onClick={() => void openTicket(ticket)}
                        type="button"
                      >
                        {ticket.public_id}
                      </button>
                    </TableCell>
                    <TableCell>{copy.departments[ticket.department] ?? ticket.department}</TableCell>
                    <TableCell>
                      <StatusBadge
                        label={copy.statuses[ticket.status]}
                        status={DISPLAY_STATUSES[ticket.status]}
                      />
                    </TableCell>
                    <TableCell>{ticket.location}</TableCell>
                    <TableCell>{formatDate(ticket.created_at, language)}</TableCell>
                    <TableCell>{ticket.escalation_level}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <nav aria-label={`${copy.page} ${page} of ${pageCount}`} className="flex flex-wrap items-center justify-between gap-3">
              <span className="text-small text-ink-muted">
                {copy.page} {page} / {pageCount} · {total}
              </span>
              <div className="flex gap-2">
                <Button
                  disabled={page <= 1}
                  onClick={() => {
                    setLoading(true);
                    setPage((current) => current - 1);
                  }}
                  variant="secondary"
                >
                  {copy.previous}
                </Button>
                <Button
                  disabled={page >= pageCount}
                  onClick={() => {
                    setLoading(true);
                    setPage((current) => current + 1);
                  }}
                  variant="secondary"
                >
                  {copy.next}
                </Button>
              </div>
            </nav>
          </>
        )}
        </section>
      </main>

      <Drawer
        closeLabel={copy.close}
        onClose={closeDrawer}
        open={selectedSummary !== null}
        title={`${copy.detailTitle}${selectedSummary ? ` · ${selectedSummary.public_id}` : ""}`}
      >
        {detailLoading ? (
          <Skeleton className="w-full" lines={6} />
        ) : detailError ? (
          <section className="grid justify-items-start gap-3" role="alert">
            <p className="text-body text-danger">{copy.loadError}</p>
            {selectedSummary ? (
              <Button onClick={() => void openTicket(selectedSummary)} variant="secondary">
                {copy.retry}
              </Button>
            ) : null}
          </section>
        ) : selectedTicket ? (
          <div className="grid gap-6">
            <dl className="grid gap-3 sm:grid-cols-2">
              <DetailField
                label={copy.department}
                value={copy.departments[selectedTicket.department] ?? selectedTicket.department}
              />
              <DetailField label={copy.location} value={selectedTicket.location} />
              <DetailField label={copy.language} value={selectedTicket.language} />
              <div className="grid gap-1">
                <dt className="text-small font-semibold text-ink-muted">{copy.status}</dt>
                <dd>
                  <StatusBadge
                    label={copy.statuses[selectedTicket.status]}
                    status={DISPLAY_STATUSES[selectedTicket.status]}
                  />
                </dd>
              </div>
            </dl>
            <section className="grid gap-2">
              <h3 className="text-heading font-semibold">{copy.complaint}</h3>
              <p
                className="whitespace-pre-wrap break-words rounded-card border bg-surface p-4 text-body"
                lang={selectedTicket.language}
              >
                {selectedTicket.complaint_text}
              </p>
            </section>
            <section className="grid gap-3">
              <h3 className="text-heading font-semibold">{copy.timeline}</h3>
              {selectedTicket.events.length === 0 ? (
                <p className="text-small text-ink-muted">{copy.noEvents}</p>
              ) : (
                <ol className="grid gap-3 border-s-2 ps-4">
                  {selectedTicket.events.map((event) => (
                    <li className="grid gap-1" key={event.id}>
                      <p className="font-semibold">
                        {event.from_status
                          ? `${copy.statuses[event.from_status]} → `
                          : ""}
                        {copy.statuses[event.to_status]}
                      </p>
                      <p className="text-small text-ink-muted">
                        {formatDate(event.created_at, language)}
                        {event.is_public ? ` · ${copy.publicNote}` : ` · ${copy.privateNote}`}
                      </p>
                      {event.note ? <p className="break-words text-body">{event.note}</p> : null}
                    </li>
                  ))}
                </ol>
              )}
            </section>
            {canUpdate ? (
              <form className="grid gap-4 border-t pt-5" onSubmit={(event) => void saveUpdate(event)}>
                <h3 className="text-heading font-semibold">{copy.updateStatus}</h3>
                <label className="grid gap-2 font-semibold text-ink">
                  <span>{copy.status}</span>
                  <select
                    className="min-h-touch w-full rounded-sm border border-strong bg-surface px-3 text-body text-ink focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
                    onChange={(event) => setNextStatus(event.target.value as AdminTicketStatus)}
                    required
                    value={nextStatus}
                  >
                    {NEXT_STATUSES[selectedTicket.status].map((status) => (
                      <option key={status} value={status}>
                        {copy.statuses[status]}
                      </option>
                    ))}
                  </select>
                </label>
                <Textarea
                  label={copy.note}
                  maxLength={2000}
                  onChange={(event) => setNote(event.target.value)}
                  placeholder={copy.notePlaceholder}
                  required
                  value={note}
                />
                <label className="flex min-h-touch items-center gap-3 text-body">
                  <input
                    checked={isPublic}
                    className="size-5 accent-primary focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
                    onChange={(event) => setIsPublic(event.target.checked)}
                    type="checkbox"
                  />
                  {copy.publicNote}
                </label>
                {updateError ? (
                  <p className="text-small text-danger" role="alert">{copy.updateError}</p>
                ) : null}
                {updateSuccess ? (
                  <p className="text-small text-primary" role="status">{copy.updateSuccess}</p>
                ) : null}
                <Button disabled={!nextStatus || !note.trim()} loading={saving} type="submit">
                  {saving ? copy.saving : copy.saveUpdate}
                </Button>
              </form>
            ) : null}
          </div>
        ) : null}
      </Drawer>
    </div>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1">
      <dt className="text-small font-semibold text-ink-muted">{label}</dt>
      <dd className="break-words text-body">{value}</dd>
    </div>
  );
}

function formatDate(value: string, language: UiLanguage): string {
  return new Intl.DateTimeFormat(DATE_LOCALES[language], {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
