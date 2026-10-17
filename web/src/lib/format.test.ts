import { describe, expect, it } from "vitest";
import { decimalSign, fmtDecimal, fmtDuration, fmtRelative, shortHash, sumDecimals } from "./format";

describe("fmtDecimal", () => {
  it("rounds half-up on the digit string", () => {
    expect(fmtDecimal("37.4912", 2)).toBe("37,49");
    expect(fmtDecimal("0.005", 2)).toBe("0,01");
    expect(fmtDecimal("1234567.895", 2)).toBe("1.234.567,90");
  });

  it("keeps tiny non-zero values visible", () => {
    expect(fmtDecimal("0.0000001", 4)).toBe("<0,0001");
    expect(fmtDecimal("-0.0000001", 4)).toBe("−<0,0001");
  });

  it("handles signs, exponents and zero places", () => {
    expect(fmtDecimal("0.0123", 4, { signed: true })).toBe("+0,0123");
    expect(fmtDecimal("-0.73544718", 4)).toBe("−0,7354");
    expect(fmtDecimal("1E+2", 0)).toBe("100");
    expect(fmtDecimal("1.5e-3", 4)).toBe("0,0015");
    expect(fmtDecimal("0", 2, { signed: true })).toBe("0,00");
  });

  it("rejects garbage", () => {
    expect(fmtDecimal(null)).toBe("—");
    expect(fmtDecimal("NaN")).toBe("—");
    expect(fmtDecimal("1e5000")).toBe("—");
  });
});

describe("decimalSign", () => {
  it("reads sign without floats", () => {
    expect(decimalSign("-0.0001")).toBe(-1);
    expect(decimalSign("-0.000")).toBe(0);
    expect(decimalSign("12")).toBe(1);
    expect(decimalSign("abc")).toBeNull();
  });
});

describe("durations", () => {
  it("formats compactly", () => {
    expect(fmtDuration(42)).toBe("42 sn");
    expect(fmtDuration(600)).toBe("10 dk");
    expect(fmtDuration(3900)).toBe("1 sa 5 dk");
    expect(fmtRelative(100, 103)).toBe("şimdi");
    expect(fmtRelative(100, 700)).toBe("10 dk önce");
    expect(fmtRelative(1000, 100)).toBe("15 dk sonra");
  });

  it("shortens hashes", () => {
    expect(shortHash("a".repeat(64))).toBe(`${"a".repeat(10)}…${"a".repeat(8)}`);
    expect(shortHash("abc")).toBe("abc");
  });
});


describe("sumDecimals", () => {
  it("sums monetary strings exactly without binary rounding", () => {
    expect(sumDecimals(["0.1", "0.2"])).toBe("0.3");
    expect(sumDecimals(["10000000000000000.001", "0.002"])).toBe("10000000000000000.003");
    expect(sumDecimals(["-0.01", "1e-3", "1E+2"])).toBe("99.991");
    expect(sumDecimals([])).toBe("0");
  });
});
