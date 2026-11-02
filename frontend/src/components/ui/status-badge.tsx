import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Clock3,
  ClipboardCheck,
} from "lucide-react";
import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import type { TicketStatus } from "@/components/ui/ticket-status";

export type { TicketStatus } from "@/components/ui/ticket-status";

const statusDetails = {
  Filed: {
    className: "bg-filed-bg text-filed-fg",
    Icon: CircleDot,
  },
  Assigned: {
    className: "bg-assigned-bg text-assigned-fg",
    Icon: ClipboardCheck,
  },
  "In Progress": {
    className: "bg-progress-bg text-progress-fg",
    Icon: Clock3,
  },
  Resolved: {
    className: "bg-resolved-bg text-resolved-fg",
    Icon: CheckCircle2,
  },
  Escalated: {
    className: "bg-escalated-bg text-escalated-fg",
    Icon: AlertTriangle,
  },
} satisfies Record<
  TicketStatus,
  { className: string; Icon: typeof CircleDot }
>;

export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: TicketStatus;
  label?: string;
}

export function StatusBadge({
  status,
  label = status,
  className,
  ...props
}: StatusBadgeProps) {
  const { className: statusClassName, Icon } = statusDetails[status];

  return (
    <span
      className={cn(
        "inline-flex min-h-touch items-center gap-2 rounded-pill px-3 py-1 text-small font-semibold",
        statusClassName,
        className,
      )}
      {...props}
    >
      <Icon aria-hidden="true" className="icon" />
      <span>{label}</span>
    </span>
  );
}
