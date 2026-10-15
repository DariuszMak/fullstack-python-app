export interface ClockHands {
  second: number;
  minute: number;
  hour: number;
}

export function calculateHandAngles(startDt: Date, elapsedSeconds: number): ClockHands {
  const h = startDt.getHours() % 12;
  const m = startDt.getMinutes();
  const s = startDt.getSeconds();
  const ms = startDt.getMilliseconds();

  const startTotalSeconds = h * 3600 + m * 60 + s + ms / 1000;
  const totalSeconds = startTotalSeconds + elapsedSeconds;

  return {
    second: totalSeconds,
    minute: totalSeconds / 60,
    hour: totalSeconds / 3600,
  };
}

export function clockHandsInRadians(hands: ClockHands): ClockHands {
  return {
    second: (((hands.second % 60) + 60) % 60) * (Math.PI / 30),
    minute: (((hands.minute % 60) + 60) % 60) * (Math.PI / 30),
    hour: (((hands.hour % 12) + 12) % 12) * (Math.PI / 6),
  };
}
export function polarToCartesian(
  cx: number,
  cy: number,
  length: number,
  angleRad: number,
): [number, number] {
  return [cx + Math.sin(angleRad) * length, cy - Math.cos(angleRad) * length];
}

export function formatTime(dt: Date): string {
  const h = String(dt.getHours()).padStart(2, "0");
  const m = String(dt.getMinutes()).padStart(2, "0");
  const s = String(dt.getSeconds()).padStart(2, "0");
  const ms = String(Math.floor(dt.getMilliseconds())).padStart(3, "0");
  return `${h}:${m}:${s}.${ms}`;
}
