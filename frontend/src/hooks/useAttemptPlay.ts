import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { getAttempt, submitChoice } from "../api/endpoints";
import type { AttemptState } from "../api/types";
import { remainingAtReceiptMs, remainingNowMs } from "../utils/time";

type Snapshot = {
  state: AttemptState;
  receivedAt: number;
  remainingAtReceipt: number | null;
};

const RESYNC_AFTER_EARLY_TIMEOUT_MS = 1000;

/**
 * Drives one attempt. The server is the source of truth: every decision is sent with the step
 * the player saw, and any conflict is resolved by re-reading the server state, never by guessing.
 */
export function useAttemptPlay(attemptId: string, onUnauthorized: () => void) {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [loadError, setLoadError] = useState<ApiError | null>(null);
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState<{ text: string; retry: boolean } | null>(null);
  const [remainingMs, setRemainingMs] = useState<number | null>(null);
  const [animateKey, setAnimateKey] = useState(0);

  const snapshotRef = useRef<Snapshot | null>(null);
  const pendingRef = useRef(false);
  const autoTimeoutSentFor = useRef<number | null>(null);
  const autoPaused = useRef(false);
  const resyncTimer = useRef<number | undefined>(undefined);

  const accept = useCallback((state: AttemptState) => {
    const previous = snapshotRef.current?.state;
    const next: Snapshot = {
      state,
      receivedAt: performance.now(),
      remainingAtReceipt: remainingAtReceiptMs(state.deadline, state.server_time),
    };
    snapshotRef.current = next;
    setSnapshot(next);
    if (previous && state.step > previous.step) setAnimateKey((k) => k + 1);
  }, []);

  const handleAuth = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError && err.status === 401) {
        onUnauthorized();
        return true;
      }
      return false;
    },
    [onUnauthorized],
  );

  const refresh = useCallback(async () => {
    try {
      const state = await getAttempt(attemptId);
      accept(state);
      autoPaused.current = false;
      setLoadError(null);
      return true;
    } catch (err) {
      if (handleAuth(err) || !(err instanceof ApiError)) return false;
      if (snapshotRef.current) setNotice({ text: err.message, retry: true });
      else setLoadError(err);
      return false;
    }
  }, [attemptId, accept, handleAuth]);

  const send = useCallback(
    async (choiceId: string | null) => {
      const current = snapshotRef.current;
      if (!current || pendingRef.current || current.state.status !== "in_progress") return;
      pendingRef.current = true;
      setPending(true);
      setNotice(null);
      try {
        accept(await submitChoice(attemptId, choiceId, current.state.step));
      } catch (err) {
        if (handleAuth(err) || !(err instanceof ApiError)) return;
        if (err.isNetwork) {
          autoPaused.current = true;
          setNotice({ text: `${err.message} Решение не засчитано.`, retry: true });
        } else if (err.code === "step_mismatch") {
          setNotice({ text: "Этот шаг уже засчитан — показано актуальное состояние.", retry: false });
          await refresh();
        } else if (err.code === "timer_not_expired") {
          // The device reached zero before the server did; re-read after a pause instead of hammering.
          window.clearTimeout(resyncTimer.current);
          resyncTimer.current = window.setTimeout(() => void refresh(), RESYNC_AFTER_EARLY_TIMEOUT_MS);
        } else if (err.code === "choice_not_available") {
          setNotice({ text: "Этот вариант сейчас недоступен.", retry: false });
          await refresh();
        } else if (err.code === "attempt_finished") {
          await refresh();
        } else {
          setNotice({ text: err.message, retry: true });
        }
      } finally {
        pendingRef.current = false;
        setPending(false);
      }
    },
    [attemptId, accept, handleAuth, refresh],
  );

  useEffect(() => {
    snapshotRef.current = null;
    setSnapshot(null);
    void refresh();
    return () => window.clearTimeout(resyncTimer.current);
  }, [refresh]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible" && !pendingRef.current) void refresh();
    };
    const onOnline = () => {
      if (!pendingRef.current) void refresh();
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", onOnline);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", onOnline);
    };
  }, [refresh]);

  useEffect(() => {
    if (!snapshot || snapshot.remainingAtReceipt === null || snapshot.state.status !== "in_progress") {
      setRemainingMs(null);
      return;
    }
    const { remainingAtReceipt, receivedAt, state } = snapshot;
    let timer: number | undefined;
    const tick = () => {
      const left = remainingNowMs(remainingAtReceipt, receivedAt, performance.now());
      setRemainingMs(left);
      if (left > 0) {
        timer = window.setTimeout(tick, 200);
        return;
      }
      if (autoPaused.current || pendingRef.current) return;
      if (autoTimeoutSentFor.current !== state.step) {
        autoTimeoutSentFor.current = state.step;
        void send(null);
      } else {
        // Already asked for this step: let GET resolve the overdue timer on the server.
        window.clearTimeout(resyncTimer.current);
        resyncTimer.current = window.setTimeout(() => void refresh(), RESYNC_AFTER_EARLY_TIMEOUT_MS);
      }
    };
    tick();
    return () => window.clearTimeout(timer);
  }, [snapshot, send, refresh]);

  return {
    state: snapshot?.state ?? null,
    loadError,
    pending,
    notice,
    dismissNotice: () => setNotice(null),
    remainingMs,
    animateKey,
    choose: (choiceId: string) => void send(choiceId),
    retry: () => {
      setNotice(null);
      void refresh();
    },
  };
}
