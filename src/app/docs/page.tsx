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
          "TypeScript for type safety",
          "Component-based architecture with reusable UI elements",
          "Optimized data fetching with React Query",
          "Real-time charting with Chart.js"
        ]
      },
      {
        subtitle: "Backend (FastAPI)",
        details: [
          "Asynchronous request handling",
          "WebSocket server for real-time data streaming",
          "RESTful API endpoints for market data",
          "Redis for caching and pub/sub",
          "PostgreSQL for persistent storage",
          "Custom middleware for authentication",
          "Rate limiting and request validation",
          "Background task processing"
        ]
      },
      {
        subtitle: "AI Integration",
        details: [
          "Large Language Model API integration",
          "Market sentiment analysis pipeline",
          "Technical indicator calculation engine",
          "Real-time strategy optimization",
          "Document processing and embedding generation",
          "Vector similarity search",
          "Context-aware response generation",
          "Model fine-tuning capabilities"
        ]
      }
    ]
  },
  {
    title: "Google Cloud GPU Implementation",
    content: [
      {
        subtitle: "GPU Infrastructure",
        details: [
          "NVIDIA T4 GPU with 16GB VRAM",
          "Docker containerization with GPU passthrough",
          "Auto-scaling based on workload",
          "Cost optimization with spot instances",
          "CUDA acceleration for ML tasks",
          "Distributed training capabilities",
          "Model serving optimization",
          "Resource monitoring and management"
        ]
      },
      {
        subtitle: "Performance Optimization",
        details: [
          "~50ms inference speed per prediction",
          "Up to 1000 samples/second batch processing",
          "Optimized memory usage for 16GB VRAM",
          "Efficient model loading and caching",
          "Parallel processing capabilities",
          "Load balancing across GPU instances",
          "Automatic failover and recovery",
          "Resource utilization monitoring"
        ]
      },
      {
        subtitle: "Cost Management",
        details: [
          "~$0.45/hour for T4 instance",
          "Spot instance utilization for non-critical workloads",
          "Automatic scaling based on demand",
          "Resource allocation optimization",
          "Cost monitoring and alerts",
          "Usage analytics and reporting",
          "Budget management tools",
          "Cost-effective deployment strategies"
        ]
      }
    ]
  },
  {
    title: "Frontend Architecture",
    content: [
      {
        subtitle: "Component Structure",
        details: [
          "Modular component design",
          "Reusable UI components",
          "Custom hooks for business logic",
          "Context providers for state management",
          "Error boundary implementation",
          "Loading state handling",
          "Responsive design patterns",
          "Accessibility compliance"
        ]
      },
      {
        subtitle: "Data Management",
        details: [
          "WebSocket integration for real-time updates",
          "Local state management with Context API",
          "Server-side data fetching",
          "Client-side caching strategies",
          "Optimistic UI updates",
          "Error handling and recovery",
          "Data validation and sanitization",
          "Performance monitoring"
        ]
      },
      {
        subtitle: "UI/UX Features",
        details: [
          "Real-time market data visualization",
          "Interactive charts and graphs",
          "Customizable dashboard layouts",
          "Responsive design for all devices",
          "Dark/light mode support",
          "Accessibility features",
          "Loading states and animations",
          "Error handling and user feedback"
        ]
      }
    ]
  },
  {
    title: "Backend Services",
    content: [
      {
        subtitle: "Core Services",
        details: [
          "Market data ingestion and processing",
          "Options chain analysis engine",
          "Technical indicators calculation",
          "AI model inference service",
          "Document processing pipeline",
          "Vector database management",
          "WebSocket message handling",
          "Authentication and authorization"
        ]
      },
      {
        subtitle: "Data Processing",
        details: [
          "Real-time data validation",
          "Historical data analysis",
          "Batch processing capabilities",
          "Stream processing pipelines",
          "Data transformation services",
          "Cache management system",
          "Data consistency checks",
          "Error recovery mechanisms"
        ]
      },
      {
        subtitle: "API Endpoints",
        details: [
          "RESTful API design",
          "WebSocket endpoints",
          "GraphQL support",
          "Rate limiting implementation",
          "Request validation",
          "Response formatting",
          "Error handling",
          "Documentation generation"
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
          "D3.js for data visualization",
          "Chart.js for interactive charts",
          "WebSocket for real-time updates",
          "Jest for testing"
        ]
      },
      {
        subtitle: "Backend Technologies",
        details: [
          "FastAPI for API development",
          "PostgreSQL for data persistence",
          "Redis for caching",
          "Docker for containerization",
          "Nginx for reverse proxy",
          "Celery for task queues",
          "Pytest for testing",
          "Prometheus for monitoring"
        ]
      },
      {
        subtitle: "DevOps & Infrastructure",
        details: [
          "GitHub Actions for CI/CD",
          "Docker Compose for local development",
          "Google Cloud for deployment",
          "Prometheus for monitoring",
          "Grafana for visualization",
          "Kubernetes for orchestration",
          "Terraform for infrastructure",
          "ELK stack for logging"
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
