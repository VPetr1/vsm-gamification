/* Pure helpers for the scenario editor. The graph format is documented in docs/scenario-format.md. */

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export type Obj = { [key: string]: Json };

export type Clause =
  | { kind: "flag"; flag: string; negate: boolean }
  | { kind: "scale"; scale: "loyalty" | "safety"; op: string; value: number };
export type ConditionForm = { mode: "all" | "any"; clauses: Clause[] };

export const SCALE_OPS = [">=", ">", "<=", "<", "==", "!="] as const;

function leafToClause(c: Obj): Clause | null {
  const keys = Object.keys(c);
  if (keys.length === 1 && keys[0] === "flag" && typeof c.flag === "string") return { kind: "flag", flag: c.flag, negate: false };
  if (keys.length === 1 && keys[0] === "not") {
    const inner = c.not as Obj;
    if (inner && typeof inner === "object" && Object.keys(inner).length === 1 && typeof inner.flag === "string") {
      return { kind: "flag", flag: inner.flag, negate: true };
    }
    return null;
  }
  if (keys.length === 3 && "scale" in c && "op" in c && "value" in c) {
    if ((c.scale === "loyalty" || c.scale === "safety") && typeof c.op === "string" && typeof c.value === "number") {
      return { kind: "scale", scale: c.scale, op: c.op, value: c.value };
    }
    return null;
  }
  if (keys.length === 1 && (keys[0] === "min_loyalty" || keys[0] === "min_safety") && typeof c[keys[0]] === "number") {
    return { kind: "scale", scale: keys[0] === "min_loyalty" ? "loyalty" : "safety", op: ">=", value: c[keys[0]] as number };
  }
  return null;
}

/** Condition JSON -> simple form, or null when it is too complex for the form (edited as JSON then). */
export function conditionToForm(condition: Json | undefined): ConditionForm | null {
  if (condition === undefined || condition === null) return { mode: "all", clauses: [] };
  if (typeof condition !== "object" || Array.isArray(condition)) return null;
  const keys = Object.keys(condition);
  if (keys.length === 1 && (keys[0] === "all" || keys[0] === "any") && Array.isArray(condition[keys[0]])) {
    const clauses: Clause[] = [];
    for (const item of condition[keys[0]] as Json[]) {
      if (!item || typeof item !== "object" || Array.isArray(item)) return null;
      const clause = leafToClause(item);
      if (!clause) return null;
      clauses.push(clause);
    }
    return { mode: keys[0] as "all" | "any", clauses };
  }
  const single = leafToClause(condition);
  return single ? { mode: "all", clauses: [single] } : null;
}

function clauseToJson(c: Clause): Obj {
  if (c.kind === "flag") return c.negate ? { not: { flag: c.flag } } : { flag: c.flag };
  return { scale: c.scale, op: c.op, value: c.value };
}

/** Form -> condition JSON; undefined means "no condition". */
export function formToCondition(form: ConditionForm): Obj | undefined {
  if (form.clauses.length === 0) return undefined;
  if (form.clauses.length === 1) return clauseToJson(form.clauses[0]);
  return { [form.mode]: form.clauses.map(clauseToJson) };
}

function outcomesOf(node: Obj): Obj[] {
  const outcomes: Obj[] = [];
  if (Array.isArray(node.choices)) outcomes.push(...(node.choices as Obj[]));
  if (node.timeout && typeof node.timeout === "object") outcomes.push(node.timeout as Obj);
  return outcomes;
}

/** Renames a node and rewrites every reference to it (start, next_node, transitions). */
export function renameNode(graph: Obj, from: string, to: string): Obj {
  const nodes = graph.nodes as Obj;
  if (!(from in nodes) || to in nodes || !to) return graph;
  const next = structuredClone(graph) as Obj;
  const nextNodes: Obj = {};
  for (const [id, node] of Object.entries(next.nodes as Obj)) nextNodes[id === from ? to : id] = node;
  next.nodes = nextNodes;
  if (next.start_node === from) next.start_node = to;
  for (const node of Object.values(nextNodes)) {
    for (const outcome of outcomesOf(node as Obj)) {
      if (outcome.next_node === from) outcome.next_node = to;
      if (Array.isArray(outcome.transitions)) {
        for (const t of outcome.transitions as Obj[]) if (t.next_node === from) t.next_node = to;
      }
    }
  }
  return next;
}

/** Nodes that still point to `id`; shown before deleting it. */
export function referencesTo(graph: Obj, id: string): string[] {
  const refs = new Set<string>();
  if (graph.start_node === id) refs.add("start_node");
  for (const [nodeId, node] of Object.entries(graph.nodes as Obj)) {
    for (const outcome of outcomesOf(node as Obj)) {
      const targets = [outcome.next_node, ...((outcome.transitions as Obj[] | undefined) ?? []).map((t) => t.next_node)];
      if (targets.includes(id)) refs.add(nodeId);
    }
  }
  return [...refs];
}

export function freeId(taken: Iterable<string>, base: string): string {
  const used = new Set(taken);
  if (!used.has(base)) return base;
  let i = 2;
  while (used.has(`${base}_${i}`)) i += 1;
  return `${base}_${i}`;
}

export const ID_PATTERN = /^[A-Za-z][A-Za-z0-9_]{0,59}$/;

/** "nodes.suitcase.choices[0].next_node: ..." -> "suitcase"; graph-level errors -> null. */
export function errorNodeId(error: string): string | null {
  const match = /^nodes\.([^.:[\]]+)/.exec(error);
  return match ? match[1] : null;
}
