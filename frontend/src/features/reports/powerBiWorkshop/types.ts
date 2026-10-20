export type WorkshopVerificationStatus = 'verified' | 'pending_desktop' | 'missing_screenshot'

export type WorkshopImage = {
  src: string
  caption: string
  alt: string
  role: 'config' | 'result'
}

export type WorkshopDaxBlock = {
  table: string
  name: string
  expression: string
}

export type WorkshopStep = {
  id: string
  stageId: string
  order: number
  title: string
  objective: string
  prerequisites: string[]
  actions: string[]
  dax: WorkshopDaxBlock[] | null
  powerQuery: Array<{ name: string; parameter?: string; expression: string }> | null
  visual: { visualType: string; fields: string[] } | null
  expectedResult: string
  verificationChecklist: string[]
  commonMistakes: string[]
  images: WorkshopImage[]
  referenceNotes: string
  verificationStatus: WorkshopVerificationStatus
}

export type WorkshopStage = {
  id: string
  order: number
  title: string
  summary: string
}

export type WorkshopContent = {
  contentVersion: string
  reportId: string
  title: string
  learningOutcomes: string[]
  prerequisites: string[]
  testedDesktopVersion: string
  canonicalPbixSha256?: string | null
  excludedMeasures: Array<{ name: string; reason: string }>
  intentionalDifferences: Array<{ topic: string; detail: string }>
  stages: WorkshopStage[]
  steps: WorkshopStep[]
  expectedResults: Record<string, unknown>
  downloads: Array<{ label: string; path: string }>
}
