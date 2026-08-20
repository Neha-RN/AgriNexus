"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { getHealth, getFields, type Field } from "@/lib/api";

const FieldMap = dynamic(() => import("@/components/FieldMap"), {
  ssr: false,
});

type ConnectionState = "checking" | "connected" | "unavailable";
type FieldsState = "loading" | "loaded" | "error";

export default function Home() {
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("checking");

  const [fieldsState, setFieldsState] =
    useState<FieldsState>("loading");

  const [fields, setFields] = useState<Field[]>([]);
  const [fieldsError, setFieldsError] =
    useState<string | null>(null);

  const [selectedField, setSelectedField] =
    useState<Field | null>(null);

  useEffect(() => {
    let isMounted = true;

    getHealth()
      .then(() => {
        if (isMounted) {
          setConnectionState("connected");
        }
      })
      .catch(() => {
        if (isMounted) {
          setConnectionState("unavailable");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;

    getFields()
      .then((data) => {
        if (!isMounted) return;

        setFields(data);
        setFieldsState("loaded");
      })
      .catch((err: unknown) => {
        if (!isMounted) return;

        setFieldsError(
          err instanceof Error ? err.message : "Unknown error",
        );
        setFieldsState("error");
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

  const current = statusConfig[connectionState];

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="max-w-3xl w-full space-y-8">
        <div className="text-center space-y-6">
          <h1 className="text-4xl font-bold tracking-tight">
            AgriNexus
          </h1>

          <p className="text-gray-500">
            Connecting agricultural data and infrastructure.
          </p>

          <div className="flex items-center justify-center gap-2 rounded-lg border border-gray-200 px-4 py-3">
            <span
              className={`h-2.5 w-2.5 rounded-full ${current.dot}`}
            />

            <span
              className={`text-sm font-medium ${current.text}`}
            >
              {current.label}
            </span>
          </div>
        </div>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Field Map</h2>

          {fieldsState === "loaded" && (
            <FieldMap
              fields={fields}
              onFieldSelect={setSelectedField}
            />
          )}

          {fieldsState === "loading" && (
            <p className="text-sm text-gray-500">
              Loading map...
            </p>
          )}

          {fieldsState === "error" && (
            <p className="text-sm text-red-600">
              Map unavailable
              {fieldsError ? `: ${fieldsError}` : ""}
            </p>
          )}
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold">
            Selected Field
          </h2>

          {selectedField === null ? (
            <p className="text-sm text-gray-500">
              Select a field on the map to view its details.
            </p>
          ) : (
            <div className="rounded-lg border border-gray-200 p-4 text-sm space-y-1">
              <p>
                <span className="font-medium text-gray-600">
                  Name:
                </span>{" "}
                {selectedField.name}
              </p>

              <p>
                <span className="font-medium text-gray-600">
                  Country ID:
                </span>{" "}
                {selectedField.country_id}
              </p>

              <p>
                <span className="font-medium text-gray-600">
                  Crop Type:
                </span>{" "}
                {selectedField.crop_type ?? "—"}
              </p>

              <p>
                <span className="font-medium text-gray-600">
                  Area (ha):
                </span>{" "}
                {selectedField.area_hectares ?? "—"}
              </p>

              <p>
                <span className="font-medium text-gray-600">
                  Geometry Type:
                </span>{" "}
                {selectedField.geometry?.type ?? "—"}
              </p>
            </div>
          )}
        </section>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Fields</h2>

          {fieldsState === "loading" && (
            <p className="text-sm text-gray-500">
              Loading fields...
            </p>
          )}

          {fieldsState === "error" && (
            <p className="text-sm text-red-600">
              Failed to load fields
              {fieldsError ? `: ${fieldsError}` : ""}
            </p>
          )}

          {fieldsState === "loaded" && fields.length === 0 && (
            <p className="text-sm text-gray-500">
              No fields found.
            </p>
          )}

          {fieldsState === "loaded" && fields.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      Name
                    </th>

                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      Country ID
                    </th>

                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      Crop Type
                    </th>

                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      Area (ha)
                    </th>

                    <th className="px-4 py-2 text-left font-medium text-gray-600">
                      Geometry Type
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-gray-200">
                  {fields.map((field) => (
                    <tr key={field.id}>
                      <td className="px-4 py-2">
                        {field.name}
                      </td>

                      <td className="px-4 py-2">
                        {field.country_id}
                      </td>

                      <td className="px-4 py-2">
                        {field.crop_type ?? "—"}
                      </td>

                      <td className="px-4 py-2">
                        {field.area_hectares ?? "—"}
                      </td>

                      <td className="px-4 py-2">
                        {field.geometry?.type ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}