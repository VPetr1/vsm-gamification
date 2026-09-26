import { api } from "./client";
import type { AttemptResult, AttemptState, Employee, ScenarioSummary } from "./types";

export const listEmployees = () => api<Employee[]>("/employees");

export const listScenarios = () => api<ScenarioSummary[]>("/scenarios");

export const startAttempt = (employeeId: string, scenarioId: string) =>
  api<AttemptState>("/attempts", { method: "POST", body: { employee_id: employeeId, scenario_id: scenarioId } });

export const getAttempt = (attemptId: string) => api<AttemptState>(`/attempts/${encodeURIComponent(attemptId)}`);

export const submitChoice = (attemptId: string, choiceId: string | null, expectedStep: number) =>
  api<AttemptState>(`/attempts/${encodeURIComponent(attemptId)}/choice`, {
    method: "POST",
    body: { choice_id: choiceId, expected_step: expectedStep },
  });

export const getResult = (attemptId: string) => api<AttemptResult>(`/attempts/${encodeURIComponent(attemptId)}/result`);
