import type { Mood, Pose } from "./types";

const SKIN = "#F1C7A4";

function Brows({ mood }: { mood: Mood }) {
  // Left and right brow as short lines; the angle carries most of the emotion.
  const shapes: Record<Mood, [string, string]> = {
    happy: ["M-11 -9 Q-7 -12 -3 -10", "M3 -10 Q7 -12 11 -9"],
    calm: ["M-11 -9 L-3 -9", "M3 -9 L11 -9"],
    worried: ["M-11 -8 L-3 -12", "M3 -12 L11 -8"],
    scared: ["M-11 -10 Q-7 -14 -3 -12", "M3 -12 Q7 -14 11 -10"],
    upset: ["M-11 -9 L-3 -11", "M3 -11 L11 -9"],
    angry: ["M-11 -12 L-3 -8", "M3 -8 L11 -12"],
  };
  const [l, r] = shapes[mood];
  return (
    <g stroke="#3A2A22" strokeWidth={2.2} strokeLinecap="round" fill="none">
      <path d={l} />
      <path d={r} />
    </g>
  );
}

function Mouth({ mood }: { mood: Mood }) {
  switch (mood) {
    case "happy":
      return <path d="M-7 7 Q0 14 7 7" stroke="#7A3B2E" strokeWidth={2.4} fill="none" strokeLinecap="round" />;
    case "calm":
      return <path d="M-6 8 Q0 11 6 8" stroke="#7A3B2E" strokeWidth={2.2} fill="none" strokeLinecap="round" />;
    case "worried":
      return <path d="M-6 10 Q-3 8 0 10 Q3 12 6 10" stroke="#7A3B2E" strokeWidth={2.2} fill="none" strokeLinecap="round" />;
    case "scared":
      return <ellipse cx={0} cy={10} rx={4} ry={5} fill="#7A3B2E" />;
    case "upset":
      return <path d="M-6 12 Q0 7 6 12" stroke="#7A3B2E" strokeWidth={2.4} fill="none" strokeLinecap="round" />;
    case "angry":
      return <path d="M-7 12 Q0 6 7 12" stroke="#7A3B2E" strokeWidth={3} fill="none" strokeLinecap="round" />;
  }
}

function Face({ mood }: { mood: Mood }) {
  return (
    <g>
      <circle cx={-6} cy={-2} r={2.3} fill="#2A1E19" />
      <circle cx={6} cy={-2} r={2.3} fill="#2A1E19" />
      {mood === "angry" && (
        <g fill="#E57A6B" opacity={0.55}>
          <circle cx={-12} cy={5} r={4} />
          <circle cx={12} cy={5} r={4} />
        </g>
      )}
      <Brows mood={mood} />
      <Mouth mood={mood} />
    </g>
  );
}

type Palette = { hair: string; top: string; topDark: string; legs: string };

const PALETTES: Record<string, Palette> = {
  man: { hair: "#3B2E2A", top: "#4B6B8C", topDark: "#3A5573", legs: "#2B3442" },
  woman: { hair: "#7A4A2E", top: "#D9745B", topDark: "#B85D46", legs: "#3D3A4B" },
  passenger: { hair: "#5A4636", top: "#7C8B99", topDark: "#65727F", legs: "#39424D" },
  elderly: { hair: "#D7D7D2", top: "#8E7A62", topDark: "#75644F", legs: "#4A4640" },
  child: { hair: "#8A5A36", top: "#F2B632", topDark: "#D39A1E", legs: "#3F6FB0" },
  business: { hair: "#2E2622", top: "#2F3845", topDark: "#232A34", legs: "#232A34" },
  chief: { hair: "#3B2E2A", top: "#1F3A5F", topDark: "#16304F", legs: "#16304F" },
  conductor: { hair: "#4A3326", top: "#B3262E", topDark: "#8F1D24", legs: "#2A2F3A" },
  medic: { hair: "#4A3A30", top: "#F4F6F8", topDark: "#D5DCE3", legs: "#5C8FB8" },
};

/** Clothing colour a methodologist may pick; overrides the role's default top. */
const COLORS: Record<string, [string, string]> = {
  blue: ["#4B6B8C", "#3A5573"],
  red: ["#C8483F", "#A53A33"],
  green: ["#4E9A6A", "#3D7E55"],
  grey: ["#8A96A3", "#6F7B88"],
  purple: ["#7E5AA6", "#664889"],
  orange: ["#E08A3C", "#C2722B"],
  teal: ["#25A59D", "#1C8780"],
  brown: ["#8B6346", "#704F37"],
};

function Hair({ figure, hair }: { figure: string; hair: string }) {
  if (figure === "woman") {
    return <path d="M-24 4 Q-26 -30 0 -32 Q26 -30 24 4 L20 16 L14 -8 Q0 -18 -14 -8 L-20 16 Z" fill={hair} />;
  }
  if (figure === "elderly") {
    return <path d="M-23 -2 Q-24 -24 -12 -26 Q-6 -20 0 -24 Q6 -20 12 -26 Q24 -24 23 -2 Q18 -12 12 -14 Q0 -10 -12 -14 Q-18 -12 -23 -2 Z" fill={hair} />;
  }
  return <path d="M-21 -6 Q-22 -30 0 -30 Q22 -30 21 -6 Q14 -18 0 -18 Q-14 -18 -21 -6 Z" fill={hair} />;
}

/** Caps, glasses and badges that make a role recognisable at a glance. */
function HeadAccessory({ figure }: { figure: string }) {
  switch (figure) {
    case "chief":
    case "conductor":
      return (
        <g>
          <path d="M-24 -14 Q-24 -34 0 -35 Q24 -34 24 -14 Z" fill={figure === "chief" ? "#16304F" : "#2A2F3A"} />
          <rect x={-25} y={-18} width={50} height={6} rx={3} fill="#C8483F" />
          <path d="M-26 -12 Q0 -6 28 -12 L30 -8 Q0 -2 -28 -8 Z" fill="#111820" />
          {figure === "chief" && <circle cx={0} cy={-25} r={4} fill="#E8C24A" />}
        </g>
      );
    case "medic":
      return (
        <g>
          <path d="M-22 -14 Q-22 -32 0 -32 Q22 -32 22 -14 Z" fill="#F4F6F8" stroke="#C9D3DD" strokeWidth={1.5} />
          <rect x={-3} y={-29} width={6} height={14} fill="#D0342C" />
          <rect x={-7} y={-25} width={14} height={6} fill="#D0342C" />
        </g>
      );
    case "elderly":
      return (
        <g stroke="#3A3F48" strokeWidth={1.8} fill="none">
          <circle cx={-7} cy={-2} r={6} />
          <circle cx={7} cy={-2} r={6} />
          <path d="M-1 -2 H1" />
        </g>
      );
    default:
      return null;
  }
}

function TorsoDetail({ figure }: { figure: string }) {
  if (figure === "business") return <path d="M-4 -94 L0 -60 L4 -94 Z" fill="#C8483F" />;
  if (figure === "medic")
    return (
      <g>
        <rect x={10} y={-78} width={4} height={12} fill="#D0342C" />
        <rect x={6} y={-74} width={12} height={4} fill="#D0342C" />
      </g>
    );
  if (figure === "chief" || figure === "conductor")
    return (
      <g fill="#E8C24A">
        <circle cx={0} cy={-70} r={2.4} />
        <circle cx={0} cy={-52} r={2.4} />
        <circle cx={0} cy={-34} r={2.4} />
      </g>
    );
  return null;
}

/** Arms per pose; coordinates are relative to the shoulders line of the torso. */
function Arms({ pose, fill }: { pose: Pose; fill: string }) {
  switch (pose) {
    case "pointing":
      return (
        <g>
          <rect x={-38} y={-86} width={13} height={62} rx={6.5} fill={fill} transform="rotate(8 -32 -86)" />
          <rect x={24} y={-92} width={70} height={13} rx={6.5} fill={fill} transform="rotate(-12 28 -86)" />
          <circle cx={96} cy={-102} r={7} fill={SKIN} />
        </g>
      );
    case "hands_on_hips":
      return (
        <g fill={fill}>
          <path d="M-25 -88 L-46 -56 L-26 -34 L-20 -42 L-34 -56 L-20 -76 Z" />
          <path d="M25 -88 L46 -56 L26 -34 L20 -42 L34 -56 L20 -76 Z" />
        </g>
      );
    case "unwell":
      return (
        <g>
          <rect x={-38} y={-86} width={13} height={62} rx={6.5} fill={fill} transform="rotate(8 -32 -86)" />
          <rect x={-6} y={-80} width={13} height={48} rx={6.5} fill={fill} transform="rotate(60 0 -80)" />
          <circle cx={-34} cy={-60} r={7} fill={SKIN} />
        </g>
      );
    default:
      return (
        <g>
          <rect x={-38} y={-86} width={13} height={62} rx={6.5} fill={fill} transform="rotate(8 -32 -86)" />
          <rect x={25} y={-86} width={13} height={62} rx={6.5} fill={fill} transform="rotate(-8 32 -86)" />
        </g>
      );
  }
}

type FigureProps = { figure: string; mood: Mood; pose: Pose; color?: string | null };

/** A flat, friendly figure. Origin is at the feet (standing poses) or the seat (sitting, unwell). */
export function Figure({ figure, mood, pose, color }: FigureProps) {
  const base = PALETTES[figure] ?? PALETTES.passenger;
  const [top, topDark] = (color && COLORS[color]) || [base.top, base.topDark];
  const p = { ...base, top, topDark };
  const sitting = pose === "sitting" || pose === "unwell";
  const headY = sitting ? -150 : -210;
  // Unwell: slumped to the side, head tilted.
  const slump = pose === "unwell" ? "rotate(-14 0 -10)" : undefined;
  const body = (
    <g>
      {sitting ? (
        <g>
          <rect x={-18} y={-12} width={62} height={20} rx={9} fill={p.legs} />
          <rect x={30} y={-12} width={18} height={62} rx={8} fill={p.legs} />
          <rect x={26} y={44} width={30} height={10} rx={5} fill="#1E2530" />
        </g>
      ) : (
        <g>
          <rect x={-17} y={-90} width={14} height={86} rx={6} fill={p.legs} />
          <rect x={3} y={-90} width={14} height={86} rx={6} fill={p.legs} />
          <rect x={-21} y={-8} width={20} height={9} rx={4} fill="#1E2530" />
          <rect x={1} y={-8} width={20} height={9} rx={4} fill="#1E2530" />
        </g>
      )}
      <g transform={slump}>
        <g transform={`translate(0 ${sitting ? -10 : -86})`}>
          <path
            d={figure === "woman" ? "M-28 0 L-22 -92 Q0 -104 22 -92 L30 0 Z" : "M-27 0 L-25 -90 Q0 -100 25 -90 L27 0 Z"}
            fill={p.top}
          />
          <path d="M-6 -96 L0 -80 L6 -96 Z" fill={p.topDark} />
          <TorsoDetail figure={figure} />
          <Arms pose={pose} fill={p.topDark} />
        </g>
        <g transform={`translate(0 ${headY})${pose === "unwell" ? " rotate(-10)" : ""}`}>
          <rect x={-7} y={18} width={14} height={16} rx={5} fill={SKIN} />
          <circle r={24} fill={pose === "unwell" ? "#E9D2BE" : SKIN} />
          <Hair figure={figure} hair={p.hair} />
          <Face mood={mood} />
          <HeadAccessory figure={figure} />
        </g>
      </g>
    </g>
  );
  return figure === "child" ? <g transform="scale(0.68)">{body}</g> : body;
}
