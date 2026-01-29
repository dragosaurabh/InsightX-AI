/**
 * InsightX AI - Message Component (Premium Glass Surfaces)
 *
 * AI responses in elevated glass panels with strong visual presence.
 */

import React from 'react';
import InsightCard from './InsightCard';
import { ChatResponse, ClarificationResponse } from '@/lib/api';

export interface MessageData {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    response?: ChatResponse | ClarificationResponse;
    isLoading?: boolean;
}

interface MessageProps {
    message: MessageData;
    onFollowUpClick?: (question: string) => void;
}

export default function Message({ message, onFollowUpClick }: MessageProps) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex gap-4 ${isUser ? 'justify-end' : ''} message-enter`}>
            {/* AI Avatar */}
            {!isUser && (
                <div
                    className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-sm font-medium"
                    style={{
                        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1))',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        boxShadow: '0 0 15px -5px rgba(59, 130, 246, 0.25)',
                        color: 'rgba(255, 255, 255, 0.7)'
                    }}
                >
                    AI
                </div>
            )}

            {/* Content */}
            <div className={`${isUser ? 'max-w-xl' : 'flex-1 max-w-4xl'}`}>
                {/* User Message - Styled bubble */}
                {isUser && (
                    <div
                        className="inline-block px-5 py-3 rounded-2xl text-sm"
                        style={{
                            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.1))',
                            border: '1px solid rgba(59, 130, 246, 0.25)',
                            color: 'var(--text-primary)',
                            boxShadow: '0 4px 12px -4px rgba(59, 130, 246, 0.2)'
                        }}
                    >
                        {message.content}
                    </div>
                )}

                {/* Assistant Message - ELEVATED GLASS PANEL (strongest visual element) */}
                {!isUser && (
                    <div className="glass-panel-elevated p-6 space-y-5">
                        {/* Loading */}
                        {message.isLoading && (
                            <div className="flex items-center gap-3">
                                <span className="typing-dot"></span>
                                <span className="typing-dot"></span>
                                <span className="typing-dot"></span>
                                <span className="text-sm ml-2" style={{ color: 'var(--text-muted)' }}>
                                    Analyzing your data...
                                </span>
                            </div>
                        )}

                        {/* Text Response */}
                        {!message.isLoading && !message.response && (
                            <div className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                                {message.content}
                            </div>
                        )}

                        {/* Clarification */}
                        {message.response && 'needs_clarification' in message.response && (
                            <div className="text-sm leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                                {message.response.clarification_question}
                            </div>
                        )}

                        {/* Full Analysis Response */}
                        {message.response && 'answer_text' in message.response && (
                            <>
                                <InsightCard
                                    summaryLine={message.response.summary_line}
                                    numbers={message.response.numbers}
                                    chart={message.response.chart}
                                    sqlQuery={message.response.query}
                                    method={message.response.method}
                                    computedAt={new Date().toLocaleTimeString([], {
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })}
                                    sampleSize={50000}
                                />

                                {/* Follow-up Suggestions */}
                                {message.response.suggested_followups?.length > 0 && (
                                    <div
                                        className="pt-4 mt-4"
                                        style={{ borderTop: '1px solid var(--glass-border)' }}
                                    >
                                        <p className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>
                                            Related questions
                                        </p>
                                        <div className="flex flex-wrap gap-2">
                                            {message.response.suggested_followups.map((question, index) => (
                                                <button
                                                    key={index}
                                                    onClick={() => onFollowUpClick?.(question)}
                                                    className="chip"
                                                >
                                                    {question}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

                {/* Timestamp */}
                <p
                    className={`text-xs mt-2 ${isUser ? 'text-right' : ''}`}
                    style={{ color: 'var(--text-muted)' }}
                >
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
            </div>

            {/* User Avatar */}
            {isUser && (
                <div
                    className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-sm font-medium"
                    style={{
                        background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(99, 102, 241, 0.15))',
                        border: '1px solid rgba(59, 130, 246, 0.2)',
                        color: '#60a5fa'
                    }}
                >
                    U
                </div>
            )}
        </div>
    );
}
