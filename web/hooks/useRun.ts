"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, errorMessage, RunJob } from "@/lib/api";

const active = (job: RunJob | null) => !!job && ["queued", "running", "cancelling"].includes(job.status);

export function useRun(strategyId: string) {
  const [job, setJob] = useState<RunJob | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const pending = useRef(false);
  const generation = useRef(0);
  const storageKey = `screening:${strategyId}`;

  useEffect(() => {
    generation.current++;
    setJob(null);
    setError(null);
    setStarting(false);
    pending.current = false;
    try { setJobId(sessionStorage.getItem(storageKey)); } catch { setJobId(null); }
    return () => { generation.current++; };
  }, [storageKey]);

  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const next = await api.getRun(jobId!, controller.signal);
        if (controller.signal.aborted) return;
        setJob(next);
        setError(next.error);
        if (active(next)) timer = setTimeout(poll, 1000);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(errorMessage(err));
        if (err instanceof ApiError && err.status === 404) {
          try { sessionStorage.removeItem(storageKey); } catch {}
          setJobId(null);
          setJob(null);
        } else timer = setTimeout(poll, 4000);
      }
    }
    poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [jobId, retry, storageKey]);

  const start = useCallback(async () => {
    if (!strategyId || pending.current) return;
    const version = generation.current;
    pending.current = true;
    setStarting(true);
    setError(null);
    try {
      const next = await api.startRun(strategyId);
      try {
        sessionStorage.setItem(storageKey, next.id);
        sessionStorage.setItem("screening:selected", strategyId);
      } catch {}
      if (version !== generation.current) return;
      setJob(next);
      setJobId(next.id);
    } catch (err) {
      if (version === generation.current) setError(errorMessage(err));
    } finally {
      if (version === generation.current) { setStarting(false); pending.current = false; }
    }
  }, [strategyId, storageKey]);

  async function cancel() {
    if (!jobId) return;
    const version = generation.current;
    try {
      const next = await api.cancelRun(jobId);
      if (version === generation.current) { setJob(next); setRetry(value => value + 1); }
    } catch (err) { if (version === generation.current) setError(errorMessage(err)); }
  }

  return { job, result: job?.result ?? null, running: starting || active(job) || (!!jobId && !job), error, start, cancel };
}
