import type { ToastState } from "../hooks/useToast";

export function Toast({ toast }: { toast: ToastState | null }) {
  if (!toast) return null;
  return (
    <div className={`ec-toast ec-toast--${toast.kind}`} role="status">
      {toast.message}
    </div>
  );
}
