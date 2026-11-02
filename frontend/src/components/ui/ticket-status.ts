export const TICKET_STATUSES = [
  "Filed",
  "Assigned",
  "In Progress",
  "Resolved",
  "Escalated",
] as const;

export type TicketStatus = (typeof TICKET_STATUSES)[number];
