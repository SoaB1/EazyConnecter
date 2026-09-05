import { useCallback, useRef, useState } from "react";

export interface ToastState {
  message: string;
  kind: "info" | "error";
}

export function useToast() {
  const [toast, setToast] = useState<ToastState | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = useCallback((message: string, kind: ToastState["kind"] = "info") => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setToast({ message, kind });
    timerRef.current = setTimeout(() => setToast(null), 4000);
  }, []);

  return { toast, show };
}
