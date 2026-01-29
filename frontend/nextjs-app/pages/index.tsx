/**
 * InsightX AI - Home Page (Desktop-First Wide Layout)
 *
 * Premium desktop experience with full-width design.
 */

import Head from 'next/head';
import ChatWindow from '@/components/ChatWindow';

export default function Home() {
    return (
        <>
            <Head>
                <title>InsightX AI · Payment Analytics</title>
                <meta
                    name="description"
                    content="Conversational analytics for payment data. Ask questions, get precise answers."
                />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link rel="icon" href="/favicon.svg" type="image/svg+xml" />

                <meta property="og:title" content="InsightX AI · Payment Analytics" />
                <meta property="og:description" content="Ask questions about payment data. Get precise, explainable answers." />
                <meta property="og:type" content="website" />
            </Head>

            <main className="h-screen overflow-hidden">
                {/* Full-width desktop layout with comfortable padding */}
                <div className="h-full w-full max-w-6xl mx-auto px-6 lg:px-12">
                    <ChatWindow />
                </div>
            </main>
        </>
    );
}
