import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Clock } from "./Clock";

vi.mock("./useClockCanvas", () => ({
  useClockCanvas: () => ({
    current: null,
  }),
}));

const handleReloadMock = vi.fn();

vi.mock("./useClockTime", () => ({
  useClockTime: () => ({
    datetime: "2025-01-01T12:00:00.000Z",
    status: "ok",
    handleReload: handleReloadMock,

    serverAnchorRef: { current: new Date() },
    wallAnchorRef: { current: 0 },
    controllerRef: { current: {} },
    readyRef: { current: true },
  }),
}));

describe("Clock", () => {
  beforeEach(() => {
    handleReloadMock.mockClear();
  });

  it("renders title", () => {
    render(<Clock />);

    expect(screen.getByText("Current datetime")).toBeInTheDocument();
  });

  it("renders datetime", () => {
    render(<Clock />);

    expect(screen.getByText("2025-01-01T12:00:00.000Z")).toBeInTheDocument();
  });

  it("renders reload button", () => {
    render(<Clock />);

    expect(
      screen.getByRole("button", {
        name: "Reload time",
      }),
    ).toBeInTheDocument();
  });

  it("calls reload handler", () => {
    render(<Clock />);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Reload time",
      }),
    );

    expect(handleReloadMock).toHaveBeenCalled();
  });

  it("renders canvas", () => {
    render(<Clock />);

    expect(document.querySelector("canvas")).toBeTruthy();
  });
});
