import { describe, expect, it } from "vitest";
import { formatSeconds, remainingAtReceiptMs, remainingNowMs, signed } from "./time";

describe("countdown", () => {
  it("uses server time, not the device clock", () => {
    expect(remainingAtReceiptMs("2026-09-25T12:00:20Z", "2026-09-25T12:00:05Z")).toBe(15_000);
  });

  it("returns null without a deadline and never goes below zero", () => {
    expect(remainingAtReceiptMs(null, "2026-09-25T12:00:00Z")).toBeNull();
    expect(remainingAtReceiptMs("2026-09-25T12:00:00Z", "2026-09-25T12:00:09Z")).toBe(0);
  });

  it("subtracts only elapsed monotonic time", () => {
    expect(remainingNowMs(15_000, 1_000, 6_000)).toBe(10_000);
    expect(remainingNowMs(15_000, 1_000, 99_000)).toBe(0);
  });

  it("shows whole seconds rounded up", () => {
    expect(formatSeconds(10_001)).toBe("11");
    expect(formatSeconds(10_000)).toBe("10");
  });

  it("formats deltas with a real minus sign", () => {
    expect(signed(5)).toBe("+5");
    expect(signed(-20)).toBe("−20");
    expect(signed(0)).toBe("0");
  });
});
