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

export interface PublicTicketResponse {
  public_id: string;
  status: string;
  department: string;
  location: string;
  created_at: string;
  updated_at: string;
  public_events: PublicTicketEvent[];
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
