export type Phase = 'ready' | 'running' | 'finished'
export interface TypingState {
  target: string
  input: string
  phase: Phase
  startedAt: number | null
  endedAt: number | null
  durationMs: number
  attempts: number
  correctAttempts: number
  errors: Record<string, number>
}
export type TypingAction =
  | { type: 'insert'; text: string; now: number }
  | { type: 'backspace'; now: number }
  | { type: 'tick'; now: number }

export function createSession(target: string, seconds = 0): TypingState {
  return {
    target,
    input: '',
    phase: 'ready',
    startedAt: null,
    endedAt: null,
    durationMs: seconds * 1000,
    attempts: 0,
    correctAttempts: 0,
    errors: {},
  }
}

// Pure, synchronous transitions: the final keystroke belongs to the final snapshot.
export function advance(state: TypingState, action: TypingAction): TypingState {
  if (state.phase === 'finished' || !state.target) return state
  if (
    state.startedAt !== null &&
    state.durationMs > 0 &&
    action.now >= state.startedAt + state.durationMs
  ) {
    return { ...state, phase: 'finished', endedAt: state.startedAt + state.durationMs }
  }
  if (action.type === 'tick') return state
  if (action.type === 'backspace') return { ...state, input: state.input.slice(0, -1) }
  if (!action.text) return state
  const text = action.text.slice(0, state.target.length - state.input.length)
  const errors = { ...state.errors }
  let correct = 0
  for (let i = 0; i < text.length; i++) {
    const expected = state.target[state.input.length + i]
    if (text[i] === expected) correct++
    else errors[expected] = (errors[expected] ?? 0) + 1
  }
  const input = state.input + text
  const finished = input.length === state.target.length
  return {
    ...state,
    input,
    startedAt: state.startedAt ?? action.now,
    phase: finished ? 'finished' : 'running',
    endedAt: finished ? action.now : null,
    attempts: state.attempts + text.length,
    correctAttempts: state.correctAttempts + correct,
    errors,
  }
}

export function metrics(state: TypingState, now: number) {
  const elapsedMs =
    state.startedAt === null ? 0 : Math.max(0, (state.endedAt ?? now) - state.startedAt)
  const correct = [...state.input].filter((char, i) => char === state.target[i]).length
  const minutes = elapsedMs / 60000
  return {
    elapsedMs,
    wpm: minutes > 0 ? Math.round(correct / 5 / minutes) : 0,
    rawWpm: minutes > 0 ? Math.round(state.attempts / 5 / minutes) : 0,
    accuracy: state.attempts ? Math.round((state.correctAttempts / state.attempts) * 100) : 100,
    errors: state.attempts - state.correctAttempts,
    progress: state.target.length
      ? Math.round((state.input.length / state.target.length) * 100)
      : 0,
  }
}

export function indentAt(target: string, index: number) {
  const lineStart = target.lastIndexOf('\n', index - 1) + 1
  if (target.slice(lineStart, index).trim()) return ''
  if (target[index] === '\t') return '\t'
  return target.slice(index).match(/^ {1,4}/)?.[0] ?? ''
}
