import { describe, expect, it } from "vitest";
import { conditionToForm, errorNodeId, formToCondition, freeId, referencesTo, renameNode, type Obj } from "./graphOps";

describe("condition form", () => {
  it("round-trips flags, negated flags and scale comparisons", () => {
    const condition: Obj = { any: [{ flag: "was_rude" }, { not: { flag: "aisle_cleared" } }, { scale: "loyalty", op: "<", value: 70 }] };
    const form = conditionToForm(condition)!;
    expect(form.mode).toBe("any");
    expect(form.clauses).toHaveLength(3);
    expect(formToCondition(form)).toEqual(condition);
  });

  it("treats a missing condition as an empty form and an empty form as no condition", () => {
    expect(conditionToForm(undefined)).toEqual({ mode: "all", clauses: [] });
    expect(formToCondition({ mode: "all", clauses: [] })).toBeUndefined();
  });

  it("writes a single clause without a wrapper and reads legacy min_*", () => {
    expect(formToCondition({ mode: "all", clauses: [{ kind: "flag", flag: "x", negate: false }] })).toEqual({ flag: "x" });
    expect(conditionToForm({ min_safety: 40 })).toEqual({
      mode: "all",
      clauses: [{ kind: "scale", scale: "safety", op: ">=", value: 40 }],
    });
  });

  it("refuses nested structures so they are edited as JSON instead of being lost", () => {
    expect(conditionToForm({ all: [{ any: [{ flag: "a" }] }] })).toBeNull();
    expect(conditionToForm({ not: { all: [] } })).toBeNull();
  });
});

const graph: Obj = {
  start_node: "a",
  nodes: {
    a: { text: "", timer_seconds: 10, timeout: { next_node: "b" }, choices: [{ id: "x", text: "", next_node: "b" }] },
    b: { text: "", choices: [{ id: "y", text: "", transitions: [{ condition: { flag: "f" }, next_node: "a" }, { next_node: "c" }] }] },
    c: { text: "", is_ending: true, ending_summary: "" },
  },
};

describe("graph edits", () => {
  it("renames a node and every reference to it", () => {
    const renamed = renameNode(graph, "a", "start");
    expect(renamed.start_node).toBe("start");
    const nodes = renamed.nodes as Obj;
    expect(Object.keys(nodes)).toEqual(["start", "b", "c"]);
    expect(((nodes.b as Obj).choices as Obj[])[0].transitions).toEqual([
      { condition: { flag: "f" }, next_node: "start" },
      { next_node: "c" },
    ]);
    expect(graph.start_node).toBe("a"); // input untouched
  });

  it("does not rename onto an existing id", () => {
    expect(renameNode(graph, "a", "b")).toBe(graph);
  });

  it("lists references before deleting", () => {
    expect(referencesTo(graph, "b").sort()).toEqual(["a"]);
    expect(referencesTo(graph, "a").sort()).toEqual(["b", "start_node"]);
  });

  it("finds a free id and maps validator errors to nodes", () => {
    expect(freeId(["node", "node_2"], "node")).toBe("node_3");
    expect(errorNodeId("nodes.suitcase.choices[0].next_node: points to unknown node 'x'")).toBe("suitcase");
    expect(errorNodeId("graph.start_node: must name an existing node")).toBeNull();
  });
});
