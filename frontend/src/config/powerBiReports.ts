/** Catalog of Power BI reports shown in the Reports section. */
export type PowerBiReport = {
  id: string
  title: string
  description: string
  category: string
  /** Local .pbix name (for admin reference). */
  sourceFile?: string
  /** iframe src from Power BI Service (Publish to web or secure embed). */
  embedUrl: string
  /** Optional PNG/JPG preview (simpler than PDF). */
  previewImageUrl: string
  /** Static PDF for in-app preview (public/ or full URL). */
  previewPdfUrl: string
  /** Other PDF names Power BI may use when exporting to public/reports/. */
  previewPdfAlternates?: string[]
  /** PDF download; defaults to preview file when empty. */
  downloadPdfUrl: string
  /** Public folder with manifest.json, CSVs, DAX/M JSON (build lab). */
  labPath?: string
}

const executiveSalesUrl = (import.meta.env.VITE_POWERBI_EXECUTIVE_SALES_EMBED_URL ?? '').trim()
const executivePreview =
  (import.meta.env.VITE_POWERBI_EXECUTIVE_SALES_PREVIEW_URL ?? '/reports/executive-sales-toast.pdf').trim()
const executiveDownload = (import.meta.env.VITE_POWERBI_EXECUTIVE_SALES_DOWNLOAD_URL ?? '').trim()
const executiveImage = (
  import.meta.env.VITE_POWERBI_EXECUTIVE_SALES_PREVIEW_IMAGE_URL ?? '/reports/executive-sales-toast.png'
).trim()

export const powerBiReports: PowerBiReport[] = [
  {
    id: 'executive-sales-toast',
    title: 'Executive Sales Report — Toast Notification',
    description: 'Executive sales KPIs with toast-style alerts for at-a-glance performance.',
    category: 'Sales',
    sourceFile: 'Exceutive Sales Report - Toast Notifictaion.pbix',
    embedUrl: executiveSalesUrl,
    previewImageUrl: executiveImage,
    previewPdfUrl: executivePreview,
    previewPdfAlternates: ['/reports/Exceutive Sales Report - Toast Notifictaion.pdf'],
    downloadPdfUrl: executiveDownload,
    labPath: '/reports/executive-sales-toast-lab',
  },
]

export function getPowerBiReport(id: string): PowerBiReport | undefined {
  return powerBiReports.find((report) => report.id === id)
}
