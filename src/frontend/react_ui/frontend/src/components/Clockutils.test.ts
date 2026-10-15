import { describe, it, expect, afterEach } from "vitest";
import { getApiBaseUrl } from "../config";

import { PID } from "./pid";
import { PIDMovementStrategy, EasingMovementStrategy, TickMovementStrategy } from "./strategies";
import {
  calculateHandAngles,
  clockHandsInRadians,
  polarToCartesian,
  formatTime,
  type ClockHands,
} from "./clockHelpers";
import { ClockController } from "./clockController";

import {
  PID as PIDFromUtils,
  PIDMovementStrategy as PIDStrategyFromUtils,
  calculateHandAngles as calcFromUtils,
  polarToCartesian as polarFromUtils,
  formatTime as formatFromUtils,
  ClockController as ControllerFromUtils,
} from "./clockUtils";

function localDate(h: number, m: number, s: number, ms = 0): Date {
  return new Date(2025, 0, 1, h, m, s, ms);
}

function runTicks(
  controller: ClockController,
  startDate: Date,
  ticks: number,
  stepMs: number,
): ClockController {
  for (let i = 1; i <= ticks; i++) {
    controller.update(new Date(startDate.getTime() + i * stepMs));
  }
  return controller;
}

describe("PID", () => {
  it("first update applies kp, ki, kd correctly", () => {
    const pid = new PID(1.0, 0.1, 0.5);
    expect(pid.update(1.0)).toBeCloseTo(1.6);
  });

  it("second update uses accumulated integral and previous error", () => {
    const pid = new PID(1.0, 0.1, 0.5);
    pid.update(1.0);
    expect(pid.update(0.5)).toBeCloseTo(0.4);
  });

  it("reset zeroes internal state", () => {
    const pid = new PID(1.0, 0.1, 0.5);
    pid.update(1.0);
    pid.update(0.5);
    expect(pid._integral).not.toBe(0);
    expect(pid._prevError).not.toBe(0);
    pid.reset();
    expect(pid._integral).toBe(0);
    expect(pid._prevError).toBe(0);
  });

  it("after reset the same input gives the same result as first call", () => {
    const pid = new PID(0.1, 0.1, 0.0);
    const first = pid.update(5.0);
    pid.update(3.0);
    pid.reset();
    expect(pid.update(5.0)).toBeCloseTo(first);
  });

  it("re-exported from clockUtils is the same class", () => {
    expect(new PIDFromUtils(1, 0, 0).update(2)).toBeCloseTo(new PID(1, 0, 0).update(2));
  });
});

describe("PIDMovementStrategy", () => {
  it("moves current toward target", () => {
    const s = new PIDMovementStrategy(0.1, 0, 0);
    const v1 = s.update(0, 10);
    expect(v1).toBeGreaterThan(0);
    expect(s.update(v1, 10)).toBeGreaterThan(v1);
  });

  it("reset causes same output as first call", () => {
    const s = new PIDMovementStrategy(0.1, 0.1, 0);
    const first = s.update(0, 10);
    s.update(5, 10);
    s.reset();
    expect(s.update(0, 10)).toBeCloseTo(first);
  });

  it("re-exported from clockUtils works identically", () => {
    const a = new PIDMovementStrategy(0.15, 0.005, 0.005);
    const b = new PIDStrategyFromUtils(0.15, 0.005, 0.005);
    expect(a.update(0, 30)).toBeCloseTo(b.update(0, 30));
  });
});

describe("EasingMovementStrategy", () => {
  it("moves fractionally toward target", () => {
    const s = new EasingMovementStrategy(0.2);
    expect(s.update(0, 10)).toBeCloseTo(2.0);
    expect(s.update(5, 15)).toBeCloseTo(7.0);
  });

  it("factor 1.0 snaps directly to target", () => {
    expect(new EasingMovementStrategy(1.0).update(3, 10)).toBeCloseTo(10);
  });

  it("factor 0.0 stays at current", () => {
    expect(new EasingMovementStrategy(0.0).update(3, 10)).toBeCloseTo(3);
  });

  it("reset is a no-op (stateless)", () => {
    const s = new EasingMovementStrategy(0.5);
    s.reset();
    expect(s.update(0, 10)).toBeCloseTo(5);
  });
});

describe("TickMovementStrategy", () => {
  it("snaps immediately to target", () => {
    const s = new TickMovementStrategy();
    expect(s.update(5, 20)).toBeCloseTo(20);
    expect(s.update(-10, -3.5)).toBeCloseTo(-3.5);
  });
});

describe("calculateHandAngles", () => {
  it("elapsed 0 at midnight gives all zeros", () => {
    const h = calculateHandAngles(localDate(0, 0, 0), 0);
    expect(h.second).toBeCloseTo(0);
    expect(h.minute).toBeCloseTo(0);
    expect(h.hour).toBeCloseTo(0);
  });

  it("elapsed 0 at noon gives all zeros (12-hour wrap in start)", () => {
    const h = calculateHandAngles(localDate(12, 0, 0), 0);
    expect(h.second).toBeCloseTo(0);
    expect(h.minute).toBeCloseTo(0);
    expect(h.hour).toBeCloseTo(0);
  });

  it("elapsed 0 at half past three", () => {
    const h = calculateHandAngles(localDate(3, 30, 0), 0);
    expect(h.second).toBeCloseTo(3 * 3600 + 30 * 60);
    expect(h.minute).toBeCloseTo((3 * 3600 + 30 * 60) / 60);
    expect(h.hour).toBeCloseTo((3 * 3600 + 30 * 60) / 3600);
  });

  it("elapsed 0 at 23:59:59 gives near-maximum totals", () => {
    const h = calculateHandAngles(localDate(23, 59, 59), 0);

    const total = 11 * 3600 + 59 * 60 + 59;
    expect(h.second).toBeCloseTo(total, 3);
    expect(h.minute).toBeCloseTo(total / 60, 5);
    expect(h.hour).toBeCloseTo(total / 3600, 5);
  });

  it("milliseconds in start contribute fractional seconds", () => {
    const h0 = calculateHandAngles(localDate(0, 0, 30, 0), 0);
    const h500 = calculateHandAngles(localDate(0, 0, 30, 500), 0);
    expect(h500.second).toBeGreaterThan(h0.second);
  });

  it("elapsed seconds accumulate without wrapping", () => {
    const h = calculateHandAngles(localDate(0, 0, 0), 12 * 3600);
    expect(h.second).toBeCloseTo(43200);
    expect(h.minute).toBeCloseTo(720);
    expect(h.hour).toBeCloseTo(12);
  });

  it("elapsed seconds accumulate past one full day", () => {
    const totalMs = 23 * 3600 * 1000 + 59 * 60 * 1000 + 59 * 1000 + 999;
    const h = calculateHandAngles(localDate(0, 0, 0), totalMs / 1000);
    expect(h.second).toBeCloseTo(totalMs / 1000, 2);
    expect(h.minute).toBeCloseTo(totalMs / 1000 / 60, 4);
    expect(h.hour).toBeCloseTo(totalMs / 1000 / 3600, 5);
  });

  it("elapsed seconds accumulate past one month", () => {
    const totalMs = 37 * 24 * 3600 * 1000 + 65 * 60 * 1000 + 61 * 1000 + 2;
    const h = calculateHandAngles(localDate(0, 0, 0), totalMs / 1000);
    expect(h.second).toBeCloseTo(totalMs / 1000, 1);
    expect(h.minute).toBeCloseTo(totalMs / 1000 / 60, 3);
    expect(h.hour).toBeCloseTo(totalMs / 1000 / 3600, 4);
  });

  it("PM hour (15:30) produces same result as AM (3:30) with elapsed=0", () => {
    const am = calculateHandAngles(localDate(3, 30, 0), 0);
    const pm = calculateHandAngles(localDate(15, 30, 0), 0);
    expect(pm.second).toBeCloseTo(am.second, 5);
    expect(pm.minute).toBeCloseTo(am.minute, 5);
    expect(pm.hour).toBeCloseTo(am.hour, 5);
  });

  it("re-exported from clockUtils produces identical results", () => {
    const a = calculateHandAngles(localDate(9, 15, 30, 250), 120);
    const b = calcFromUtils(localDate(9, 15, 30, 250), 120);
    expect(a.second).toBeCloseTo(b.second);
    expect(a.minute).toBeCloseTo(b.minute);
    expect(a.hour).toBeCloseTo(b.hour);
  });
});

describe("clockHandsInRadians", () => {
  it("zero hands give zero radians", () => {
    const r = clockHandsInRadians({ second: 0, minute: 0, hour: 0 });
    expect(r.second).toBeCloseTo(0);
    expect(r.minute).toBeCloseTo(0);
    expect(r.hour).toBeCloseTo(0);
  });

  it("30 seconds → π radians (half circle)", () => {
    expect(clockHandsInRadians({ second: 30, minute: 0, hour: 0 }).second).toBeCloseTo(Math.PI);
  });

  it("30 minutes → π radians (half circle)", () => {
    expect(clockHandsInRadians({ second: 0, minute: 30, hour: 0 }).minute).toBeCloseTo(Math.PI);
  });

  it("6 hours → π radians (half circle)", () => {
    expect(clockHandsInRadians({ second: 0, minute: 0, hour: 6 }).hour).toBeCloseTo(Math.PI);
  });

  it("15 seconds → π/2 radians (quarter circle)", () => {
    expect(clockHandsInRadians({ second: 15, minute: 0, hour: 0 }).second).toBeCloseTo(Math.PI / 2);
  });

  it("unbounded 60 seconds wraps to 0 radians (full revolution)", () => {
    expect(clockHandsInRadians({ second: 60, minute: 0, hour: 0 }).second).toBeCloseTo(0);
  });

  it("unbounded 90 seconds wraps to π radians", () => {
    expect(clockHandsInRadians({ second: 90, minute: 0, hour: 0 }).second).toBeCloseTo(Math.PI);
  });

  it("unbounded 12 hours wraps to 0 radians (full revolution)", () => {
    expect(clockHandsInRadians({ second: 0, minute: 0, hour: 12 }).hour).toBeCloseTo(0);
  });

  it("formula for non-wrapped values", () => {
    const hands: ClockHands = { second: 15, minute: 30, hour: 6 };
    const r = clockHandsInRadians(hands);
    expect(r.second).toBeCloseTo((15 / 60) * 2 * Math.PI);
    expect(r.minute).toBeCloseTo((30 / 60) * 2 * Math.PI);
    expect(r.hour).toBeCloseTo((6 / 12) * 2 * Math.PI);
  });

  it("large unbounded values produce same radian as their wrapped equivalent", () => {
    const large = clockHandsInRadians({ second: 3723, minute: 3723 / 60, hour: 3723 / 3600 });
    const small = clockHandsInRadians({
      second: 3,
      minute: (3723 / 60) % 60,
      hour: (3723 / 3600) % 12,
    });
    expect(large.second).toBeCloseTo(small.second, 8);
    expect(large.minute).toBeCloseTo(small.minute, 8);
    expect(large.hour).toBeCloseTo(small.hour, 8);
  });
});

describe("polarToCartesian", () => {
  it("angle 0 points straight up (north)", () => {
    const [x, y] = polarToCartesian(100, 100, 50, 0);
    expect(x).toBeCloseTo(100);
    expect(y).toBeCloseTo(50);
  });

  it("angle π/2 points right (east)", () => {
    const [x, y] = polarToCartesian(0, 0, 1, Math.PI / 2);
    expect(x).toBeCloseTo(1);
    expect(y).toBeCloseTo(0);
  });

  it("angle π points straight down (south)", () => {
    const [x, y] = polarToCartesian(0, 0, 10, Math.PI);
    expect(x).toBeCloseTo(0, 5);
    expect(y).toBeCloseTo(10, 5);
  });

  it("angle 3π/2 points left (west)", () => {
    const [x, y] = polarToCartesian(0, 0, 1, (3 * Math.PI) / 2);
    expect(x).toBeCloseTo(-1);
    expect(y).toBeCloseTo(0, 5);
  });

  it("respects center offset", () => {
    const [x, y] = polarToCartesian(50, 80, 20, 0);
    expect(x).toBeCloseTo(50);
    expect(y).toBeCloseTo(60);
  });

  it("re-exported from clockUtils produces identical results", () => {
    const a = polarToCartesian(100, 100, 50, Math.PI / 4);
    const b = polarFromUtils(100, 100, 50, Math.PI / 4);
    expect(a[0]).toBeCloseTo(b[0]);
    expect(a[1]).toBeCloseTo(b[1]);
  });
});

describe("formatTime", () => {
  it("formats HH:MM:SS.mmm using local time fields", () => {
    const dt = new Date(2025, 0, 1, 3, 4, 5, 678);
    const result = formatTime(dt);
    const hh = String(dt.getHours()).padStart(2, "0");
    const mm = String(dt.getMinutes()).padStart(2, "0");
    const ss = String(dt.getSeconds()).padStart(2, "0");
    expect(result).toBe(`${hh}:${mm}:${ss}.678`);
  });

  it("pads single-digit fields with zeros", () => {
    const dt = new Date(2025, 0, 1, 1, 2, 3, 4);
    const result = formatTime(dt);
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}\.\d{3}$/);
    expect(result.endsWith(".004")).toBe(true);
  });

  it("milliseconds are floored, not rounded", () => {
    const dt = new Date(2025, 0, 1, 0, 0, 0, 999);
    expect(formatTime(dt).endsWith(".999")).toBe(true);
  });

  it("re-exported from clockUtils produces identical result", () => {
    const dt = new Date(2025, 0, 1, 8, 30, 15, 123);
    expect(formatFromUtils(dt)).toBe(formatTime(dt));
  });
});

describe("ClockController", () => {
  it("starts with all hands at zero", () => {
    const c = new ClockController();
    expect(c._clockHands).toEqual({ second: 0, minute: 0, hour: 0 });
  });

  it("update advances hands from zero toward target", () => {
    const start = localDate(3, 30, 45);
    const c = new ClockController(start);
    c.update(new Date(start.getTime() + 1000));
    expect(c._clockHands.second).toBeGreaterThan(0);
    expect(c._clockHands.minute).toBeGreaterThan(0);
    expect(c._clockHands.hour).toBeGreaterThan(0);
  });

  it("repeated updates bring hands monotonically closer to target (eventually)", () => {
    const start = localDate(6, 0, 0);
    const c = new ClockController(start);

    runTicks(c, start, 40_000, 15);

    const target = calculateHandAngles(start, 10 * 60);

    expect(Math.abs(target.second - c._clockHands.second)).toBeLessThan(1);
    expect(Math.abs(target.minute - c._clockHands.minute)).toBeLessThan(1);
    expect(Math.abs(target.hour - c._clockHands.hour)).toBeLessThan(1);
  });

  it("reset zeroes all hands and accepts a new start anchor", () => {
    const start = localDate(3, 0, 0);
    const c = new ClockController(start);
    runTicks(c, start, 100, 15);
    expect(c._clockHands.second).toBeGreaterThan(0);

    const newStart = localDate(9, 0, 0);
    c.reset(newStart);
    expect(c._clockHands).toEqual({ second: 0, minute: 0, hour: 0 });
  });

  it("after reset, same first update gives same result as a fresh controller", () => {
    const start = localDate(9, 15, 0);
    const tick = new Date(start.getTime() + 15);

    const c1 = new ClockController(start);
    c1.update(tick);

    const c2 = new ClockController(localDate(3, 0, 0));
    c2.update(new Date(localDate(3, 0, 0).getTime() + 15));
    c2.reset(start);
    c2.update(tick);

    expect(c1._clockHands.second).toBeCloseTo(c2._clockHands.second, 10);
    expect(c1._clockHands.minute).toBeCloseTo(c2._clockHands.minute, 10);
    expect(c1._clockHands.hour).toBeCloseTo(c2._clockHands.hour, 10);
  });

  it("re-exported from clockUtils is the same class", () => {
    const start = localDate(1, 2, 3);
    const c = new ControllerFromUtils(start);
    c.update(new Date(start.getTime() + 1000));
    expect(c._clockHands.second).toBeGreaterThan(0);
  });

  it("clockHandsInRadians on controller output always stays within [0, 2π)", () => {
    const start = localDate(11, 55, 0);
    const c = new ClockController(start);

    for (let i = 1; i <= 60_000; i++) {
      c.update(new Date(start.getTime() + i * 15));
    }
    const r = clockHandsInRadians(c._clockHands);
    expect(r.second).toBeGreaterThanOrEqual(0);
    expect(r.second).toBeLessThan(2 * Math.PI);
    expect(r.minute).toBeGreaterThanOrEqual(0);
    expect(r.minute).toBeLessThan(2 * Math.PI);
    expect(r.hour).toBeGreaterThanOrEqual(0);
    expect(r.hour).toBeLessThan(2 * Math.PI);
  });
});

describe("calculateHandAngles — timezone handling", () => {
  it("uses local time fields, not UTC (regression: hands were 2h behind in UTC+2)", () => {
    const local14 = new Date(2026, 3, 5, 14, 49, 14, 0);
    const h = calculateHandAngles(local14, 0);
    const expectedTotalSeconds = 2 * 3600 + 49 * 60 + 14;
    expect(h.second).toBeCloseTo(expectedTotalSeconds);
    expect(h.hour).toBeCloseTo(expectedTotalSeconds / 3600);
  });
});

describe("getApiBaseUrl", () => {
  afterEach(() => {
    delete window.__APP_CONFIG__;
  });

  it("returns __APP_CONFIG__.apiBaseUrl when injected", () => {
    window.__APP_CONFIG__ = { apiBaseUrl: "http://192.168.1.10:9000" };
    expect(getApiBaseUrl()).toBe("http://192.168.1.10:9000");
  });

  it("falls back to VITE_BACKEND_URL env var when no config injected", () => {
    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });
});
