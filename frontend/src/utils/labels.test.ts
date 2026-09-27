import { describe, expect, it } from "vitest";
import { achievementGlyph } from "./achievements";
import { outcomeLabel, outcomeTone } from "./labels";

describe("ending badge", () => {
  it("uses the preset title and tone", () => {
    expect(outcomeLabel({ outcome: "calm_resolution" })).toBe("Спокойное разрешение");
    expect(outcomeTone({ outcome: "escalated_to_senior" })).toBe("bad");
  });

  it("prefers the methodologist's own label and tone", () => {
    const custom = { outcome: "custom", outcome_label: "Пассажир благодарит", outcome_tone: "good" };
    expect(outcomeLabel(custom)).toBe("Пассажир благодарит");
    expect(outcomeTone(custom)).toBe("good");
  });

  it("falls back to neutral and no badge", () => {
    expect(outcomeLabel({ outcome: null })).toBeNull();
    expect(outcomeTone({ outcome: "custom", outcome_label: "x", outcome_tone: null })).toBe("neutral");
  });
});

describe("achievement icon", () => {
  it("maps known icons and falls back to a medal", () => {
    expect(achievementGlyph("heart")).toBe("❤️");
    expect(achievementGlyph("rocket")).toBe("🏅");
    expect(achievementGlyph(null)).toBe("🏅");
  });
});
