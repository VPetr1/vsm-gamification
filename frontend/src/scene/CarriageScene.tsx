import { Figure } from "./Figure";
import type { SceneCharacter, SceneModel } from "./types";
import { MOOD_TONE, moodWord } from "./types";

const SEAT_X = [70, 330, 590];
const SITTING_X: Record<SceneCharacter["position"], number> = { left: 150, center: 410, right: 670 };
const STANDING_X: Record<SceneCharacter["position"], number> = { left: 250, center: 470, right: 640 };
const FLOOR_Y = 330;

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

function Seat({ x }: { x: number }) {
  return (
    <g>
      <rect x={x + 40} y={150} width={112} height={160} rx={22} fill="#29405E" />
      <rect x={x + 50} y={158} width={92} height={32} rx={10} fill="#F4F6F8" />
      <rect x={x + 44} y={200} width={6} height={100} rx={3} fill="#25B5AD" />
      <rect x={x + 20} y={284} width={150} height={32} rx={12} fill="#223750" />
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

function MoodTag({ character, x, y }: { character: SceneCharacter; x: number; y: number }) {
  const word = moodWord(character.mood, character.figure);
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

export function CarriageScene({ scene, label }: { scene: SceneModel; label: string }) {
  const placed = scene.characters.map((c) => ({
    character: c,
    x: c.pose === "sitting" ? SITTING_X[c.position] : STANDING_X[c.position],
  }));
  return (
    <svg className="scene" viewBox="0 0 800 380" role="img" aria-label={label} preserveAspectRatio="xMidYMid slice">
      <rect width={800} height={380} fill="#EDF1F5" />
      <rect width={800} height={44} fill="#FFFFFF" />
      <rect x={60} y={16} width={680} height={10} rx={5} fill="#E1F5F4" />
      <rect y={50} width={800} height={10} fill="#C9D3DD" />
      {SEAT_X.map((x) => (
        <rect key={x} x={x + 20} y={56} width={160} height={6} rx={3} fill="#AEBBC8" />
      ))}
      <Windows />
      {SEAT_X.map((x) => (
        <Seat key={x} x={x} />
      ))}
      <rect y={FLOOR_Y} width={800} height={50} fill="#D5DDE5" />
      <rect y={FLOOR_Y + 14} width={800} height={4} fill="#25B5AD" opacity={0.6} />
      {scene.props.includes("spill") && <Spill x={560} />}
      {scene.props.includes("suitcase") && <Suitcase x={470} />}
      {placed.map(({ character, x }) => (
        <g key={character.id} transform={`translate(${x} ${character.pose === "sitting" ? 292 : FLOOR_Y})`}>
          <Figure figure={character.figure} mood={character.mood} pose={character.pose} />
        </g>
      ))}
      {placed.map(({ character, x }) => {
        const top = character.pose === "sitting" ? 292 - 180 : FLOOR_Y - 244;
        return (
          <g key={`${character.id}-labels`}>
            {character.speaking && <SpeakerMark x={x + 44} y={top + 4} />}
            <MoodTag character={character} x={x} y={top - 34} />
          </g>
        );
      })}
    </svg>
  );
}
