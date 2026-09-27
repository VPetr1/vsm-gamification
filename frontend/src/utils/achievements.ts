/* Icons an achievement may use (backend ACHIEVEMENT_ICONS) and the glyph shown for each. */
export const ACHIEVEMENT_ICONS: { id: string; title: string; glyph: string }[] = [
  { id: "medal", title: "медаль", glyph: "🏅" },
  { id: "star", title: "звезда", glyph: "⭐" },
  { id: "shield", title: "щит", glyph: "🛡️" },
  { id: "heart", title: "сердце", glyph: "❤️" },
  { id: "handshake", title: "рукопожатие", glyph: "🤝" },
  { id: "clock", title: "часы", glyph: "⏱️" },
];

export function achievementGlyph(icon: string | null | undefined): string {
  return ACHIEVEMENT_ICONS.find((i) => i.id === icon)?.glyph ?? "🏅";
}
