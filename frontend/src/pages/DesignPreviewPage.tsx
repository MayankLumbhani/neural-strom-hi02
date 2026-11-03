import { useId, useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  ChatBubble,
  Drawer,
  EmptyState,
  ErrorState,
  Input,
  QuickReply,
  Skeleton,
  StatusBadge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Textarea,
  TicketCard,
} from "@/components/ui";
import { TICKET_STATUSES } from "@/components/ui/ticket-status";
import {
  getDesignMessages,
  UI_LANGUAGES,
  type UiLanguage,
} from "@/lib/i18n";

export function DesignPreviewPage() {
  const [language, setLanguage] = useState<UiLanguage>("en");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const copy = getDesignMessages(language);

  return (
    <main
      className="mx-auto grid max-w-page gap-6 px-4 py-8 text-ink"
      lang={language}
    >
      <header className="grid gap-3">
        <p className="text-small font-semibold text-ink-muted">
          {copy.previewOnly}
        </p>
        <h1 className="text-display font-bold">{copy.title}</h1>
        <p className="text-body text-ink-muted">{copy.description}</p>
        <fieldset className="grid gap-2">
          <legend className="font-semibold">{copy.languageLabel}</legend>
          <div className="flex flex-wrap gap-2" role="group">
            {UI_LANGUAGES.map(({ code, label }) => (
              <Button
                aria-pressed={language === code}
                key={code}
                onClick={() => {
                  setLanguage(code);
                  setNotice("");
                }}
                variant={language === code ? "primary" : "secondary"}
              >
                {label}
              </Button>
            ))}
          </div>
        </fieldset>
      </header>

      <DemoSection title={copy.buttons}>
        <div className="flex flex-wrap gap-3">
          <Button>{copy.primary}</Button>
          <Button variant="secondary">{copy.secondary}</Button>
          <Button variant="ghost">{copy.ghost}</Button>
          <Button variant="danger">{copy.danger}</Button>
          <Button loading>{copy.loading}</Button>
        </div>
      </DemoSection>

      <DemoSection title={copy.forms}>
        <div className="grid gap-4 md:grid-cols-2">
          <Input
            defaultValue={copy.fieldValue}
            label={copy.fieldLabel}
            readOnly
          />
          <Input
            defaultValue=""
            error={copy.fieldError}
            label={copy.fieldLabel}
          />
          <Textarea
            defaultValue={copy.textAreaValue}
            label={copy.textAreaLabel}
            rows={3}
          />
        </div>
      </DemoSection>

      <DemoSection title={copy.card}>
        <Card>
          <CardHeader>
            <CardTitle>{copy.cardTitle}</CardTitle>
          </CardHeader>
          <CardContent>{copy.cardText}</CardContent>
        </Card>
      </DemoSection>

      <DemoSection title={copy.status}>
        <div className="flex flex-wrap gap-3">
          {TICKET_STATUSES.map((status) => (
            <StatusBadge
              key={status}
              label={copy.statuses[status]}
              status={status}
            />
          ))}
        </div>
      </DemoSection>

      <DemoSection title={copy.chat}>
        <div className="grid gap-3">
          <ChatBubble
            language={language}
            message={copy.citizenMessage}
            sender="citizen"
          />
          <ChatBubble
            language={language}
            message={copy.botMessage}
            sender="bot"
          />
        </div>
      </DemoSection>

      <DemoSection title={copy.quickReplies}>
        <div className="flex flex-wrap gap-3">
          {[copy.quickReplyOne, copy.quickReplyTwo].map((reply) => (
            <QuickReply
              key={reply}
              label={reply}
              onSelect={(selectedReply) =>
                setNotice(`${copy.selectedReply}: ${selectedReply}`)
              }
            />
          ))}
        </div>
      </DemoSection>

      <DemoSection title={copy.ticket}>
        <TicketCard
          department={copy.departmentValue}
          filedAt={copy.filedAtValue}
          labels={{
            title: copy.ticket,
            department: copy.department,
            location: copy.location,
            filedAt: copy.filedAt,
            copyId: copy.copyId,
            copied: copy.copied,
            copyFailed: copy.copyFailed,
          }}
          location={copy.locationValue}
          status="Filed"
          statusLabel={copy.statuses.Filed}
          ticketId="FMC-261103-AB12"
        />
      </DemoSection>

      <DemoSection title={copy.table}>
        <Table>
          <caption className="sr-only">{copy.table}</caption>
          <TableHeader>
            <TableRow>
              <TableHead>{copy.ticketId}</TableHead>
              <TableHead>{copy.department}</TableHead>
              <TableHead>{copy.status}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell dir="ltr">FMC-261103-AB12</TableCell>
              <TableCell>{copy.departmentValue}</TableCell>
              <TableCell>{copy.statuses.Filed}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </DemoSection>

      <DemoSection title={copy.drawer}>
        <Button onClick={() => setDrawerOpen(true)} variant="secondary">
          {copy.openDrawer}
        </Button>
        <Drawer
          closeLabel={copy.closeDrawer}
          onClose={() => setDrawerOpen(false)}
          open={drawerOpen}
          title={copy.drawer}
        >
          <p>{copy.drawerText}</p>
        </Drawer>
      </DemoSection>

      <DemoSection title={copy.emptyState}>
        <EmptyState
          action={
            <Button onClick={() => setNotice(copy.previewOnly)}>
              {copy.emptyAction}
            </Button>
          }
          description={copy.emptyDescription}
          title={copy.emptyTitle}
        />
      </DemoSection>

      <DemoSection title={copy.errorState}>
        <ErrorState
          message={copy.errorMessage}
          onRetry={() => setNotice(copy.retryNotice)}
          retryLabel={copy.retry}
          title={copy.errorTitle}
        />
      </DemoSection>

      <DemoSection title={copy.loadingState}>
        <div className="grid gap-4">
          <Skeleton className="w-full" lines={1} />
          <Skeleton className="w-2/3" lines={3} />
        </div>
      </DemoSection>

      <p aria-live="polite" className="min-h-6 text-small text-ink-muted">
        {notice}
      </p>
    </main>
  );
}

function DemoSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  const titleId = useId();

  return (
    <section
      aria-labelledby={titleId}
      className="grid gap-3 border-t pt-4"
    >
      <h2 className="text-title font-semibold" id={titleId}>
        {title}
      </h2>
      {children}
    </section>
  );
}
