import { useEffect, useRef } from "react";
import type { ClockTimeRefs } from "./useClockTime";
import { renderClock } from "./clockRenderer";

export function useClockCanvas(timeRefs: ClockTimeRefs): React.RefObject<HTMLCanvasElement | null> {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animRef = useRef<number>(0);

  const { serverAnchorRef, wallAnchorRef, controllerRef, readyRef } = timeRefs;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const draw = () => {
      if (!readyRef.current) {
        animRef.current = requestAnimationFrame(draw);
        return;
      }

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const elapsed = (performance.now() - wallAnchorRef.current) / 1000;
      const now = new Date(serverAnchorRef.current.getTime() + elapsed * 1000);

      const controller = controllerRef.current;
      controller.update(now);

      renderClock(canvas, ctx, { hands: controller._clockHands, now });

      animRef.current = requestAnimationFrame(draw);
    };

    animRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animRef.current);
    };
  }, [serverAnchorRef, wallAnchorRef, controllerRef, readyRef]);

  return canvasRef;
}
