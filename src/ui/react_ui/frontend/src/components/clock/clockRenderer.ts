import {
  polarToCartesian,
  formatTime,
  clockHandsInRadians,
  type ClockHands,
} from "../clockHelpers";

interface RenderState {
  hands: ClockHands;
  now: Date;
}

function isDarkMode(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resizeCanvas(
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
): { size: number; cx: number; cy: number; radius: number } {
  const dpr = window.devicePixelRatio || 1;
  const size = canvas.clientWidth;

  if (canvas.width !== size * dpr || canvas.height !== size * dpr) {
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);
  }

  return {
    size,
    cx: size / 2,
    cy: size / 2,
    radius: size * 0.42,
  };
}

function drawFace(ctx: CanvasRenderingContext2D, cx: number, cy: number, radius: number): void {
  const isDark = isDarkMode();

  ctx.fillStyle = isDark ? "#1a1a1a" : "#ffffff";
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = isDark ? "#555" : "#ccc";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.stroke();
}

function drawTicks(ctx: CanvasRenderingContext2D, cx: number, cy: number, radius: number): void {
  const isDark = isDarkMode();

  for (let i = 0; i < 60; i++) {
    const angle = (i / 60) * Math.PI * 2;
    const isHour = i % 5 === 0;
    const outer = polarToCartesian(cx, cy, radius, angle);
    const inner = polarToCartesian(cx, cy, radius - (isHour ? 10 : 5), angle);

    ctx.strokeStyle = isDark ? "#888" : "#aaa";
    ctx.lineWidth = isHour ? 2.5 : 1;
    ctx.beginPath();
    ctx.moveTo(inner[0], inner[1]);
    ctx.lineTo(outer[0], outer[1]);
    ctx.stroke();
  }
}

function drawNumbers(ctx: CanvasRenderingContext2D, cx: number, cy: number, radius: number): void {
  const isDark = isDarkMode();
  const fontSize = Math.max(8, Math.floor(radius * 0.13));

  ctx.font = `${String(fontSize)}px system-ui, Arial, sans-serif`;
  ctx.fillStyle = isDark ? "#ddd" : "#333";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * Math.PI * 2;
    const [tx, ty] = polarToCartesian(cx, cy, radius - fontSize * 1.8, angle);
    const label = ((i + 11) % 12) + 1;
    ctx.fillText(String(label), tx, ty);
  }
}

function drawHands(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  hands: ClockHands,
): void {
  const isDark = isDarkMode();
  const radians = clockHandsInRadians(hands);

  const [hx, hy] = polarToCartesian(cx, cy, radius * 0.5, radians.hour);
  ctx.strokeStyle = isDark ? "#ffffff" : "#222";
  ctx.lineWidth = 6;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(hx, hy);
  ctx.stroke();

  const [mx, my] = polarToCartesian(cx, cy, radius * 0.7, radians.minute);
  ctx.strokeStyle = isDark ? "#cccccc" : "#444";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(mx, my);
  ctx.stroke();

  const [sx, sy] = polarToCartesian(cx, cy, radius * 0.88, radians.second);
  ctx.strokeStyle = "#ff3333";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.lineTo(sx, sy);
  ctx.stroke();

  ctx.fillStyle = isDark ? "#ff3333" : "#cc0000";
  ctx.beginPath();
  ctx.arc(cx, cy, 4, 0, Math.PI * 2);
  ctx.fill();
}

function drawTimeLabel(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  now: Date,
): void {
  const isDark = isDarkMode();
  const tfSize = Math.max(10, Math.floor(radius * 0.12));

  ctx.font = `${String(tfSize)}px "Consolas", monospace`;
  ctx.fillStyle = isDark ? "#96ffbe" : "#1a7a40";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(formatTime(now), cx, cy + radius * 0.62);
}

export function renderClock(
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  state: RenderState,
): void {
  const { size, cx, cy, radius } = resizeCanvas(canvas, ctx);
  ctx.clearRect(0, 0, size, size);
  drawFace(ctx, cx, cy, radius);
  drawTicks(ctx, cx, cy, radius);
  drawNumbers(ctx, cx, cy, radius);
  drawHands(ctx, cx, cy, radius, state.hands);
  drawTimeLabel(ctx, cx, cy, radius, state.now);
}
