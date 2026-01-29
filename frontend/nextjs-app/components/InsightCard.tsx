/**
 * InsightX AI - Insight Card (Desktop-First Wide Layout)
 *
 * Wide, information-dense display for desktop executives.
 */

import React, { useState } from 'react';
import { ChartData, NumberDetail } from '@/lib/api';

interface InsightCardProps {
    summaryLine: string;
    numbers: NumberDetail[];
    chart?: ChartData;
    sqlQuery: string;
    method?: string;
    computedAt?: string;
    sampleSize?: number;
}

export default function InsightCard({
    summaryLine,
    numbers,
    chart,
    sqlQuery,
    method,
    computedAt,
    sampleSize,
}: InsightCardProps) {
    const [showMethod, setShowMethod] = useState(false);

    return (
        <div className="space-y-4">
            {/* Executive Summary - Clear, confident */}
            <p className="summary-line">{summaryLine}</p>

            {/* Metrics Grid - Wide, 6-column on desktop */}
            {numbers.length > 0 && (
                <div className="metrics-grid">
                    {numbers.slice(0, 6).map((num, index) => (
                        <div key={index} className="metric-item">
                            <p className="metric-label">{num.label}</p>
                            <p className="metric-value">{num.value}</p>
                            {num.calculation?.sample_size && (
                                <p className="metric-secondary">
                                    n={num.calculation.sample_size.toLocaleString()}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Chart - Wide, supporting visual */}
            {chart && chart.data.length > 0 && (
                <WideChart data={chart.data} type={chart.type} title={chart.title} />
            )}

            {/* Methodology - Collapsible */}
            <div className="pt-2">
                <button
                    onClick={() => setShowMethod(!showMethod)}
                    className="collapse-trigger"
                >
                    <svg
                        className={`w-3.5 h-3.5 transition-transform duration-150 ${showMethod ? 'rotate-90' : ''}`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                    How this was calculated
                </button>

                {showMethod && (
                    <div className="mt-3 space-y-3 expand-enter">
                        {method && (
                            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                                {method}
                            </p>
                        )}
                        <pre className="code-block">
                            <code>{sqlQuery}</code>
                        </pre>
                    </div>
                )}
            </div>

            {/* Trust Metadata - Desktop row */}
            <div className="flex items-center gap-4 pt-1">
                {sampleSize && (
                    <span className="metadata">
                        Sample: {sampleSize.toLocaleString()} records
                    </span>
                )}
                {computedAt && (
                    <span className="metadata">
                        Computed: {computedAt}
                    </span>
                )}
                <span className="metadata">Confidence: High</span>
            </div>
        </div>
    );
}

// Wide chart component for desktop
interface WideChartProps {
    data: { x: string | number; y: number }[];
    type: string;
    title?: string;
}

function WideChart({ data, type, title }: WideChartProps) {
    if (data.length === 0) return null;

    const maxValue = Math.max(...data.map((d) => d.y));
    const minValue = Math.min(...data.map((d) => d.y));
    const range = maxValue - minValue || 1;

    const width = 600;
    const height = 80;
    const padding = 12;

    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    if (type === 'bar') {
        const barWidth = Math.min(chartWidth / data.length - 4, 32);
        const gap = (chartWidth - barWidth * data.length) / (data.length + 1);

        return (
            <div className="chart-container">
                {title && <p className="chart-title">{title}</p>}
                <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-16">
                    {data.map((point, index) => {
                        const barHeight = Math.max(((point.y - minValue) / range) * chartHeight, 3);
                        const x = padding + gap + index * (barWidth + gap);
                        const y = height - padding - barHeight;

                        return (
                            <g key={index}>
                                <rect
                                    x={x}
                                    y={y}
                                    width={barWidth}
                                    height={barHeight}
                                    fill="rgba(59, 130, 246, 0.5)"
                                    rx={3}
                                />
                                <title>{`${point.x}: ${typeof point.y === 'number' ? point.y.toLocaleString() : point.y}`}</title>
                            </g>
                        );
                    })}
                </svg>
            </div>
        );
    }

    // Line chart with area fill
    const points = data.map((point, index) => {
        const x = padding + (index / (data.length - 1)) * chartWidth;
        const y = height - padding - ((point.y - minValue) / range) * chartHeight;
        return `${x},${y}`;
    });

    const areaPath = `M ${padding},${height - padding} L ${points.join(' L ')} L ${width - padding},${height - padding} Z`;
    const linePath = `M ${points.join(' L ')}`;

    return (
        <div className="chart-container">
            {title && <p className="chart-title">{title}</p>}
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-16">
                <defs>
                    <linearGradient id="chartGradient" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="0%" stopColor="rgba(59, 130, 246, 0.25)" />
                        <stop offset="100%" stopColor="rgba(59, 130, 246, 0)" />
                    </linearGradient>
                </defs>
                <path d={areaPath} fill="url(#chartGradient)" />
                <path
                    d={linePath}
                    fill="none"
                    stroke="rgba(59, 130, 246, 0.6)"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </svg>
        </div>
    );
}
