import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { Employee } from "../api/types";

const STORAGE_KEY = "vsm.profile";

type SessionValue = {
  user: Employee | null;
  signIn: (employee: Employee) => void;
  signOut: () => void;
};

const SessionContext = createContext<SessionValue | null>(null);

function readStored(): Employee | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Employee) : null;
  } catch {
    return null;
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Employee | null>(readStored);

  const signIn = useCallback((employee: Employee) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(employee));
    } catch {
      /* private mode: keep the profile for this tab only */
    }
    setUser(employee);
  }, []);

  const signOut = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, signIn, signOut }), [user, signIn, signOut]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside SessionProvider");
  return value;
}
