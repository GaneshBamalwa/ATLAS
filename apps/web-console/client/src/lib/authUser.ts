const ACTIVE_USER_KEY = "atlas_active_user_id";

export function getActiveUserId(): string {
  if (typeof window === "undefined") return "default_user";
  return localStorage.getItem(ACTIVE_USER_KEY) || "default_user";
}

export function setActiveUserId(userId: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACTIVE_USER_KEY, userId);
}

export function syncUserIdFromUrl(): void {
  if (typeof window === "undefined") return;

  const url = new URL(window.location.href);
  const userId = url.searchParams.get("user_id");

  if (!userId) return;

  setActiveUserId(userId);

  // Remove auth callback params to keep URL clean.
  url.searchParams.delete("user_id");
  url.searchParams.delete("service");
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}
