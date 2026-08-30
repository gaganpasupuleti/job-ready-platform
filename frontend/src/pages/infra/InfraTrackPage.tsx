import { PracticeCatalog } from '@/features/practice/PracticeCatalog'

const TRACKS: Record<
  string,
  { title: string; description: string; domain: string; categorySlug?: string; topicSlugs?: string[] }
> = {
  'cloud-fundamentals': {
    title: 'Cloud Fundamentals',
    description: 'Virtualization, HA, shared responsibility, and service models.',
    domain: 'cloud',
    categorySlug: 'cloud-fundamentals',
  },
  'cloud-aws': {
    title: 'AWS',
    description: 'Job-oriented AWS services. Unofficial preparation — not an exam dump.',
    domain: 'cloud',
    categorySlug: 'aws',
  },
  'cloud-azure': {
    title: 'Azure',
    description: 'Entra ID, VNets, storage, and Azure app services. Unofficial preparation.',
    domain: 'cloud',
    categorySlug: 'azure',
  },
  'cloud-gcp': {
    title: 'GCP',
    description: 'IAM, Compute Engine, Cloud Storage, and GKE concepts. Unofficial preparation.',
    domain: 'cloud',
    categorySlug: 'gcp',
  },
  'cloud-architecture': {
    title: 'Cloud Architecture',
    description: 'HA, uploads, events, DR, and scaling tradeoffs.',
    domain: 'cloud',
    categorySlug: 'cloud-architecture',
  },
  'cloud-security': {
    title: 'Cloud Security',
    description: 'Identity, network controls, data protection, and logging.',
    domain: 'cloud',
    categorySlug: 'cloud-security',
  },
  'devops-linux': {
    title: 'Linux',
    description: 'Filesystem, permissions, processes, and logs. No dangerous automation.',
    domain: 'devops',
    categorySlug: 'linux',
  },
  'devops-git': {
    title: 'Git',
    description: 'Branching, merge, rebase concepts, and pull requests.',
    domain: 'devops',
    categorySlug: 'git',
  },
  'devops-docker': {
    title: 'Docker',
    description: 'Images, Compose, health checks, and container security.',
    domain: 'devops',
    categorySlug: 'docker',
  },
  'devops-kubernetes': {
    title: 'Kubernetes',
    description: 'Pods, Deployments, Services, and troubleshooting — no live cluster.',
    domain: 'devops',
    categorySlug: 'kubernetes',
  },
  'devops-cicd': {
    title: 'CI/CD',
    description: 'Pipeline stages, artifacts, secrets, and rollback.',
    domain: 'devops',
    categorySlug: 'cicd',
  },
  'devops-terraform': {
    title: 'Terraform',
    description: 'IaC, state, modules, and plan/apply — no live providers.',
    domain: 'devops',
    categorySlug: 'terraform',
  },
  'devops-observability': {
    title: 'Observability',
    description: 'Metrics, logs, traces, SLOs, and OpenTelemetry concepts.',
    domain: 'devops',
    categorySlug: 'observability',
  },
  'devops-sre': {
    title: 'SRE',
    description: 'Error budgets, incidents, toil, and resilience.',
    domain: 'devops',
    categorySlug: 'sre',
  },
  'cyber-fundamentals': {
    title: 'Security Fundamentals',
    description: 'CIA triad, least privilege, zero trust, and controls.',
    domain: 'cybersecurity',
    categorySlug: 'security-fundamentals',
  },
  'cyber-network': {
    title: 'Network Security',
    description: 'TLS, firewalls, segmentation, WAF, and IDS/IPS concepts.',
    domain: 'cybersecurity',
    categorySlug: 'network-security',
  },
  'cyber-iam': {
    title: 'IAM',
    description: 'RBAC, MFA, SSO, federation, and secrets — defensive only.',
    domain: 'cybersecurity',
    categorySlug: 'iam',
  },
  'cyber-web': {
    title: 'Web Security',
    description: 'Identification, impact, and prevention. No exploit payloads.',
    domain: 'cybersecurity',
    categorySlug: 'web-security',
  },
  'cyber-owasp': {
    title: 'OWASP',
    description: 'Common web risks mapped to OWASP categories. Unofficial study aid.',
    domain: 'cybersecurity',
    categorySlug: 'web-security',
    topicSlugs: ['owasp', 'xss-concepts', 'injection-concepts', 'sql-injection'],
  },
  'cyber-api': {
    title: 'API Security',
    description: 'Auth, object-level authorization, rate limits, and gateways.',
    domain: 'cybersecurity',
    categorySlug: 'api-security',
  },
  'cyber-cloud': {
    title: 'Cloud Security',
    description: 'Identity, public storage, and key management.',
    domain: 'cybersecurity',
    categorySlug: 'cyber-cloud-security',
  },
  'cyber-soc': {
    title: 'SOC',
    description: 'Roles, alerts, triage, and playbooks.',
    domain: 'cybersecurity',
    categorySlug: 'soc-siem',
    topicSlugs: ['soc-roles', 'events-alerts', 'triage', 'escalation', 'playbooks'],
  },
  'cyber-siem': {
    title: 'SIEM',
    description: 'Correlation, detection rules, and false positives.',
    domain: 'cybersecurity',
    categorySlug: 'soc-siem',
    topicSlugs: ['siem', 'detection-rules', 'false-positives'],
  },
  'cyber-ir': {
    title: 'Incident Response',
    description: 'Prepare, identify, contain, eradicate, recover. Safe tabletop only.',
    domain: 'cybersecurity',
    categorySlug: 'incident-response',
  },
  'cyber-coding': {
    title: 'Secure Coding',
    description: 'Validation, encoding, parameterized queries, and secrets.',
    domain: 'cybersecurity',
    categorySlug: 'secure-coding',
  },
}

export function InfraTrackPage({ track }: { track: keyof typeof TRACKS }) {
  const config = TRACKS[track]
  return (
    <PracticeCatalog
      title={config.title}
      description={config.description}
      domainSlug={config.domain}
      categorySlug={config.categorySlug}
      topicSlugs={config.topicSlugs}
    />
  )
}
