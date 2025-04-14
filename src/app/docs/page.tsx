import Link from 'next/link';

const ARCHITECTURE_SECTIONS = [
  {
    title: "System Architecture",
    content: [
      {
        subtitle: "Frontend (Next.js 14)",
        details: [
          "Server-side rendering with React Server Components",
          "Real-time WebSocket integration for market data",
          "TailwindCSS for responsive design",
          "Custom hooks for state management",
          "TypeScript for type safety"
        ]
      },
      {
        subtitle: "Backend (FastAPI)",
        details: [
          "Asynchronous request handling",
          "WebSocket server for real-time data streaming",
          "RESTful API endpoints for market data",
          "Redis for caching and pub/sub",
          "PostgreSQL for persistent storage"
        ]
      },
      {
        subtitle: "AI Integration",
        details: [
          "Large Language Model API integration",
          "Market sentiment analysis pipeline",
          "Technical indicator calculation engine",
          "Real-time strategy optimization"
        ]
      }
    ]
  },
  {
    title: "Data Flow",
    content: [
      {
        subtitle: "Market Data Pipeline",
        details: [
          "Real-time market data ingestion",
          "Options chain processing",
          "Greeks calculation engine",
          "Technical indicator computation",
          "WebSocket broadcasting"
        ]
      },
      {
        subtitle: "Analysis Pipeline",
        details: [
          "Historical data processing",
          "Volatility surface modeling",
          "Options strategy analysis",
          "Risk metrics calculation",
          "Position management system"
        ]
      }
    ]
  },
  {
    title: "Development Stack",
    content: [
      {
        subtitle: "Frontend Technologies",
        details: [
          "Next.js 14 with App Router",
          "TailwindCSS for styling",
          "TypeScript for type safety",
          "React Query for data fetching",
          "D3.js for data visualization"
        ]
      },
      {
        subtitle: "Backend Technologies",
        details: [
          "FastAPI for API development",
          "PostgreSQL for data persistence",
          "Redis for caching",
          "Docker for containerization",
          "Nginx for reverse proxy"
        ]
      },
      {
        subtitle: "DevOps & Infrastructure",
        details: [
          "GitHub Actions for CI/CD",
          "Docker Compose for local development",
          "AWS for cloud deployment",
          "Prometheus for monitoring",
          "Grafana for visualization"
        ]
      }
    ]
  }
];

export default function Documentation() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-900 to-black text-white">
      <div className="max-w-6xl mx-auto px-4 py-16">
        <div className="flex justify-between items-center mb-12">
          <h1 className="text-4xl font-bold text-green-400">robinAI Documentation</h1>
          <Link
            href="/"
            className="flex items-center gap-2 text-green-400 hover:text-green-300 transition-colors"
          >
            <span>Back to Home</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
        </div>

        <div className="space-y-16">
          {ARCHITECTURE_SECTIONS.map((section, index) => (
            <section key={index} className="glass-card p-8 rounded-xl">
              <h2 className="text-2xl font-bold text-green-400 mb-8">{section.title}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {section.content.map((subsection, subIndex) => (
                  <div key={subIndex} className="space-y-4">
                    <h3 className="text-xl font-semibold text-green-300">{subsection.subtitle}</h3>
                    <ul className="space-y-2">
                      {subsection.details.map((detail, detailIndex) => (
                        <li key={detailIndex} className="flex items-start gap-2 text-gray-300">
                          <svg className="w-5 h-5 mt-1 flex-shrink-0 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <span>{detail}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
} 
