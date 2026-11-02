import { AlertCircle, Inbox, RotateCw } from "lucide-react";
import { useId, type ReactNode } from "react";
import { Button } from "@/components/ui/button";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  const titleId = useId();

  return (
    <section
      aria-labelledby={titleId}
      className="grid justify-items-center gap-3 rounded-card border border-dashed bg-surface p-6 text-center"
    >
      <Inbox aria-hidden="true" className="icon text-ink-muted" />
      <h2
        className="text-heading font-semibold text-ink"
        id={titleId}
      >
        {title}
      </h2>
      <p className="max-w-chat text-body text-ink-muted">{description}</p>
      {action}
    </section>
  );
}

export function ErrorState({
  title,
  message,
  retryLabel,
  onRetry,
}: {
  title: string;
  message: string;
  retryLabel: string;
  onRetry: () => void;
}) {
  const titleId = useId();

  return (
    <section
      aria-labelledby={titleId}
      className="grid justify-items-start gap-3 rounded-card border border-danger bg-surface p-4"
      role="alert"
    >
      <h2
        className="flex items-center gap-2 text-heading font-semibold text-danger"
        id={titleId}
      >
        <AlertCircle aria-hidden="true" className="icon" />
        {title}
      </h2>
      <p className="text-body text-ink">{message}</p>
      <Button onClick={onRetry} variant="secondary">
        <RotateCw aria-hidden="true" className="icon" />
        {retryLabel}
      </Button>
    </section>
  );
}

export function Skeleton({
  className,
  lines = 1,
}: {
  className?: string;
  lines?: number;
}) {
  return (
    <div
      aria-hidden="true"
      className="grid gap-3"
      data-testid="skeleton"
    >
      {Array.from({ length: Math.max(1, lines) }, (_, index) => (
        <div
          className={`h-4 animate-pulse rounded-sm bg-surface-muted ${className ?? ""}`}
          key={index}
        />
      ))}
    </div>
  );
}
