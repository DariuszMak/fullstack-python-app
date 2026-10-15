import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useClockTime } from "./useClockTime";

describe("useClockTime", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("loads time successfully", async () => {
    vi.spyOn(window, "fetch").mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          datetime: "2025-01-01T12:00:00.000Z",
        }),
    } as Response);

    const { result } = renderHook(() => useClockTime());

    await waitFor(() => {
      expect(result.current.status).toBe("ok");
    });

    expect(result.current.datetime).toBe("2025-01-01T12:00:00.000Z");
  });

  it("handles fetch failure", async () => {
    vi.spyOn(window, "fetch").mockRejectedValue(new Error("network"));

    const { result } = renderHook(() => useClockTime());

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });
  });

  it("reload updates datetime", async () => {
    vi.spyOn(window, "fetch").mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          datetime: "2025-01-01T15:30:00.000Z",
        }),
    } as Response);

    const { result } = renderHook(() => useClockTime());

    await waitFor(() => {
      expect(result.current.status).toBe("ok");
    });

    await act(async () => {
      await result.current.handleReload();
    });

    expect(result.current.datetime).toBe("2025-01-01T15:30:00.000Z");
  });

  it("reload handles HTTP error", async () => {
    vi.spyOn(window, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
    } as Response);

    const { result } = renderHook(() => useClockTime());

    await waitFor(() => {
      expect(result.current.status).toBe("error");
    });
  });
});
