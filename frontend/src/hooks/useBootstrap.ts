import { useCallback, useEffect, useState } from "react";
import { getBootstrap, reload as reloadApi, waitForPywebviewReady } from "../api/client";
import type { Bootstrap } from "../types";

export function useBootstrap() {
  const [data, setData] = useState<Bootstrap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      await waitForPywebviewReady();
      const b = await getBootstrap();
      setData(b);
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const b = await reloadApi();
      setData(b);
      setError(null);
      return b;
    } catch (e) {
      setError(String(e));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, reload };
}
