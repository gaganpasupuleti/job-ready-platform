import { Link } from 'react-router-dom'

import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

const TRACKS: Record<
  string,
  { title: string; description: string; categorySlug?: string; topicSlugs?: string[] }
> = {
  genai: {
    title: 'Generative AI',
    description: 'LLM fundamentals, transformers, embeddings, and vector databases.',
    categorySlug: 'generative-ai',
    topicSlugs: ['llm-fundamentals', 'transformers', 'embeddings'],
  },
  rag: {
    title: 'RAG',
    description: 'Ingestion, chunking, retrieval, grounding, citations, and production RAG.',
    categorySlug: 'generative-ai',
    topicSlugs: ['rag', 'retrieval', 'vector-databases'],
  },
  'prompt-engineering': {
    title: 'Prompt Engineering',
    description: 'Instruction design, few-shot, structured outputs, and injection awareness.',
    categorySlug: 'prompt-engineering',
  },
  agents: {
    title: 'AI Agents',
    description: 'Loops, tools, memory, guardrails, and orchestration — no live agent runtime.',
    categorySlug: 'ai-agents',
    topicSlugs: ['agent-fundamentals', 'agent-loops', 'multi-agent-systems', 'tool-calling'],
  },
  mcp: {
    title: 'MCP',
    description: 'Host, client, server, tools, resources, prompts, and permissions.',
    categorySlug: 'ai-agents',
    topicSlugs: ['mcp-fundamentals'],
  },
  'tool-calling': {
    title: 'Tool Calling',
    description: 'When to call tools, required params, sequencing, and confirmation.',
    categorySlug: 'generative-ai',
    topicSlugs: ['tool-calling'],
  },
  evaluation: {
    title: 'LLM Evaluation',
    description: 'Golden sets, groundedness, retrieval metrics, and production eval.',
    categorySlug: 'generative-ai',
    topicSlugs: ['llm-evaluation'],
  },
  security: {
    title: 'AI Security',
    description: 'Prompt injection, leakage, excessive agency, and RAG trust boundaries.',
    categorySlug: 'generative-ai',
    topicSlugs: ['ai-security'],
  },
  'system-design': {
    title: 'AI System Design',
    description: 'RAG assistants, support bots, and tool-using workflows.',
    categorySlug: 'generative-ai',
    topicSlugs: ['ai-system-design'],
  },
}

export function AiTrackPage({ track }: { track: keyof typeof TRACKS }) {
  const config = TRACKS[track]
  return (
    <div className="space-y-4">
      {track === 'prompt-engineering' && (
        <p className="text-sm text-[var(--color-text-muted)]">
          Interactive challenges:{' '}
          <Link className="text-[var(--color-accent)] hover:underline" to="/ai/prompt-engineering/challenges">
            /ai/prompt-engineering/challenges
          </Link>
        </p>
      )}
      <PracticeCatalog
        title={config.title}
        description={config.description}
        domainSlug="ai"
        categorySlug={config.categorySlug}
        topicSlugs={config.topicSlugs}
      />
    </div>
  )
}
