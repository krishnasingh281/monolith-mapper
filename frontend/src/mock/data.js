// MonolithMapper Landing Page Mock Data

// ===============================
// AGENTS
// ===============================

export const agents = [
  {
    id: "retriever",
    name: "Retriever Agent",
    icon: "Search",
    description:
      "Intelligently searches your codebase using GraphRAG embeddings to find relevant context across millions of lines of legacy code.",
    metrics: [
      { label: "Accuracy", value: 94, unit: "%" },
      { label: "Speed", value: 200, unit: "ms" }
    ]
  },
  {
    id: "guardrail",
    name: "Guardrail Agent",
    icon: "ShieldCheck",
    description:
      "Validates LLM outputs against Tree-sitter AST rules to prevent hallucinations and ensure syntactically correct code generation.",
    metrics: [
      { label: "Prevention", value: 99.2, unit: "%" },
      { label: "False Positives", value: 0.1, unit: "%" }
    ]
  },
  {
    id: "generator",
    name: "Generator Agent",
    icon: "Sparkles",
    description:
      "Produces modernized code refactors using context-aware prompts powered by your organization’s knowledge graph.",
    metrics: [
      { label: "Quality", value: 96, unit: "%" },
      { label: "Consistency", value: 98, unit: "%" }
    ]
  },
  {
    id: "evaluator",
    name: "Evaluator Agent",
    icon: "Gauge",
    description:
      "Continuously monitors output quality using Langfuse observability to detect knowledge rot and optimize RAG pipelines.",
    metrics: [
      { label: "Coverage", value: 100, unit: "%" },
      { label: "Latency", value: 50, unit: "ms" }
    ]
  }
];

// ===============================
// TECH STACK
// ===============================

export const techStack = [
  { id: "chromadb", name: "ChromaDB", icon: "Database" },
  { id: "treesitter", name: "Tree-sitter", icon: "GitBranch" },
  { id: "fastapi", name: "FastAPI", icon: "Zap" },
  { id: "nextjs", name: "Next.js", icon: "Layout" },
  { id: "langfuse", name: "Langfuse", icon: "Activity" },
  { id: "graphrag", name: "GraphRAG", icon: "Network" }
];

// ===============================
// OBSERVABILITY METRICS
// ===============================

export const observabilityMetrics = {
  totalRequests: 1247,
  avgLatency: 342,
  successRate: 99.4,
  tokensProcessed: 2400000,

  traces: [
    {
      id: "trace_1",
      operation: "Code Modernization",
      duration: 1200,
      status: "success",

      steps: [
        { name: "Retrieval", time: 220, tokens: 1240 },
        { name: "Guardrail Check", time: 45, tokens: 0 },
        { name: "Generation", time: 830, tokens: 3420 },
        { name: "Evaluation", time: 105, tokens: 240 }
      ]
    }
  ]
};

// ===============================
// FEATURES
// ===============================

export const features = [
  {
    id: "knowledge-graph",
    title: "GraphRAG Knowledge Graph",
    description:
      "Transform your monolithic codebase into a living, queryable knowledge graph with semantic search capabilities."
  },
  {
    id: "ast-parsing",
    title: "Tree-sitter AST Parsing",
    description:
      "Parse and understand code structure across 40+ languages with millisecond-level precision."
  },
  {
    id: "agent-workflows",
    title: "Agentic Workflows",
    description:
      "Four specialized AI agents collaborate to retrieve, validate, generate, and evaluate every code transformation."
  },
  {
    id: "observability",
    title: "Zero Knowledge Rot",
    description:
      "Continuous observability with Langfuse ensures your RAG pipeline stays aligned with your evolving codebase."
  }
];

// ===============================
// HERO STATS
// ===============================

export const stats = [
  {
    id: "loc",
    label: "Lines of Code Analyzed",
    value: 2000000,
    display: "2M+"
  },
  {
    id: "quality",
    label: "Code Quality Score",
    value: 96,
    display: "96%"
  },
  {
    id: "success",
    label: "Refactor Success Rate",
    value: 99.4,
    display: "99.4%"
  },
  {
    id: "speed",
    label: "Average Processing Time",
    value: 400,
    display: "< 400ms"
  }
];