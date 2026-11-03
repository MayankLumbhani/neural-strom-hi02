import { Check, Copy } from "lucide-react";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/ui/status-badge";
import type { TicketStatus } from "@/components/ui/ticket-status";

export interface TicketCardProps {
  ticketId: string;
  department: string;
  location?: string;
  filedAt?: string;
  status: TicketStatus;
  statusLabel: string;
  valueLanguage?: string;
  labels: {
    title: string;
    department: string;
    location: string;
    filedAt: string;
    copyId: string;
    copied: string;
    copyFailed: string;
  };
}

export function TicketCard({
  ticketId,
  department,
  location,
  filedAt,
  status,
  statusLabel,
  valueLanguage,
  labels,
}: TicketCardProps) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">(
    "idle",
  );

  async function copyTicketId(): Promise<void> {
    try {
      await navigator.clipboard.writeText(ticketId);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
  }

  return (
    <Card className="relative overflow-hidden border-l-4 border-l-accent shadow-raised">
      <CardHeader>
        <CardTitle>{labels.title}</CardTitle>
        <p className="font-mono text-title font-semibold text-ink" dir="ltr">
          {ticketId}
        </p>
      </CardHeader>
      <dl className="grid gap-3 border-y border-dashed py-4">
        <TicketDetail
          label={labels.department}
          value={department}
          valueLanguage={valueLanguage}
        />
        {location ? (
          <TicketDetail
            label={labels.location}
            value={location}
            valueLanguage={valueLanguage}
          />
        ) : null}
        {filedAt ? <TicketDetail label={labels.filedAt} value={filedAt} /> : null}
      </dl>
      <CardContent className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <StatusBadge
          label={statusLabel}
          lang={valueLanguage}
          status={status}
        />
        <Button onClick={copyTicketId} variant="secondary">
          {copyState === "copied" ? (
            <Check aria-hidden="true" className="icon" />
          ) : (
            <Copy aria-hidden="true" className="icon" />
          )}
          {copyState === "copied" ? labels.copied : labels.copyId}
        </Button>
      </CardContent>
      <p
        aria-live="polite"
        className="text-small text-danger"
        role={copyState === "failed" ? "alert" : undefined}
      >
        {copyState === "failed" ? labels.copyFailed : ""}
      </p>
    </Card>
  );
}

function TicketDetail({
  label,
  value,
  valueLanguage,
}: {
  label: string;
  value: string;
  valueLanguage?: string;
}) {
  return (
    <div className="grid gap-1">
      <dt className="text-small text-ink-muted">{label}</dt>
      <dd className="break-words text-body text-ink" lang={valueLanguage}>
        {value}
      </dd>
    </div>
  );
}
