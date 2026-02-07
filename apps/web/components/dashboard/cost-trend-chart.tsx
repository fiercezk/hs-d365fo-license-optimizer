"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';
import type { CSSProperties } from 'react';

export interface CostTrendDataPoint {
  date: string; // ISO 8601 date string
  actualCost: number;
  forecastCost?: number;
  targetCost?: number;
}

interface CostTrendChartProps {
  data: CostTrendDataPoint[];
  title?: string;
  currency?: string;
}

/**
 * Cost Trend Chart Component
 *
 * Displays license cost over time using Recharts LineChart.
 * Shows three series:
 *   - Actual Cost (blue line): Real monthly license spend
 *   - Forecast Cost (dotted gray): What cost would be without optimizations
 *   - Target Cost (green line): Cost reduction goal
 *
 * Usage:
 *   <CostTrendChart data={trendData} currency="USD" />
 *
 * Data source: Algorithm 5.1 (License Trend Analyzer)
 */
export function CostTrendChart({
  data,
  title = "License Cost Trend (Last 12 Months)",
  currency = "USD"
}: CostTrendChartProps) {

  // Format currency for tooltip and Y-axis
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format date for X-axis labels
  const formatDate = (dateString: string): string => {
    try {
      const date = parseISO(dateString);
      return format(date, 'MMM yyyy'); // "Jan 2026"
    } catch {
      return dateString;
    }
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="rounded-lg border bg-white p-3 shadow-lg">
        <p className="mb-2 font-semibold text-gray-900">
          {formatDate(label)}
        </p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-600">{entry.name}:</span>
            <span className="font-medium text-gray-900">
              {formatCurrency(entry.value)}
            </span>
          </div>
        ))}
        {payload.length > 1 && payload[0].value < payload[1]?.value && (
          <div className="mt-2 border-t pt-2 text-sm">
            <span className="text-green-600 font-medium">
              Savings: {formatCurrency(payload[1].value - payload[0].value)}
            </span>
          </div>
        )}
      </div>
    );
  };

  // Handle empty data state
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="mt-4 flex h-64 items-center justify-center rounded-lg bg-gray-50 text-gray-400">
          <p className="text-sm">No cost trend data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <div className="mt-4">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={data}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              tickFormatter={formatCurrency}
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="line"
              iconSize={18}
            />

            {/* Actual Cost Line */}
            <Line
              type="monotone"
              dataKey="actualCost"
              name="Actual Cost"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
            />

            {/* Forecast Cost Line (dotted) */}
            {data.some(d => d.forecastCost !== undefined) && (
              <Line
                type="monotone"
                dataKey="forecastCost"
                name="Forecast (No Optimization)"
                stroke="#9ca3af"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: '#9ca3af', r: 3 }}
              />
            )}

            {/* Target Cost Line */}
            {data.some(d => d.targetCost !== undefined) && (
              <Line
                type="monotone"
                dataKey="targetCost"
                name="Target Cost"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: '#10b981', r: 3 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats below chart */}
      <div className="mt-6 grid grid-cols-1 gap-4 border-t pt-4 sm:grid-cols-3">
        <div>
          <p className="text-xs text-gray-500">Current Month</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatCurrency(data[data.length - 1].actualCost)}
          </p>
        </div>
        {data[data.length - 1].forecastCost && (
          <div>
            <p className="text-xs text-gray-500">Savings vs. Forecast</p>
            <p className="text-lg font-semibold text-green-600">
              {formatCurrency(
                data[data.length - 1].forecastCost - data[data.length - 1].actualCost
              )}
            </p>
          </div>
        )}
        <div>
          <p className="text-xs text-gray-500">12-Month Average</p>
          <p className="text-lg font-semibold text-gray-900">
            {formatCurrency(
              data.reduce((sum, d) => sum + d.actualCost, 0) / data.length
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
