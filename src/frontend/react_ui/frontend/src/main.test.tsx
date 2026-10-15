import { describe, it, expect, vi } from "vitest";

describe("main.tsx", () => {
  it("throws when root element missing", async () => {
    const spy = vi.spyOn(document, "getElementById").mockImplementation(() => null);

    await expect(import("./main")).rejects.toThrow("Root element not found");

    spy.mockRestore();
  });
});
