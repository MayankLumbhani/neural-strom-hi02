export function getApiBaseUrl(): string {
  const configuredUrl = import.meta.env.VITE_API_BASE_URL?.trim();
  if (!configuredUrl) {
    throw new Error(
      "VITE_API_BASE_URL is required. Copy frontend/.env.example to frontend/.env.",
    );
  }

  return configuredUrl.replace(/\/+$/, "");
}
