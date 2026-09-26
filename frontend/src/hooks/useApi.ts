import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

/** Loads data once per `key`, exposes loading/error/reload, and signs out on 401. */
export function useApi<T>(load: () => Promise<T>, key: string) {
  const { sessionLost } = useAuth();
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const loadRef = useRef(load);
  loadRef.current = load;

  const reload = useCallback(() => {
    setError(null);
    loadRef.current()
      .then(setData)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) sessionLost();
        else setError(err instanceof ApiError ? err : new ApiError(0, "unknown", "Не удалось загрузить данные"));
      });
  }, [sessionLost]);

  useEffect(() => {
    setData(null);
    reload();
  }, [reload, key]);

  return { data, error, reload, setData };
}
