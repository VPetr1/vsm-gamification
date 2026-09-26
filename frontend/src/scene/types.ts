export type Mood = "happy" | "calm" | "worried" | "upset" | "angry" | "scared";

export type SceneCharacter = {
  id: string;
  name: string;
  figure: string;
  pose: "sitting" | "standing";
  position: "left" | "center" | "right";
  mood: Mood;
  speaking: boolean;
};

export type SceneModel = {
  characters: SceneCharacter[];
  props: string[];
};

const MOOD_WORDS: Record<Mood, { m: string; f: string; n: string }> = {
  happy: { m: "доволен", f: "довольна", n: "довольны" },
  calm: { m: "спокоен", f: "спокойна", n: "спокойны" },
  worried: { m: "встревожен", f: "встревожена", n: "встревожены" },
  upset: { m: "расстроен", f: "расстроена", n: "расстроены" },
  angry: { m: "раздражён", f: "раздражена", n: "раздражены" },
  scared: { m: "напуган", f: "напугана", n: "напуганы" },
};

export function moodWord(mood: Mood, figure: string): string {
  const words = MOOD_WORDS[mood];
  if (figure === "man") return words.m;
  if (figure === "woman") return words.f;
  return words.n;
}

export const MOOD_TONE: Record<Mood, "good" | "neutral" | "warn" | "bad"> = {
  happy: "good",
  calm: "good",
  worried: "warn",
  scared: "warn",
  upset: "bad",
  angry: "bad",
};
