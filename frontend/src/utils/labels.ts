export const OUTCOME_LABEL: Record<string, string> = {
  calm_resolution: "Спокойное разрешение",
  resolved_with_dissatisfaction: "Разрешено с недовольством",
  escalated_to_senior: "Передано старшему",
};

const OUTCOME_TONE: Record<string, "good" | "neutral" | "bad"> = {
  calm_resolution: "good",
  resolved_with_dissatisfaction: "neutral",
  escalated_to_senior: "bad",
};

type Ending = { outcome: string | null; outcome_label?: string | null; outcome_tone?: string | null };

/** Badge text of an ending: the methodologist's own label for a custom ending, else the preset title. */
export function outcomeLabel(e: Ending): string | null {
  if (e.outcome_label) return e.outcome_label;
  return e.outcome ? OUTCOME_LABEL[e.outcome] ?? e.outcome : null;
}

export function outcomeTone(e: Ending): "good" | "neutral" | "bad" {
  const tone = e.outcome_tone ?? (e.outcome ? OUTCOME_TONE[e.outcome] : undefined);
  return tone === "good" || tone === "bad" ? tone : "neutral";
}

const TAG_LABEL: Record<string, string> = {
  communication: "Коммуникация",
  safety: "Безопасность",
  first_aid: "Первая помощь",
  stress_resistance: "Стрессоустойчивость",
};

export function tagLabel(tag: string): string {
  return TAG_LABEL[tag] ?? tag;
}

export function isCompetencyTag(tag: string): boolean {
  return tag in TAG_LABEL;
}
