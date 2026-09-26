export const OUTCOME_LABEL: Record<string, string> = {
  calm_resolution: "Спокойное разрешение",
  resolved_with_dissatisfaction: "Разрешено с недовольством",
  escalated_to_senior: "Передано старшему",
};

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
