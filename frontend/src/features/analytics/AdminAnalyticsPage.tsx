import { AlertTriangle, Clock3, FileText, ListChecks } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Button,
  Card,
  CardTitle,
  EmptyState,
  ErrorState,
  Skeleton,
  StatusBadge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui";
import {
  ApiError,
  getAdminAnalyticsSummary,
  getAdminTickets,
  type AdminTicketSummary,
  type AnalyticsSummary,
  type LoginResponse,
} from "@/lib/api";
import { getAnalyticsMessages } from "@/lib/analytics-i18n";
import { getOfficerMessages } from "@/lib/officer-i18n";
import type { UiLanguage } from "@/lib/i18n";

const ESCALATED_PAGE_SIZE = 100;
const DATE_LOCALES: Record<UiLanguage, string> = {
  en: "en-IN",
  hi: "hi-IN",
  gu: "gu-IN",
};

interface AdminAnalyticsPageProps {
  language: UiLanguage;
  session: LoginResponse;
  onLogout: () => void;
}

interface ChartDatum {
  name: string;
  count: number;
}

/** Present ticket analytics and the current escalated ticket queue. */
export function AdminAnalyticsPage({
  language,
  session,
  onLogout,
}: AdminAnalyticsPageProps) {
  const copy = getAnalyticsMessages(language);
  const officerCopy = getOfficerMessages(language);
  const { departments, statuses } = officerCopy;
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [escalatedTickets, setEscalatedTickets] = useState<AdminTicketSummary[]>([]);
  const [escalatedTotal, setEscalatedTotal] = useState(0);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    void Promise.all([
      getAdminAnalyticsSummary(session.access_token),
      getAdminTickets(session.access_token, {
        status: "ESCALATED",
        page: 1,
        pageSize: ESCALATED_PAGE_SIZE,
      }),
    ])
      .then(([analytics, escalated]) => {
        if (active) {
          setSummary(analytics);
          setEscalatedTickets(escalated.items);
          setEscalatedTotal(escalated.total);
          setLoadState("ready");
        }
      })
      .catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 401) {
          onLogout();
          return;
        }
        if (active) {
          setLoadState("error");
        }
      });
    return () => {
      active = false;
    };
  }, [onLogout, refreshKey, session.access_token]);

  const departmentData = useMemo((): ChartDatum[] => {
    if (!summary) {
      return [];
    }
    const counts = new Map<string, number>(
      summary.by_department.map((entry) => [entry.department_code, entry.count]),
    );
    return Object.entries(departments).map(([code, name]) => ({
      name,
      count: counts.get(code) ?? 0,
    }));
  }, [departments, summary]);

  const statusData = useMemo((): ChartDatum[] => {
    if (!summary) {
      return [];
    }
    const counts = new Map<string, number>(
      summary.by_status.map((entry) => [entry.value, entry.count]),
    );
    return Object.entries(statuses).map(([status, name]) => ({
      name,
      count: counts.get(status) ?? 0,
    }));
  }, [statuses, summary]);

  const languageData = useMemo(
    (): ChartDatum[] =>
      summary?.by_language.map(({ value, count }) => ({
        name: value.toUpperCase(),
        count,
      })) ?? [],
    [summary],
  );

  function retry(): void {
    setLoadState("loading");
    setRefreshKey((key) => key + 1);
  }

  const resolvedCount =
    summary?.by_status.find(({ value }) => value === "RESOLVED")?.count ?? 0;
  const openCount = Math.max(0, (summary?.total_tickets ?? 0) - resolvedCount);
  const averageResolution = summary?.average_resolution_time_hours;
  const formattedHours =
    averageResolution === null || averageResolution === undefined
      ? copy.noResolutionTime
      : copy.hoursValue.replace(
          "{hours}",
          new Intl.NumberFormat(DATE_LOCALES[language], {
            maximumFractionDigits: 1,
          }).format(averageResolution),
        );

  return (
    <div className="flex min-h-screen flex-col bg-background text-ink">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex w-full max-w-page flex-wrap items-center justify-between gap-4 px-4 py-4">
          <div>
            <p className="text-heading font-semibold">{officerCopy.serviceName}</p>
            <p className="text-small text-ink-muted">{copy.title}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              className="inline-flex min-h-touch items-center text-small font-semibold text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus focus-visible:ring-offset-2"
              to="/dashboard"
            >
              {copy.backToDashboard}
            </Link>
            <Button onClick={onLogout} variant="secondary">
              {copy.logout}
            </Button>
          </div>
        </div>
      </header>

      <main
        className="mx-auto grid w-full max-w-page flex-1 content-start gap-6 px-4 py-6"
        lang={language}
      >
        <header className="grid gap-2">
          <h1 className="text-display font-bold text-ink">{copy.title}</h1>
          <p className="max-w-chat text-body text-ink-muted">{copy.description}</p>
        </header>

        {loadState === "loading" ? (
          <section aria-label={copy.loading} className="grid gap-6">
            <Skeleton className="w-full" lines={2} />
            <Skeleton className="w-full" lines={5} />
          </section>
        ) : loadState === "error" || summary === null ? (
          <ErrorState
            message={copy.errorMessage}
            onRetry={retry}
            retryLabel={copy.retry}
            title={copy.errorTitle}
          />
        ) : (
          <>
            <section
              aria-label={copy.title}
              className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
            >
              <MetricCard
                description={copy.totalDescription}
                Icon={FileText}
                label={copy.totalTickets}
                value={formatCount(summary.total_tickets, language)}
              />
              <MetricCard
                description={copy.openDescription}
                Icon={ListChecks}
                label={copy.openTickets}
                value={formatCount(openCount, language)}
              />
              <MetricCard
                description={copy.escalatedDescription}
                Icon={AlertTriangle}
                label={copy.escalatedTickets}
                value={formatCount(escalatedTotal, language)}
              />
              <MetricCard
                description={copy.averageResolutionDescription}
                Icon={Clock3}
                label={copy.averageResolution}
                value={formattedHours}
              />
            </section>

            <section
              aria-label={copy.title}
              className="grid gap-6 lg:grid-cols-2"
            >
              <DistributionPanel
                description={copy.departmentTitle}
                hasData={summary.total_tickets > 0}
                rows={departmentData}
                title={copy.departmentTitle}
                categoryLabel={copy.category}
                countLabel={copy.count}
                noDataLabel={copy.noChartData}
                language={language}
              />
              <DistributionPanel
                description={copy.statusTitle}
                hasData={summary.total_tickets > 0}
                rows={statusData}
                title={copy.statusTitle}
                categoryLabel={copy.category}
                countLabel={copy.count}
                noDataLabel={copy.noChartData}
                language={language}
              />
              <DistributionPanel
                description={copy.languageTitle}
                hasData={languageData.length > 0}
                rows={languageData}
                title={copy.languageTitle}
                categoryLabel={copy.category}
                countLabel={copy.count}
                noDataLabel={copy.noChartData}
                language={language}
              />
            </section>

            <section className="grid gap-4" aria-labelledby="escalated-tickets-title">
              <h2
                className="text-title font-semibold text-ink"
                id="escalated-tickets-title"
              >
                {copy.escalatedListTitle}
              </h2>
              {escalatedTickets.length === 0 ? (
                <EmptyState
                  description={copy.noEscalatedDescription}
                  title={copy.noEscalatedTitle}
                />
              ) : (
                <Table aria-label={copy.escalatedListTitle}>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{copy.ticket}</TableHead>
                      <TableHead>{copy.department}</TableHead>
                      <TableHead>{copy.location}</TableHead>
                      <TableHead>{copy.filed}</TableHead>
                      <TableHead>{copy.escalationLevel}</TableHead>
                      <TableHead>{officerCopy.status}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {escalatedTickets.map((ticket) => (
                      <TableRow
                        className="border-s-2 border-s-danger"
                        key={ticket.public_id}
                      >
                        <TableCell className="font-mono font-semibold">
                          {ticket.public_id}
                        </TableCell>
                        <TableCell>
                          {officerCopy.departments[ticket.department] ??
                            ticket.department}
                        </TableCell>
                        <TableCell>{ticket.location}</TableCell>
                        <TableCell>{formatDate(ticket.created_at, language)}</TableCell>
                        <TableCell>{ticket.escalation_level}</TableCell>
                        <TableCell>
                          <StatusBadge
                            label={officerCopy.statuses.ESCALATED}
                            status="Escalated"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
              {escalatedTotal > escalatedTickets.length ? (
                <p className="text-small text-ink-muted">
                  {copy.showingRecent
                    .replace("{shown}", formatCount(escalatedTickets.length, language))
                    .replace("{total}", formatCount(escalatedTotal, language))}
                </p>
              ) : null}
            </section>
          </>
        )}
      </main>
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string;
  description: string;
  Icon: typeof FileText;
}

function MetricCard({ label, value, description, Icon }: MetricCardProps) {
  return (
    <Card className="grid content-start gap-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-small font-semibold text-ink-muted">{label}</h2>
        <Icon aria-hidden="true" className="icon text-primary" />
      </div>
      <p className="break-words text-title font-semibold text-ink">{value}</p>
      <p className="text-small text-ink-muted">{description}</p>
    </Card>
  );
}

interface DistributionPanelProps {
  title: string;
  description: string;
  rows: ChartDatum[];
  categoryLabel: string;
  countLabel: string;
  noDataLabel: string;
  hasData: boolean;
  language: UiLanguage;
}

function DistributionPanel({
  title,
  description,
  rows,
  categoryLabel,
  countLabel,
  noDataLabel,
  hasData,
  language,
}: DistributionPanelProps) {
  return (
    <Card className="grid min-w-0 content-start gap-4">
      <CardTitle>{title}</CardTitle>
      {hasData && rows.length > 0 ? (
        <div
          aria-label={description}
          className="h-chart min-w-0"
          role="img"
        >
          <ResponsiveContainer height="100%" width="100%">
            <BarChart
              accessibilityLayer
              data={rows}
              layout="vertical"
              margin={{ left: 0, right: 12 }}
            >
              <CartesianGrid
                horizontal={false}
                stroke="var(--color-border)"
              />
              <XAxis
                allowDecimals={false}
                axisLine={false}
                tick={{ fill: "var(--color-ink-muted)", fontSize: "var(--text-small)" }}
                tickLine={false}
                type="number"
              />
              <YAxis
                axisLine={false}
                dataKey="name"
                tick={{ fill: "var(--color-ink-muted)", fontSize: "var(--text-small)" }}
                tickLine={false}
                type="category"
                width="auto"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--color-surface)",
                  borderColor: "var(--color-border)",
                  borderRadius: "var(--radius-sm)",
                  color: "var(--color-ink)",
                }}
                formatter={(value) => [
                  formatCount(Number(value), language),
                  countLabel,
                ]}
              />
              <Bar dataKey="count" fill="var(--color-primary)">
                <LabelList dataKey="count" fill="var(--color-ink)" position="right" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="grid h-chart place-items-center text-center text-small text-ink-muted">
          {noDataLabel}
        </p>
      )}
      <Table aria-label={`${title} ${categoryLabel} ${countLabel}`}>
        <TableHeader>
          <TableRow>
            <TableHead>{categoryLabel}</TableHead>
            <TableHead>{countLabel}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length ? (
            rows.map((row) => (
              <TableRow key={row.name}>
                <TableCell>{row.name}</TableCell>
                <TableCell>{formatCount(row.count, language)}</TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell>{noDataLabel}</TableCell>
              <TableCell />
            </TableRow>
          )}
        </TableBody>
      </Table>
    </Card>
  );
}

function formatCount(value: number, language: UiLanguage): string {
  return new Intl.NumberFormat(DATE_LOCALES[language]).format(value);
}

function formatDate(value: string, language: UiLanguage): string {
  return new Intl.DateTimeFormat(DATE_LOCALES[language], {
    dateStyle: "medium",
  }).format(new Date(value));
}
