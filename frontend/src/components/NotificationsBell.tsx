import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { getNotifications, markAllNotificationsRead, markNotificationRead } from "../api/endpoints";
import type { Notifications } from "../api/types";
import { formatDateTime } from "../utils/time";

export function NotificationsBell() {
  const [data, setData] = useState<Notifications | null>(null);
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const panelRef = useRef<HTMLDivElement>(null);

  const load = useCallback(() => {
    getNotifications()
      .then((d) => {
        setData(d);
        setFailed(false);
      })
      .catch(() => setFailed(true));
  }, []);

  // Refresh on every page change: rewards arrive when an attempt finishes.
  useEffect(load, [load, location.pathname]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    const onClick = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onClick);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onClick);
    };
  }, [open]);

  const unread = data?.unread ?? 0;
  return (
    <div className="bell" ref={panelRef}>
      <button
        type="button"
        className="btn btn-ghost bell-button"
        aria-expanded={open}
        aria-haspopup="true"
        aria-label={`Уведомления${unread ? `: ${unread} непрочитанных` : ""}`}
        onClick={() => setOpen((o) => !o)}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 3a6 6 0 0 0-6 6v4l-2 3h16l-2-3V9a6 6 0 0 0-6-6zm0 18a2.5 2.5 0 0 0 2.4-2h-4.8A2.5 2.5 0 0 0 12 21z" fill="currentColor" />
        </svg>
        {unread > 0 && <span className="bell-count">{unread}</span>}
      </button>
      {open && (
        <div className="bell-panel" role="dialog" aria-label="Уведомления">
          <div className="bell-head">
            <strong>Уведомления</strong>
            {unread > 0 && (
              <button type="button" className="btn btn-ghost small" onClick={() => void markAllNotificationsRead().then(load)}>
                Прочитать все
              </button>
            )}
          </div>
          {failed && <p className="muted small">Не удалось загрузить уведомления.</p>}
          {data && data.items.length === 0 && <p className="muted small">Уведомлений пока нет.</p>}
          <ul>
            {data?.items.map((n) => (
              <li key={n.id} className={n.read ? "" : "is-unread"}>
                <button
                  type="button"
                  onClick={() => {
                    void markNotificationRead(n.id).then(load);
                    setOpen(false);
                    if (n.link) navigate(n.link);
                  }}
                >
                  <span className="bell-title">{n.title}</span>
                  <span className="muted small">{n.body}</span>
                  <span className="muted small">{formatDateTime(n.created_at)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
