import { Figure } from "./Figure";
import type { Background, Position, SceneCharacter, SceneModel } from "./types";
import { MOOD_TONE, moodWord } from "./types";

const SEAT_X = [70, 330, 590];
const SITTING_X: Record<Position, number> = { far_left: 110, left: 190, center: 410, right: 630, far_right: 710 };
const STANDING_X: Record<Position, number> = { far_left: 90, left: 250, center: 470, right: 640, far_right: 740 };
const FLOOR_Y = 330;

type Theme = { wall: string; seat: string; seatDark: string; headrest: string; floor: string; accent: string };
const THEMES: Record<Exclude<Background, "vestibule">, Theme> = {
  standard: { wall: "#EDF1F5", seat: "#29405E", seatDark: "#223750", headrest: "#F4F6F8", floor: "#D5DDE5", accent: "#25B5AD" },
  business: { wall: "#F3EEE6", seat: "#6B4A3A", seatDark: "#573B2E", headrest: "#F1E6D2", floor: "#CDB79E", accent: "#C9A24A" },
};

function Windows() {
  return (
    <g>
      <defs>
        {SEAT_X.map((x, i) => (
          <clipPath id={`win-${i}`} key={x}>
            <rect x={x + 10} y={78} width={180} height={104} rx={24} />
          </clipPath>
        ))}
      </defs>
      {SEAT_X.map((x, i) => (
        <g key={x}>
          <rect x={x + 4} y={72} width={192} height={116} rx={28} fill="#C3CED9" />
          <g clipPath={`url(#win-${i})`}>
            <rect x={x + 10} y={78} width={180} height={104} fill="#D8EEF4" />
            <g className="landscape">
              <path d={`M${x - 200} 160 Q${x - 120} 120 ${x - 40} 150 T${x + 120} 145 T${x + 280} 150 T${x + 440} 150 V190 H${x - 200} Z`} fill="#A7D3CC" />
              <path d={`M${x - 200} 172 Q${x - 90} 150 ${x + 20} 168 T${x + 240} 165 T${x + 460} 170 V190 H${x - 200} Z`} fill="#7DB8AA" />
              {[0, 60, 140, 230, 320, 410].map((dx) => (
                <g key={dx}>
                  <rect x={x - 150 + dx} y={150} width={4} height={18} fill="#5B8F83" />
                  <circle cx={x - 148 + dx} cy={146} r={11} fill="#5FA394" />
                </g>
              ))}
            </g>
          </g>
        </g>
      ))}
    </g>
  );
}

function Seat({ x, theme }: { x: number; theme: Theme }) {
  return (
    <g>
      <rect x={x + 40} y={150} width={112} height={160} rx={22} fill={theme.seat} />
      <rect x={x + 50} y={158} width={92} height={32} rx={10} fill={theme.headrest} />
      <rect x={x + 44} y={200} width={6} height={100} rx={3} fill={theme.accent} />
      <rect x={x + 20} y={284} width={150} height={32} rx={12} fill={theme.seatDark} />
      <rect x={x + 150} y={262} width={34} height={12} rx={6} fill="#1B2D44" />
      <rect x={x + 70} y={316} width={10} height={16} fill="#8A98A8" />
      <rect x={x + 130} y={316} width={10} height={16} fill="#8A98A8" />
    </g>
  );
}

function Suitcase({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} ${FLOOR_Y})`}>
      <rect x={-34} y={-78} width={68} height={74} rx={10} fill="#E8A317" />
      <rect x={-34} y={-78} width={68} height={74} rx={10} fill="none" stroke="#B87F0F" strokeWidth={3} />
      <rect x={-10} y={-92} width={20} height={16} rx={5} fill="none" stroke="#6B5A3A" strokeWidth={5} />
      <rect x={-18} y={-72} width={6} height={62} rx={3} fill="#C98D14" />
      <rect x={12} y={-72} width={6} height={62} rx={3} fill="#C98D14" />
      <circle cx={-22} cy={-2} r={5} fill="#3A3F48" />
      <circle cx={22} cy={-2} r={5} fill="#3A3F48" />
    </g>
  );
}

function Spill({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} ${FLOOR_Y + 8})`}>
      <ellipse rx={62} ry={9} fill="#C79A6B" opacity={0.55} />
      <ellipse cx={30} cy={-2} rx={14} ry={4} fill="#FFFFFF" opacity={0.5} />
      <g transform="translate(-54 -10) rotate(-70)">
        <rect x={-8} y={-10} width={16} height={20} rx={3} fill="#F4F6F8" stroke="#9AA7B4" strokeWidth={2} />
      </g>
    </g>
  );
}

function FirstAidKit({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} ${FLOOR_Y})`}>
      <rect x={-26} y={-40} width={52} height={38} rx={6} fill="#F4F6F8" stroke="#C9D3DD" strokeWidth={2} />
      <rect x={-10} y={-48} width={20} height={9} rx={3} fill="none" stroke="#9AA7B4" strokeWidth={3} />
      <rect x={-4} y={-33} width={8} height={24} fill="#D0342C" />
      <rect x={-12} y={-25} width={24} height={8} fill="#D0342C" />
    </g>
  );
}

function Water({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} ${FLOOR_Y})`}>
      <rect x={-22} y={-60} width={44} height={6} rx={3} fill="#8A98A8" />
      <rect x={-3} y={-54} width={6} height={54} fill="#8A98A8" />
      <path d="M-10 -92 L10 -92 L7 -62 L-7 -62 Z" fill="#D8EEF4" stroke="#9AA7B4" strokeWidth={2} />
      <path d="M-9 -82 L9 -82 L7 -63 L-7 -63 Z" fill="#8FCBE0" />
    </g>
  );
}

function Phone({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} ${FLOOR_Y + 6}) rotate(-20)`}>
      <rect x={-9} y={-16} width={18} height={30} rx={4} fill="#1E2530" />
      <rect x={-6} y={-12} width={12} height={20} rx={2} fill="#6FB3D9" />
    </g>
  );
}

function Stroller({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} ${FLOOR_Y})`}>
      <path d="M-34 -60 Q-34 -90 0 -90 L0 -60 Z" fill="#7E5AA6" />
      <rect x={-36} y={-62} width={60} height={30} rx={10} fill="#9A78C2" />
      <path d="M24 -60 L40 -96" stroke="#3A3F48" strokeWidth={4} strokeLinecap="round" />
      <circle cx={-24} cy={-10} r={10} fill="none" stroke="#3A3F48" strokeWidth={4} />
      <circle cx={14} cy={-10} r={10} fill="none" stroke="#3A3F48" strokeWidth={4} />
    </g>
  );
}

function Bag({ x }: { x: number }) {
  return (
    <g transform={`translate(${x} ${FLOOR_Y})`}>
      <path d="M-14 -44 Q-14 -60 0 -60 Q14 -60 14 -44" fill="none" stroke="#3A2A22" strokeWidth={4} />
      <rect x={-26} y={-46} width={52} height={44} rx={8} fill="#3F3A35" />
      <rect x={-26} y={-34} width={52} height={5} fill="#5A544D" />
      <text x={30} y={-50} fontSize={22} fontWeight={700} fill="#D0342C">?</text>
    </g>
  );
}

function Vestibule() {
  return (
    <g>
      <rect width={800} height={380} fill="#E4E9EE" />
      <rect x={290} y={60} width={220} height={270} rx={10} fill="#B8C4D0" />
      <rect x={300} y={70} width={96} height={260} rx={6} fill="#CBD5DF" />
      <rect x={404} y={70} width={96} height={260} rx={6} fill="#CBD5DF" />
      <rect x={316} y={96} width={64} height={90} rx={14} fill="#D8EEF4" />
      <rect x={420} y={96} width={64} height={90} rx={14} fill="#D8EEF4" />
      <rect x={380} y={210} width={8} height={40} rx={4} fill="#8A98A8" />
      <rect x={412} y={210} width={8} height={40} rx={4} fill="#8A98A8" />
      <rect x={120} y={120} width={10} height={210} rx={5} fill="#9AA7B4" />
      <rect x={670} y={120} width={10} height={210} rx={5} fill="#9AA7B4" />
      <rect x={560} y={96} width={70} height={46} rx={6} fill="#29405E" />
      <text x={595} y={126} textAnchor="middle" fontSize={16} fill="#E1F5F4">WC</text>
    </g>
  );
}

function Carriage({ theme }: { theme: Theme }) {
  return (
    <g>
      <rect width={800} height={380} fill={theme.wall} />
      <rect width={800} height={44} fill="#FFFFFF" />
      <rect x={60} y={16} width={680} height={10} rx={5} fill="#E1F5F4" />
      <rect y={50} width={800} height={10} fill="#C9D3DD" />
      {SEAT_X.map((x) => (
        <rect key={x} x={x + 20} y={56} width={160} height={6} rx={3} fill="#AEBBC8" />
      ))}
      <Windows />
      {SEAT_X.map((x) => (
        <Seat key={x} x={x} theme={theme} />
      ))}
    </g>
  );
}

function MoodTag({ character, x, y }: { character: SceneCharacter; x: number; y: number }) {
  const word = moodWord(character.mood, character.gender);
  const width = Math.max(96, word.length * 9 + 40);
  return (
    <g transform={`translate(${x - width / 2} ${y})`} className={`mood-tag tone-${MOOD_TONE[character.mood]}`}>
      <rect width={width} height={28} rx={14} />
      <text x={width / 2} y={19} textAnchor="middle">
        {word}
      </text>
    </g>
  );
}

function SpeakerMark({ x, y }: { x: number; y: number }) {
  return (
    <g transform={`translate(${x} ${y})`} className="speaker-mark">
      <path d="M-18 -30 H18 Q24 -30 24 -24 V-6 Q24 0 18 0 H4 L-4 9 L-4 0 H-18 Q-24 0 -24 -6 V-24 Q-24 -30 -18 -30 Z" />
      <circle cx={-9} cy={-15} r={3} />
      <circle cx={0} cy={-15} r={3} />
      <circle cx={9} cy={-15} r={3} />
    </g>
  );
}

const PROP_X: Record<string, number> = { bag: 200, first_aid_kit: 300, water: 360, suitcase: 470, spill: 560, phone: 610, stroller: 700 };
const PROP_VIEW: Record<string, (x: number) => JSX.Element> = {
  bag: (x) => <Bag x={x} />,
  first_aid_kit: (x) => <FirstAidKit x={x} />,
  water: (x) => <Water x={x} />,
  suitcase: (x) => <Suitcase x={x} />,
  spill: (x) => <Spill x={x} />,
  phone: (x) => <Phone x={x} />,
  stroller: (x) => <Stroller x={x} />,
};

function figureTop(c: SceneCharacter): number {
  const seated = c.pose === "sitting" || c.pose === "unwell";
  const height = seated ? 180 : 244;
  return (seated ? 292 : FLOOR_Y) - height * (c.figure === "child" ? 0.68 : 1);
}

export function CarriageScene({ scene, label }: { scene: SceneModel; label: string }) {
  const placed = scene.characters
    .map((c) => ({
      character: c,
      x: c.pose === "sitting" || c.pose === "unwell" ? SITTING_X[c.position] : STANDING_X[c.position],
    }))
    .sort((a, b) => a.x - b.x);
  // Neighbours closer than a tag's width get their mood tags on alternating heights.
  const tagLift = placed.map((p, i) => (i > 0 && p.x - placed[i - 1].x < 150 && i % 2 === 1 ? 34 : 0));
  const theme = scene.background === "vestibule" ? THEMES.standard : THEMES[scene.background] ?? THEMES.standard;
  return (
    <svg className="scene" viewBox="0 0 800 380" role="img" aria-label={label} preserveAspectRatio="xMidYMid slice">
      {scene.background === "vestibule" ? <Vestibule /> : <Carriage theme={theme} />}
      <rect y={FLOOR_Y} width={800} height={50} fill={theme.floor} />
      <rect y={FLOOR_Y + 14} width={800} height={4} fill={theme.accent} opacity={0.6} />
      {scene.props.filter((id) => id in PROP_VIEW).map((id) => (
        <g key={id}>{PROP_VIEW[id](PROP_X[id])}</g>
      ))}
      {placed.map(({ character, x }) => (
        <g
          key={character.id}
          transform={`translate(${x} ${character.pose === "sitting" || character.pose === "unwell" ? 292 : FLOOR_Y})`}
        >
          <Figure figure={character.figure} mood={character.mood} pose={character.pose} color={character.color} />
        </g>
      ))}
      {placed.map(({ character, x }, i) => {
        const top = figureTop(character);
        return (
          <g key={`${character.id}-labels`}>
            {character.speaking && <SpeakerMark x={x + 44} y={top + 4} />}
            <MoodTag character={character} x={x} y={top - 34 - tagLift[i]} />
          </g>
        );
      })}
    </svg>
  );
}
