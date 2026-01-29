/**
 * InsightX AI - Chat Window (Premium Glass Surfaces)
 *
 * Desktop-first with visible glass panels.
 */

import React, { useState, useRef, useEffect } from 'react';
import Message, { MessageData } from './Message';
import { sendChatMessage, isClarificationResponse, resetSession } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

const SAMPLE_QUERIES = [
    "What is the overall failure rate in the last 30 days?",
    "Compare failure rates between Android and iOS",
    "Show me the top failure codes by volume",
    "Average transaction amount by payment category",
    "Provide an executive summary of transactions",
];

export default function ChatWindow() {
    const [messages, setMessages] = useState<MessageData[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.style.height = 'auto';
            inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
        }
    }, [input]);

    const handleSend = async (messageText?: string) => {
        const text = messageText || input.trim();
        if (!text || isLoading) return;

        setInput('');
        setError(null);

        const userMessage: MessageData = {
            id: uuidv4(),
            role: 'user',
            content: text,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        const loadingMessage: MessageData = {
            id: uuidv4(),
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            isLoading: true,
        };
        setMessages((prev) => [...prev, loadingMessage]);
        setIsLoading(true);

        try {
            const response = await sendChatMessage(text);

            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === loadingMessage.id
                        ? {
                            ...msg,
                            isLoading: false,
                            content: isClarificationResponse(response)
                                ? response.clarification_question
                                : response.answer_text,
                            response: response,
                        }
                        : msg
                )
            );
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Request failed';
            setError(errorMessage);

            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === loadingMessage.id
                        ? { ...msg, isLoading: false, content: `Error: ${errorMessage}` }
                        : msg
                )
            );
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleNewChat = () => {
        resetSession();
        setMessages([]);
        setError(null);
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <header className="flex-shrink-0 py-5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        {/* Logo with glow */}
                        <div
                            className="w-10 h-10 rounded-xl flex items-center justify-center"
                            style={{
                                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.15))',
                                boxShadow: '0 0 20px -5px rgba(59, 130, 246, 0.3)',
                                border: '1px solid rgba(255, 255, 255, 0.1)'
                            }}
                        >
                            <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                                InsightX AI
                            </h1>
                            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                Conversational Analytics for Payments
                            </p>
                        </div>
                    </div>
                    <button onClick={handleNewChat} className="btn-ghost">
                        New Chat
                    </button>
                </div>
            </header>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto py-4 space-y-6">
                {/* Welcome State - Inside a visible glass panel */}
                {messages.length === 0 && (
                    <div className="flex items-center justify-center h-full">
                        <div
                            className="glass-panel p-8 max-w-2xl w-full text-center"
                        >
                            {/* Icon with glow */}
                            <div
                                className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.1))',
                                    boxShadow: '0 0 40px -10px rgba(59, 130, 246, 0.4)',
                                    border: '1px solid rgba(255, 255, 255, 0.1)'
                                }}
                            >
                                <svg className="w-8 h-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
                                </svg>
                            </div>

                            <h2 className="text-2xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                                Payment Analytics Assistant
                            </h2>
                            <p className="text-sm mb-8 max-w-md mx-auto" style={{ color: 'var(--text-secondary)' }}>
                                Ask questions about your transaction data in natural language.
                                Get precise, explainable answers backed by real-time analysis.
                            </p>

                            {/* Sample queries in a grid */}
                            <div className="grid gap-3">
                                {SAMPLE_QUERIES.map((query, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleSend(query)}
                                        className="chip text-left justify-start w-full"
                                    >
                                        <svg className="w-4 h-4 mr-2 flex-shrink-0" style={{ color: 'var(--accent)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                                        </svg>
                                        {query}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Message List */}
                {messages.map((message) => (
                    <Message
                        key={message.id}
                        message={message}
                        onFollowUpClick={(q) => handleSend(q)}
                    />
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Error Banner */}
            {error && (
                <div className="flex-shrink-0 mb-4">
                    <div
                        className="glass-card px-4 py-3 flex items-center gap-3"
                        style={{ borderColor: 'rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.1)' }}
                    >
                        <span style={{ color: '#ef4444' }}>{error}</span>
                        <button
                            onClick={() => setError(null)}
                            className="ml-auto opacity-60 hover:opacity-100 transition-opacity"
                            style={{ color: '#ef4444' }}
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Input Area - Visible glass container */}
            <div className="flex-shrink-0 pb-5">
                <div className="glass-input-container p-4">
                    <div className="flex gap-3 items-end">
                        <div className="flex-1 relative">
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Ask about your payment data..."
                                className="input-glass resize-none min-h-[52px] max-h-[120px] pr-14"
                                rows={1}
                                disabled={isLoading}
                            />
                            <button
                                onClick={() => handleSend()}
                                disabled={!input.trim() || isLoading}
                                className="absolute right-2 bottom-2 p-3 rounded-xl transition-all duration-200 disabled:opacity-30"
                                style={{
                                    background: input.trim() ? 'var(--accent)' : 'rgba(255, 255, 255, 0.05)',
                                    color: 'white',
                                    boxShadow: input.trim() ? '0 4px 12px -2px rgba(59, 130, 246, 0.3)' : 'none'
                                }}
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                                </svg>
                            </button>
                        </div>
                    </div>
                    <div className="flex items-center justify-between mt-3 px-1">
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            Press Enter to send · Shift+Enter for new line
                        </p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            Powered by Gemini
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
