/* Values the server accepts for scene metadata (backend/app/scenarios/visual.py), with Russian labels. */

export type Option = { id: string; title: string };

export const FIGURES: Option[] = [
  { id: "man", title: "мужчина" },
  { id: "woman", title: "женщина" },
  { id: "passenger", title: "пассажир" },
  { id: "elderly", title: "пожилой пассажир" },
  { id: "child", title: "ребёнок" },
  { id: "business", title: "бизнесмен" },
  { id: "chief", title: "начальник поезда" },
  { id: "conductor", title: "коллега-проводник" },
  { id: "medic", title: "медик" },
];

export const GENDERS: Option[] = [
  { id: "m", title: "он" },
  { id: "f", title: "она" },
  { id: "n", title: "не указан" },
];

export const COLORS: Option[] = [
  { id: "blue", title: "синий" },
  { id: "red", title: "красный" },
  { id: "green", title: "зелёный" },
  { id: "grey", title: "серый" },
  { id: "purple", title: "фиолетовый" },
  { id: "orange", title: "оранжевый" },
  { id: "teal", title: "бирюзовый" },
  { id: "brown", title: "коричневый" },
];

export const POSES: Option[] = [
  { id: "standing", title: "стоит" },
  { id: "sitting", title: "сидит" },
  { id: "unwell", title: "плохо (полулёжа)" },
  { id: "pointing", title: "указывает" },
  { id: "hands_on_hips", title: "руки на поясе" },
];

export const POSITIONS: Option[] = [
  { id: "far_left", title: "крайнее слева" },
  { id: "left", title: "слева" },
  { id: "center", title: "в центре" },
  { id: "right", title: "справа" },
  { id: "far_right", title: "крайнее справа" },
];

export const PROPS: Option[] = [
  { id: "suitcase", title: "чемодан в проходе" },
  { id: "spill", title: "пролитый напиток" },
  { id: "first_aid_kit", title: "аптечка" },
  { id: "water", title: "стакан воды" },
  { id: "phone", title: "телефон" },
  { id: "stroller", title: "детская коляска" },
  { id: "bag", title: "бесхозная сумка" },
];

export const BACKGROUNDS: Option[] = [
  { id: "standard", title: "вагон «Стандарт»" },
  { id: "business", title: "вагон «Бизнес»" },
  { id: "vestibule", title: "тамбур" },
];

export const MOODS: Option[] = [
  { id: "happy", title: "доволен" },
  { id: "calm", title: "спокоен" },
  { id: "worried", title: "встревожен" },
  { id: "scared", title: "напуган" },
  { id: "upset", title: "расстроен" },
  { id: "angry", title: "раздражён" },
];

export const OUTCOME_TONES: Option[] = [
  { id: "good", title: "хороший" },
  { id: "neutral", title: "нейтральный" },
  { id: "bad", title: "плохой" },
];
