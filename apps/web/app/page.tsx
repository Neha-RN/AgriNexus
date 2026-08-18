"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

type ConnectionState = "checking" | "connected" | "unavailable";

export default function Home() {
  const [state, setState] = useState<ConnectionState>("checking");

  useEffect(() => {
    let isMounted = true;

    getHealth()
      .then(() => {
        if (isMounted) {
          setState("connected");
        }
      })
      .catch(() => {
        if (isMounted) {
          setState("unavailable");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const statusConfig: Record<
    ConnectionState,
    { label: string; dot: string; text: string }
  > = {
    checking: {
      label: "Checking backend connection...",
      dot: "bg-yellow-500",
      text: "text-yellow-600",
    },
    connected: {
      label: "Backend connected",
      dot: "bg-green-500",
      text: "text-green-600",
    },
    unavailable: {
      label: "Backend unavailable",
      dot: "bg-red-500",
      text: "text-red-600",
    },
  };

  const current = statusConfig[state];

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-md space-y-6 text-center">
        <h1 className="text-4xl font-bold tracking-tight">AgriNexus</h1>

        <p className="text-gray-500">
          Connecting agricultural data and infrastructure.
        </p>

        <div className="flex items-center justify-center gap-2 rounded-lg border border-gray-200 px-4 py-3">
          <span
            className={`h-2.5 w-2.5 rounded-full ${current.dot}`}
          />

          <span className={`text-sm font-medium ${current.text}`}>
            {current.label}
          </span>
        </div>
      </div>
    </main>
  );
}