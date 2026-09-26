import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { startAttempt } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";

/** Starts (or resumes) a scenario and opens the play screen. */
export function useStartScenario() {
  const navigate = useNavigate();
  const { sessionLost } = useAuth();
  const [starting, setStarting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const start = async (scenarioId: string, resumeAttemptId?: string | null) => {
    if (starting) return;
    if (resumeAttemptId) {
      navigate(`/attempts/${resumeAttemptId}`);
      return;
    }
    setStarting(scenarioId);
    setError(null);
    try {
      const state = await startAttempt(scenarioId);
      navigate(`/attempts/${state.attempt_id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) sessionLost();
      else setError(err instanceof ApiError ? err.message : "Не удалось начать сценарий");
      setStarting(null);
    }
  };

  return { start, starting, error };
}
