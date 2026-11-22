import { useEffect, useState } from "react";

type ApiStatus = "checking" | "ok" | "unreachable";

/** Placeholder shell for the hello-world deploy: proves the site, the /api rewrite and the backend are wired. */
export default function App() {
  const [status, setStatus] = useState<ApiStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((response) => setStatus(response.ok ? "ok" : "unreachable"))
      .catch((error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) setStatus("unreachable");
      });
    return () => controller.abort();
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-3xl font-semibold">recyclops-ai</h1>
      <p className="mt-2 text-muted">A clean-air day planner for your household, built on live air-quality data.</p>
      <p className="mt-6" aria-live="polite">
        Service status: <strong>{status}</strong>
      </p>
    </main>
  );
}
