import { getApiBaseUrl } from "@/lib/config";

export interface ChatMessageRequest {
  text: string;
  conversation_id?: string | null;
}

export interface ChatReply {
  text: string;
  quick_replies: string[];
}

export interface ChatTicketSummary {
  ticket_id: string;
  department: string;
  status: string;
}

export interface ChatMessageResponse {
  conversation_id: string;
  state: string;
  language: string;
  language_tier: number;
  reply: ChatReply;
  ticket: ChatTicketSummary | null;
}

export interface ReadinessResponse {
  status: string;
  db: string;
  model: string;
  model_error: string | null;
}

export interface PublicTicketEvent {
  from_status: string | null;
  to_status: string;
  note: string | null;
  created_at: string;
}

export type TicketStatusCode =
  | "FILED"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "RESOLVED"
  | "ESCALATED";

export interface PublicTicketResponse {
  public_id: string;
  language: string;
  status_code: TicketStatusCode;
  status: string;
  department: string;
  location: string;
  created_at: string;
  updated_at: string;
  public_events: PublicTicketEvent[];
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
  role: "ADMIN" | "DEPARTMENT_OFFICER";
  department: string | null;
}

export type AdminTicketStatus =
  | "FILED"
  | "ASSIGNED"
  | "IN_PROGRESS"
  | "RESOLVED"
  | "ESCALATED";

export interface AdminTicketSummary {
  public_id: string;
  status: AdminTicketStatus;
  department: string;
  location: string;
  language: string;
  created_at: string;
  status_changed_at: string;
  escalation_level: number;
}

export interface AdminTicketEvent {
  id: string;
  from_status: AdminTicketStatus | null;
  to_status: AdminTicketStatus;
  actor_type: string;
  note: string | null;
  is_public: boolean;
  created_at: string;
}

export interface AdminTicket extends AdminTicketSummary {
  complaint_text: string;
  contact_phone: string | null;
  resolved_at: string | null;
  events: AdminTicketEvent[];
}

export interface AdminTicketList {
  items: AdminTicketSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface AnalyticsSummary {
  total_tickets: number;
  by_department: {
    department_code: string;
    department_name: string;
    count: number;
  }[];
  by_status: { value: AdminTicketStatus; count: number }[];
  by_language: { value: string; count: number }[];
  average_resolution_time_hours: number | null;
}

interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
  request_id?: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly requestId: string | undefined,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const body: unknown = await response.json();
    const errorBody = isApiErrorBody(body) ? body : {};
    throw new ApiError(
      errorBody.error?.message ?? "The request could not be completed.",
      response.status,
      errorBody.error?.code ?? "HTTP_ERROR",
      errorBody.request_id,
    );
  }

  return (await response.json()) as T;
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  if (!isRecord(value)) {
    return false;
  }

  if (value.request_id !== undefined && typeof value.request_id !== "string") {
    return false;
  }

  if (value.error === undefined) {
    return true;
  }

  if (!isRecord(value.error)) {
    return false;
  }

  return (
    (value.error.code === undefined || typeof value.error.code === "string") &&
    (value.error.message === undefined ||
      typeof value.error.message === "string") &&
    (value.error.details === undefined || isRecord(value.error.details))
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function sendChatMessage(
  payload: ChatMessageRequest,
): Promise<ChatMessageResponse> {
  return requestJson<ChatMessageResponse>("/api/v1/chat/messages", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getBackendReadiness(): Promise<ReadinessResponse> {
  return requestJson<ReadinessResponse>("/ready");
}

export function getTicketStatus(publicId: string): Promise<PublicTicketResponse> {
  return requestJson<PublicTicketResponse>(
    `/api/v1/tickets/${encodeURIComponent(publicId)}`,
  );
}

export function loginStaff(
  username: string,
  password: string,
): Promise<LoginResponse> {
  return requestJson<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function getAdminTickets(
  accessToken: string,
  filters: {
    status?: AdminTicketStatus;
    search?: string;
    dateFrom?: string;
    dateTo?: string;
    page: number;
    pageSize: number;
  },
): Promise<AdminTicketList> {
  const query = new URLSearchParams({
    page: String(filters.page),
    page_size: String(filters.pageSize),
  });
  if (filters.status) {
    query.set("status", filters.status);
  }
  if (filters.search) {
    query.set("q", filters.search);
  }
  if (filters.dateFrom) {
    query.set("date_from", filters.dateFrom);
  }
  if (filters.dateTo) {
    query.set("date_to", filters.dateTo);
  }
  return requestJson<AdminTicketList>(`/api/v1/admin/tickets?${query}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function getAdminTicket(
  accessToken: string,
  publicId: string,
): Promise<AdminTicket> {
  return requestJson<AdminTicket>(
    `/api/v1/admin/tickets/${encodeURIComponent(publicId)}`,
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
}

export function updateAdminTicketStatus(
  accessToken: string,
  publicId: string,
  update: { status: AdminTicketStatus; note: string; is_public: boolean },
): Promise<AdminTicket> {
  return requestJson<AdminTicket>(
    `/api/v1/admin/tickets/${encodeURIComponent(publicId)}/status`,
    {
      method: "PATCH",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: JSON.stringify(update),
    },
  );
}

export function getAdminAnalyticsSummary(
  accessToken: string,
): Promise<AnalyticsSummary> {
  return requestJson<AnalyticsSummary>("/api/v1/admin/analytics/summary", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}
