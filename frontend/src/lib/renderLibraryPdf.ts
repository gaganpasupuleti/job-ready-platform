import type { PDFDocumentProxy } from 'pdfjs-dist'

let pdfjsReady: Promise<typeof import('pdfjs-dist/legacy/build/pdf.mjs')> | null = null

async function loadPdfJs() {
  if (!pdfjsReady) {
    pdfjsReady = (async () => {
      const mod = await import('pdfjs-dist/legacy/build/pdf.mjs')
      const worker = await import('pdfjs-dist/legacy/build/pdf.worker.min.mjs?url')
      mod.GlobalWorkerOptions.workerSrc = worker.default
      return mod
    })()
  }
  return pdfjsReady
}

const openDocuments = new WeakMap<ArrayBuffer, Promise<PDFDocumentProxy>>()

export async function openLibraryPdf(data: ArrayBuffer) {
  const pdf = await loadPdfJs()
  let pending = openDocuments.get(data)
  if (!pending) {
    pending = pdf
      .getDocument({
        data: new Uint8Array(data),
        standardFontDataUrl: `${import.meta.env.BASE_URL}standard_fonts/`,
      })
      .promise
    openDocuments.set(data, pending)
  }
  const doc = await pending
  return {
    numPages: doc.numPages,
    async renderPage(pageNumber: number, canvas: HTMLCanvasElement, scale = 1.2) {
      const ctx = canvas.getContext('2d')
      if (!ctx) throw new Error('This PDF file could not be opened.')
      const index = Math.min(Math.max(1, pageNumber), doc.numPages)
      const page = await doc.getPage(index)
      const viewport = page.getViewport({ scale })
      canvas.width = viewport.width
      canvas.height = viewport.height
      await page.render({ canvas, canvasContext: ctx, viewport }).promise
    },
  }
}
