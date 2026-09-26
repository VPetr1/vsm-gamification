/**
 * The countdown never trusts the device clock: the server sends both `deadline` and `server_time`,
 * so the time left at the moment of the response is `deadline - server_time`. After that the client
 * only measures elapsed time with a monotonic clock (performance.now()).
 */
export function remainingAtReceiptMs(deadline: string | null, serverTime: string): number | null {
  if (!deadline) return null;
  const left = Date.parse(deadline) - Date.parse(serverTime);
  return Number.isFinite(left) ? Math.max(0, left) : null;
}

export function remainingNowMs(remainingAtReceipt: number, receivedAtPerf: number, nowPerf: number): number {
  return Math.max(0, remainingAtReceipt - (nowPerf - receivedAtPerf));
}

export function formatSeconds(ms: number): string {
  return String(Math.ceil(ms / 1000));
}

const dateTimeFormat = new Intl.DateTimeFormat("ru-RU", {
  day: "numeric",
  month: "long",
  hour: "2-digit",
  minute: "2-digit",
});

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "" : dateTimeFormat.format(date);
}

export function signed(delta: number): string {
  if (delta > 0) return `+${delta}`;
  if (delta < 0) return `−${Math.abs(delta)}`;
  return "0";
}
