import { useClockTime } from "./useClockTime";
import { useClockCanvas } from "./useClockCanvas";

export function Clock() {
  const { datetime, status, handleReload, ...timeRefs } = useClockTime();
  const canvasRef = useClockCanvas(timeRefs);

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}>
      <h1 style={{ margin: 0 }}>Current datetime</h1>
      {datetime && <p style={{ margin: 0 }}>{datetime}</p>}

      <canvas
        ref={canvasRef}
        style={{
          width: "300px",
          height: "300px",
          borderRadius: "50%",
          display: "block",
        }}
      />

      <button onClick={() => void handleReload()} disabled={status === "loading"}>
        {status === "loading" ? "Loading…" : "Reload time"}
      </button>

      {status === "error" && <p style={{ color: "red", margin: 0 }}>Failed to load time</p>}
    </div>
  );
}
