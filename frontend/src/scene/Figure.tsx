import type { Mood } from "./types";

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
};

function Hair({ figure, hair }: { figure: string; hair: string }) {
  if (figure === "woman") {
    return <path d="M-24 4 Q-26 -30 0 -32 Q26 -30 24 4 L20 16 L14 -8 Q0 -18 -14 -8 L-20 16 Z" fill={hair} />;
  }
  return <path d="M-21 -6 Q-22 -30 0 -30 Q22 -30 21 -6 Q14 -18 0 -18 Q-14 -18 -21 -6 Z" fill={hair} />;
}

/** A flat, friendly figure. Origin is at the feet (standing) or the seat (sitting). */
export function Figure({ figure, mood, pose }: { figure: string; mood: Mood; pose: "sitting" | "standing" }) {
  const p = PALETTES[figure] ?? PALETTES.passenger;
  const sitting = pose === "sitting";
  const headY = sitting ? -150 : -210;
  return (
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
      <g transform={`translate(0 ${sitting ? -10 : -86})`}>
        <path
          d={figure === "woman" ? "M-28 0 L-22 -92 Q0 -104 22 -92 L30 0 Z" : "M-27 0 L-25 -90 Q0 -100 25 -90 L27 0 Z"}
          fill={p.top}
        />
        <path d="M-6 -96 L0 -80 L6 -96 Z" fill={p.topDark} />
        <rect x={-38} y={-86} width={13} height={62} rx={6.5} fill={p.topDark} transform="rotate(8 -32 -86)" />
        <rect x={25} y={-86} width={13} height={62} rx={6.5} fill={p.topDark} transform="rotate(-8 32 -86)" />
      </g>
      <g transform={`translate(0 ${headY})`}>
        <rect x={-7} y={18} width={14} height={16} rx={5} fill={SKIN} />
        <circle r={24} fill={SKIN} />
        <Hair figure={figure} hair={p.hair} />
        <Face mood={mood} />
      </g>
    </g>
  );
}
