/** Parse React Flow viewport inline transform for stability assertions. */
export function parseViewportTransform(style: string | null) {
  if (!style) return null
  const translate = style.match(/translate\(\s*([-\d.]+)px,\s*([-\d.]+)px\s*\)/)
  const scale = style.match(/scale\(([-\d.]+)\)/)
  if (!translate || !scale) return null
  return {
    x: Number.parseFloat(translate[1]),
    y: Number.parseFloat(translate[2]),
    zoom: Number.parseFloat(scale[1]),
  }
}

export function viewportTransformsClose(
  a: string | null,
  b: string | null,
  tolerance = { translatePx: 1.5, zoom: 0.02 },
) {
  const left = parseViewportTransform(a)
  const right = parseViewportTransform(b)
  if (!left || !right) return false
  return (
    Math.abs(left.x - right.x) <= tolerance.translatePx &&
    Math.abs(left.y - right.y) <= tolerance.translatePx &&
    Math.abs(left.zoom - right.zoom) <= tolerance.zoom
  )
}
