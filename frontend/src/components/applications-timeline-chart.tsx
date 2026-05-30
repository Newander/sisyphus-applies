"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { TimelinePoint } from "@/lib/api";

export function ApplicationsTimelineChart({ data }: { data: TimelinePoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          interval={4}
          tickFormatter={(value: string) => value.slice(5)}
        />
        <YAxis allowDecimals={false} tick={{ fontSize: 12 }} width={32} />
        <Tooltip
          labelFormatter={(label: string) => label}
          formatter={(value: number, name: string) => [
            value,
            name === "applications" ? "Applications" : "Updates",
          ]}
        />
        <Legend
          formatter={(value: string) => (value === "applications" ? "Applications" : "Updates")}
        />
        <Line
          type="monotone"
          dataKey="applications"
          stroke="#2563eb"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="updates"
          stroke="#16a34a"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
