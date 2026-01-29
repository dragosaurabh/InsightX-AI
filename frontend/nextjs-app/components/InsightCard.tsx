/**
 * InsightX AI - Insight Card Component
 *
 * Displays analysis results with summary, numbers, charts, and SQL query.
 */

import React, { useState } from 'react';
import { ChartData, NumberDetail } from '@/lib/api';

interface InsightCardProps {
    summaryLine: string;
    numbers: NumberDetail[];
    chart?: ChartData;
    sqlQuery: string;
    method?: string;
}

export default function InsightCard({
    summaryLine,
    numbers,
    chart,
    sqlQuery,
    method,
}: InsightCardProps) {
    const [showQuery, setShowQuery] = useState(false);

    return (
        <div className="glass-card p-4 space-y-4">
            {/* Summary Line */}
            <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                </div>
                <p className="text-lg font-medium text-white leading-relaxed">{summaryLine}</p>
            </div>

            {/* Numbers Grid */}
            {numbers.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {numbers.slice(0, 6).map((num, index) => (
                        <div key={index} className="stat-card">
                            <span className="stat-label">{num.label}</span>
                            <span className="stat-value">{num.value}</span>
                            {num.calculation?.formula && (
                                <span className="text-xs text-slate-500 mt-1">{num.calculation.formula}</span>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Chart */}
            {chart && chart.data.length > 0 && (
                <div className="glass-card p-4">
                    <h4 className="text-sm font-medium text-slate-400 mb-3">{chart.title || 'Chart'}</h4>
                    <SparklineChart data={chart.data} type={chart.type} />
                </div>
            )}

            {/* Method */}
            {method && (
                <p className="text-sm text-slate-400 border-l-2 border-primary-500 pl-3">
                    <span className="font-medium text-slate-300">Method:</span> {method}
                </p>
            )}

            {/* SQL Query Toggle */}
            <div>
                <button
                    onClick={() => setShowQuery(!showQuery)}
                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-primary-400 transition-colors"
                >
                    <svg
                        className={`w-4 h-4 transition-transform ${showQuery ? 'rotate-90' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    {showQuery ? 'Hide SQL Query' : 'View SQL Query'}
                </button>
                {showQuery && (
                    <div className="mt-3 relative">
                        <pre className="code-block text-xs overflow-x-auto">
                            <code>{sqlQuery}</code>
                        </pre>
                        <button
                            onClick={() => navigator.clipboard.writeText(sqlQuery)}
                            className="absolute top-2 right-2 p-1.5 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
                            title="Copy SQL"
                        >
                            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

// Simple Sparkline Chart Component
interface SparklineChartProps {
    data: { x: string | number; y: number }[];
    type: string;
}

function SparklineChart({ data, type }: SparklineChartProps) {
    if (data.length === 0) return null;

    const maxValue = Math.max(...data.map((d) => d.y));
    const minValue = Math.min(...data.map((d) => d.y));
    const range = maxValue - minValue || 1;

    const width = 400;
    const height = 100;
    const padding = 10;

    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    if (type === 'bar') {
        const barWidth = chartWidth / data.length - 4;

        return (
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-24">
                {data.map((point, index) => {
                    const barHeight = ((point.y - minValue) / range) * chartHeight;
                    const x = padding + index * (chartWidth / data.length);
                    const y = height - padding - barHeight;

                    return (
                        <g key={index}>
                            <rect
                                x={x}
                                y={y}
                                width={barWidth}
                                height={barHeight}
                                fill="url(#bar-gradient)"
                                rx={2}
                            />
                            <title>{`${point.x}: ${point.y}`}</title>
                        </g>
                    );
                })}
                <defs>
                    <linearGradient id="bar-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#0ea5e9" />
                        <stop offset="100%" stopColor="#0284c7" />
                    </linearGradient>
                </defs>
            </svg>
        );
    }

    // Line chart
    const points = data.map((point, index) => {
        const x = padding + (index / (data.length - 1)) * chartWidth;
        const y = height - padding - ((point.y - minValue) / range) * chartHeight;
        return `${x},${y}`;
    });

    const linePath = `M ${points.join(' L ')}`;
    const areaPath = `M ${padding},${height - padding} L ${points.join(' L ')} L ${width - padding},${height - padding} Z`;

    return (
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-24">
            <defs>
                <linearGradient id="sparkline-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#0ea5e9" stopOpacity="0" />
                </linearGradient>
            </defs>
            <path d={areaPath} className="sparkline-area" />
            <path d={linePath} className="sparkline-path" />
            {data.map((point, index) => {
                const x = padding + (index / (data.length - 1)) * chartWidth;
                const y = height - padding - ((point.y - minValue) / range) * chartHeight;
                return (
                    <circle
                        key={index}
                        cx={x}
                        cy={y}
                        r={3}
                        fill="#0ea5e9"
                        className="opacity-0 hover:opacity-100 transition-opacity"
                    >
                        <title>{`${point.x}: ${point.y}`}</title>
                    </circle>
                );
            })}
        </svg>
    );
}
