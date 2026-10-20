/** Shipped when API is down or not deployed yet (matches backend/app/data/roadmaps). */
export const STATIC_ROADMAP_CATALOG = {
  roadmaps: [
    {
      family_slug: 'data-engineer',
      title: 'Data Engineer',
      config_version: '2-linked-draft',
      description: 'Linked draft curriculum: SQL, Python, pipelines, and platform practice.',
      preview_only: true,
      student_eligible: false,
    },
  ],
} satisfies {
  roadmaps: {
    family_slug: string
    title: string
    config_version: string
    description: string
    preview_only: boolean
    student_eligible: boolean
  }[]
}

export function catalogItemForFamily(slug: string) {
  return STATIC_ROADMAP_CATALOG.roadmaps.find((row) => row.family_slug === slug)
}
