import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useClockCanvas } from "./useClockCanvas";
import { ClockController } from "../clockController";

describe("useClockCanvas", () => {
  beforeEach(() => {
    vi.spyOn(window, "requestAnimationFrame").mockImplementation((cb) => {
      cb(0);
      return 1;
    });

    vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => undefined);
  });

  it("returns canvas ref", () => {
    const { result } = renderHook(() =>
      useClockCanvas({
        serverAnchorRef: {
          current: new Date(),
        },
        wallAnchorRef: {
          current: 0,
        },
        controllerRef: {
          current: new ClockController(),
        },
        readyRef: {
          current: false,
        },
      }),
    );

    expect(result.current).toBeDefined();
  });
});
