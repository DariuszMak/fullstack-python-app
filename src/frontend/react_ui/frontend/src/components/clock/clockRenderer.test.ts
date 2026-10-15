/* eslint-disable @typescript-eslint/unbound-method */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderClock } from "./clockRenderer";

function createMockContext(): CanvasRenderingContext2D {
  return {
    canvas: document.createElement("canvas"),
    save: vi.fn(),
    restore: vi.fn(),
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    arc: vi.fn(),
    fill: vi.fn(),
    stroke: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    fillText: vi.fn(),
    strokeRect: vi.fn(),

    font: "",
    fillStyle: "",
    strokeStyle: "",
    lineWidth: 1,
    textAlign: "center",
    textBaseline: "middle",

    scale: vi.fn(),
  } as unknown as CanvasRenderingContext2D;
}

describe("renderClock", () => {
  let ctx: CanvasRenderingContext2D;
  let canvas: HTMLCanvasElement;

  beforeEach(() => {
    ctx = createMockContext();
    canvas = document.createElement("canvas");
    canvas.width = 200;
    canvas.height = 200;

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it("renders without crashing", () => {
    renderClock(canvas, ctx, {
      hands: {
        hour: 0,
        minute: 0,
        second: 0,
      },
      now: new Date(),
    });

    const clearRectMock = ctx.clearRect as unknown as ReturnType<typeof vi.fn>;

    expect(clearRectMock).toHaveBeenCalled();
  });
});
