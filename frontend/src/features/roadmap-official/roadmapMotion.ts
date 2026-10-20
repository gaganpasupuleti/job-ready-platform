export function flowDuration(reducedMotion: boolean, ms: number): number {
  return reducedMotion ? 0 : ms
}
