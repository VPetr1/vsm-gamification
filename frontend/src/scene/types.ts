export type Mood = "happy" | "calm" | "worried" | "upset" | "angry" | "scared";

export type Pose = "sitting" | "standing" | "unwell" | "pointing" | "hands_on_hips";
export type Position = "far_left" | "left" | "center" | "right" | "far_right";
export type Background = "standard" | "business" | "vestibule";

export type SceneCharacter = {
  id: string;
  name: string;
  figure: string;
  gender: "m" | "f" | "n";
  color: string | null;
  pose: Pose;
  position: Position;
  mood: Mood;
  speaking: boolean;
};

export type SceneModel = {
  background: Background;
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

export function moodWord(mood: Mood, gender: "m" | "f" | "n"): string {
  return MOOD_WORDS[mood][gender];
}

export const MOOD_TONE: Record<Mood, "good" | "neutral" | "warn" | "bad"> = {
  happy: "good",
  calm: "good",
  worried: "warn",
  scared: "warn",
  upset: "bad",
  angry: "bad",
};
