/**
 * InsightX AI - Home Page
 *
 * Main page with the chat interface.
 */

import Head from 'next/head';
import ChatWindow from '@/components/ChatWindow';

export default function Home() {
    return (
        <>
            <Head>
                <title>InsightX AI - Conversational Analytics for Payments</title>
                <meta
                    name="description"
                    content="Ask plain English questions about your payment data. Get precise, explainable answers backed by deterministic analysis."
                />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link rel="icon" href="/favicon.ico" />

                {/* Open Graph */}
                <meta property="og:title" content="InsightX AI - Conversational Analytics for Payments" />
                <meta property="og:description" content="Ask plain English questions about your payment data. Get precise, explainable answers." />
                <meta property="og:type" content="website" />

                {/* Twitter */}
                <meta name="twitter:card" content="summary_large_image" />
                <meta name="twitter:title" content="InsightX AI" />
                <meta name="twitter:description" content="Conversational analytics for digital payments" />
            </Head>

            <main className="h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
                {/* Background Pattern */}
                <div className="fixed inset-0 overflow-hidden pointer-events-none">
                    <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
                    <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
                    <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-20" />
                </div>

                {/* Content */}
                <div className="relative h-full max-w-5xl mx-auto">
                    <ChatWindow />
                </div>
            </main>
        </>
    );
}
