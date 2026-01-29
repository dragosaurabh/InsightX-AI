/**
 * InsightX AI - Chat Window Component
 *
 * Main chat interface with message list, input, and send functionality.
 */

import React, { useState, useRef, useEffect } from 'react';
import Message, { MessageData } from './Message';
import { sendChatMessage, isClarificationResponse, getSessionId, resetSession } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';

const SAMPLE_QUERIES = [
    "What is the overall failure rate in the last 30 days?",
    "Compare failure rate on Android vs iOS",
    "Show average transaction amount by category",
    "What are the top failure codes?",
    "Provide an executive summary for transactions",
];

export default function ChatWindow() {
    const [messages, setMessages] = useState<MessageData[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Auto-resize textarea
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

        // Add user message
        const userMessage: MessageData = {
            id: uuidv4(),
            role: 'user',
            content: text,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        // Add loading message
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

            // Replace loading message with response
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
            const errorMessage = err instanceof Error ? err.message : 'An error occurred';
            setError(errorMessage);

            // Replace loading with error message
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === loadingMessage.id
                        ? {
                            ...msg,
                            isLoading: false,
                            content: `Sorry, I encountered an error: ${errorMessage}. Please try again.`,
                        }
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

    const handleFollowUpClick = (question: string) => {
        handleSend(question);
    };

    const handleNewChat = () => {
        resetSession();
        setMessages([]);
        setError(null);
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <header className="flex-shrink-0 px-4 py-3 border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center glow-primary">
                            <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                        </div>
                        <div>
                            <h1 className="text-lg font-semibold text-white">InsightX AI</h1>
                            <p className="text-xs text-slate-400">Conversational Analytics for Payments</p>
                        </div>
                    </div>
                    <button
                        onClick={handleNewChat}
                        className="btn-secondary text-sm flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        New Chat
                    </button>
                </div>
            </header>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {/* Welcome Message */}
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center px-4">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mb-6 glow-primary">
                            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Welcome to InsightX AI</h2>
                        <p className="text-slate-400 mb-6 max-w-md">
                            Ask questions about your payment data in plain English. Get precise, explainable answers backed by deterministic analysis.
                        </p>

                        {/* Sample Queries */}
                        <div className="w-full max-w-lg">
                            <p className="text-sm text-slate-500 mb-3">Try asking:</p>
                            <div className="flex flex-wrap gap-2 justify-center">
                                {SAMPLE_QUERIES.map((query, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleSend(query)}
                                        className="chip text-xs"
                                    >
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
                        onFollowUpClick={handleFollowUpClick}
                    />
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Error Banner */}
            {error && (
                <div className="flex-shrink-0 px-4">
                    <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {error}
                        <button onClick={() => setError(null)} className="ml-auto hover:text-red-300">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Input Area */}
            <div className="flex-shrink-0 p-4 border-t border-slate-700 bg-slate-900/50 backdrop-blur-sm">
                <div className="flex gap-3 items-end">
                    <div className="flex-1 relative">
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Ask about your payment data..."
                            className="input-field resize-none min-h-[48px] max-h-[120px] pr-12"
                            rows={1}
                            disabled={isLoading}
                        />
                        <button
                            onClick={() => handleSend()}
                            disabled={!input.trim() || isLoading}
                            className="absolute right-2 bottom-2 p-2 rounded-lg bg-primary-500 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary-600 transition-colors"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                </div>
                <p className="text-xs text-slate-500 mt-2 text-center">
                    Press Enter to send, Shift+Enter for new line
                </p>
            </div>
        </div>
    );
}
