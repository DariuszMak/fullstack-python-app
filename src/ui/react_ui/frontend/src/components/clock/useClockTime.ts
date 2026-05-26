import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";
import { ClockController } from "../clockController";
import { getApiBaseUrl } from "../../config";

type ClockStatus = "loading" | "ok" | "error";

export interface ClockTimeRefs {
  serverAnchorRef: RefObject<Date>;
  wallAnchorRef: RefObject<number>;
  controllerRef: RefObject<ClockController>;
  readyRef: RefObject<boolean>;
}

interface UseClockTimeResult extends ClockTimeRefs {
  datetime: string | null;
  status: ClockStatus;
  handleReload: () => Promise<void>;
}

async function fetchTimeData(): Promise<{ datetime: string }> {
  const res = await fetch(`${getApiBaseUrl()}/api/v1/time`);
  if (!res.ok) throw new Error(`HTTP ${String(res.status)}`);
  return (await res.json()) as { datetime: string };
}

function applyTimeData(
  data: { datetime: string },
  refs: {
    serverAnchorRef: RefObject<Date>;
    wallAnchorRef: RefObject<number>;
    controllerRef: RefObject<ClockController>;
    readyRef: RefObject<boolean>;
  },
): void {
  const serverDate = new Date(data.datetime);

  (refs.serverAnchorRef as { current: Date }).current = serverDate;
  (refs.wallAnchorRef as { current: number }).current = performance.now();
  (refs.controllerRef as { current: ClockController }).current.reset(serverDate);
  (refs.readyRef as { current: boolean }).current = true;
}

export function useClockTime(): UseClockTimeResult {
  const serverAnchorRef = useRef<Date>(new Date(0));
  const wallAnchorRef = useRef<number>(0);
  const controllerRef = useRef<ClockController>(new ClockController(new Date(0)));
  const readyRef = useRef<boolean>(false);

  const [datetime, setDatetime] = useState<string | null>(null);

  const [status, setStatus] = useState<ClockStatus>("loading");

  const handleReload = async () => {
    setStatus("loading");
    try {
      const data = await fetchTimeData();
      applyTimeData(data, { serverAnchorRef, wallAnchorRef, controllerRef, readyRef });
      setDatetime(data.datetime);
      setStatus("ok");
    } catch {
      setStatus("error");
    }
  };

  useEffect(() => {
    fetchTimeData()
      .then((data) => {
        applyTimeData(data, { serverAnchorRef, wallAnchorRef, controllerRef, readyRef });
        setDatetime(data.datetime);
        setStatus("ok");
      })
      .catch(() => {
        setStatus("error");
      });
  }, []);

  return {
    datetime,
    status,
    handleReload,
    serverAnchorRef,
    wallAnchorRef,
    controllerRef,
    readyRef,
  };
}
