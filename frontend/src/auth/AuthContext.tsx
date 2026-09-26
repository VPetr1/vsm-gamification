import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ApiError } from "../api/client";
import * as endpoints from "../api/endpoints";
import type { Me } from "../api/types";

type AuthValue = {
  user: Me | null;
  checking: boolean;
  signIn: (login: string, password: string) => Promise<Me>;
  signOut: () => Promise<void>;
  /** Called when any request answers 401: the server session is gone, so is the local user. */
  sessionLost: () => void;
};

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Me | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    endpoints
      .me()
      .then(setUser)
      .catch((err: unknown) => {
        if (!(err instanceof ApiError && err.status === 401)) console.warn("Не удалось проверить сессию", err);
        setUser(null);
      })
      .finally(() => setChecking(false));
  }, []);

  const signIn = useCallback(async (login: string, password: string) => {
    const account = await endpoints.signIn(login, password);
    setUser(account);
    return account;
  }, []);

  const signOut = useCallback(async () => {
    try {
      await endpoints.signOut();
    } finally {
      setUser(null);
    }
  }, []);

  const sessionLost = useCallback(() => setUser(null), []);

  const value = useMemo(
    () => ({ user, checking, signIn, signOut, sessionLost }),
    [user, checking, signIn, signOut, sessionLost],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
