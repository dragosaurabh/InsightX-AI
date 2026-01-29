/**
 * InsightX AI - Message Component
 *
 * Renders individual chat messages (user and assistant).
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
        <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''} message-enter`}>
            {/* Avatar */}
            <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isUser
                        ? 'bg-gradient-to-br from-accent-500 to-accent-600'
                        : 'bg-gradient-to-br from-primary-500 to-primary-600'
                    }`}
            >
                {isUser ? (
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                ) : (
                    <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                )}
            </div>

            {/* Message Content */}
            <div className={`flex-1 max-w-[85%] ${isUser ? 'text-right' : ''}`}>
                {/* User Message */}
                {isUser && (
                    <div className="inline-block bg-gradient-to-r from-accent-600 to-accent-700 text-white px-4 py-2.5 rounded-2xl rounded-tr-sm">
                        <p className="text-sm leading-relaxed">{message.content}</p>
                    </div>
                )}

                {/* Assistant Message */}
                {!isUser && (
                    <div className="space-y-3">
                        {/* Loading State */}
                        {message.isLoading && (
                            <div className="inline-flex items-center gap-1.5 bg-slate-800 px-4 py-2.5 rounded-2xl rounded-tl-sm">
                                <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full"></span>
                                <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full"></span>
                                <span className="typing-dot w-2 h-2 bg-primary-400 rounded-full"></span>
                            </div>
                        )}

                        {/* Regular Text Response */}
                        {!message.isLoading && !message.response && (
                            <div className="inline-block bg-slate-800 text-slate-200 px-4 py-2.5 rounded-2xl rounded-tl-sm">
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                            </div>
                        )}

                        {/* Clarification Response */}
                        {message.response && 'needs_clarification' in message.response && (
                            <div className="inline-block bg-slate-800 text-slate-200 px-4 py-2.5 rounded-2xl rounded-tl-sm">
                                <p className="text-sm leading-relaxed">{message.response.clarification_question}</p>
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
                                />

                                {/* Follow-up Suggestions */}
                                {message.response.suggested_followups?.length > 0 && (
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {message.response.suggested_followups.map((question, index) => (
                                            <button
                                                key={index}
                                                onClick={() => onFollowUpClick?.(question)}
                                                className="chip hover:chip-active"
                                            >
                                                {question}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

                {/* Timestamp */}
                <p className={`text-xs text-slate-500 mt-1 ${isUser ? 'text-right' : ''}`}>
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
            </div>
        </div>
    );
}
