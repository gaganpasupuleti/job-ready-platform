import { useEffect, useRef, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Code2,
  Keyboard,
  RotateCcw,
  Type,
  SlidersHorizontal,
  Moon,
  Sun,
  Check,
  History,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { PracticeTrackNav } from '@/components/practice/PracticeTrackNav'
import { useAuth } from '@/hooks/useAuth'
import { advance, createSession, indentAt, metrics } from './engine'
import {
  difficulties,
  languages,
  practiceContent,
  type Difficulty,
  type Language,
  type Mode,
} from './content'
import { clearHistory, readHistory, saveResult, type TypingResult } from './history'
import './typing.css'

const keyRows = [
  ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
  ['Tab', 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
  ['Caps', 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", 'Enter'],
  ['Shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 'Shift'],
]
const shifted = '~!@#$%^&*()_+{}|:"<>?'
const unshifted = "`1234567890-=[]\\;',./"
const visibleKey = (char: string) =>
  char === ' ' ? 'Space' : char === '\n' ? 'Enter' : char === '\t' ? 'Tab' : char

export function TypingPracticePage() {
  const { user } = useAuth()
  return user ? <TypingStudio key={user.id} userId={user.id} /> : null
}

function TypingStudio({ userId }: { userId: string }) {
  const [mode, setMode] = useState<Mode>('text')
  const [language, setLanguage] = useState<Language>('Python')
  const [difficulty, setDifficulty] = useState<Difficulty>('Foundation')
  const [seconds, setSeconds] = useState(60)
  const [round, setRound] = useState(0)
  const [customDraft, setCustomDraft] = useState('')
  const [custom, setCustom] = useState('')
  const [dark, setDark] = useState(false)
  const [keyboard, setKeyboard] = useState(true)
  const [history, setHistory] = useState(() => readHistory(userId))
  const [notice, setNotice] = useState('')
  const [focused, setFocused] = useState(false)
  const [session, setSession] = useState(() =>
    createSession(practiceContent('text', 'Python', 'Foundation', 0, true), 60),
  )
  const [now, setNow] = useState(0)
  const [runId, setRunId] = useState(() => crypto.randomUUID())
  const savedId = useRef('')
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const caretRef = useRef<HTMLSpanElement>(null)
  const stats = metrics(session, now)
  const running = session.phase === 'running'
  const finished = session.phase === 'finished'
  const next = session.target[session.input.length] ?? ''
  const expectedKey = visibleKey(
    shifted.includes(next) && next ? unshifted[shifted.indexOf(next)] : next.toLowerCase(),
  )
  const shiftNeeded = /[A-Z]/.test(next) || (next !== '' && shifted.includes(next))
  const remaining = Math.max(0, Math.ceil((session.durationMs - stats.elapsedMs) / 1000))

  // Update by deadline, not interval counts: background throttling cannot extend a run.
  useEffect(() => {
    if (!running) return
    const tick = () => {
      const time = performance.now()
      setNow(time)
      setSession((previous) => advance(previous, { type: 'tick', now: time }))
    }
    const id = window.setInterval(tick, 100)
    document.addEventListener('visibilitychange', tick)
    return () => {
      clearInterval(id)
      document.removeEventListener('visibilitychange', tick)
    }
  }, [running])

  useEffect(() => {
    if (!finished || savedId.current === runId) return
    savedId.current = runId
    const result: TypingResult = {
      id: runId,
      date: new Date().toISOString(),
      mode,
      label:
        mode === 'code'
          ? `${language} · ${difficulty}`
          : mode === 'custom'
            ? 'Custom passage'
            : difficulty,
      seconds,
      wpm: stats.wpm,
      accuracy: stats.accuracy,
      errors: stats.errors,
      elapsedMs: stats.elapsedMs,
    }
    const saved = saveResult(userId, result)
    setHistory((previous) => [result, ...previous.filter((r) => r.id !== runId)].slice(0, 50))
    // Completion synchronizes the external browser store and its status message.
    if (!saved) {
      // eslint-disable-next-line react/set-state-in-effect
      setNotice('Browser storage is unavailable. This result will last until you leave this page.')
    }
  }, [
    finished,
    runId,
    userId,
    mode,
    language,
    difficulty,
    seconds,
    stats.wpm,
    stats.accuracy,
    stats.errors,
    stats.elapsedMs,
  ])

  useEffect(() => {
    const caret = caretRef.current
    const area = caret?.parentElement
    if (caret && area) {
      const y = caret.offsetTop - area.offsetTop
      if (y < area.scrollTop || y > area.scrollTop + area.clientHeight - 60)
        area.scrollTop = Math.max(0, y - 70)
    }
  }, [session.input.length])

  function reset(
    options: {
      mode?: Mode
      language?: Language
      difficulty?: Difficulty
      seconds?: number
      nextRound?: number
      custom?: string
    } = {},
  ) {
    const m = options.mode ?? mode
    const l = options.language ?? language
    const d = options.difficulty ?? difficulty
    const s = options.seconds ?? seconds
    const r = options.nextRound ?? round
    const text = m === 'custom' ? (options.custom ?? custom) : practiceContent(m, l, d, r, s > 0)
    setMode(m)
    setLanguage(l)
    setDifficulty(d)
    setSeconds(s)
    setRound(r)
    setSession(createSession(text, s))
    setNow(0)
    setRunId(crypto.randomUUID())
    setNotice('')
  }
  function insert(text: string) {
    const time = performance.now()
    setNow(time)
    setSession((previous) => advance(previous, { type: 'insert', text, now: time }))
  }
  function switchMode(m: Mode) {
    reset({ mode: m, seconds: m === 'text' ? 60 : 0 })
  }
  function startCustom() {
    const text = customDraft.replace(/\r\n?/g, '\n').trim()
    if (!text || text.length > 2000 || /[^\x20-\x7e\n\t]/.test(text)) {
      setNotice('Use 1–2,000 English letters, numbers, punctuation, spaces, tabs, or line breaks.')
      return
    }
    setCustom(text)
    reset({ custom: text })
    requestAnimationFrame(() => inputRef.current?.focus())
  }
  const similar = history.filter(
    (r) =>
      r.mode === mode &&
      r.seconds === seconds &&
      r.label === (mode === 'code' ? `${language} · ${difficulty}` : difficulty),
  )
  const best = similar.length ? Math.max(...similar.map((r) => r.wpm)) : null
  return (
    <div className={`typing-studio${dark ? ' typing-dark' : ''}`}>
      <PracticeTrackNav />
      <header className="typing-heading">
        <div>
          <p className="typing-eyebrow">PRACTICE / KEYBOARD FLUENCY</p>
          <h1>
            Find your typing rhythm<span>.</span>
          </h1>
          <p>Build accuracy first. Let speed follow.</p>
        </div>
        <Link to="/practice" className="typing-back">
          <ArrowLeft size={14} /> Practice hub
        </Link>
      </header>
      <div className="typing-toolbar">
        <div className="typing-segment" aria-label="Practice mode">
          {(
            [
              { mode: 'text', label: 'Text', icon: Type },
              { mode: 'code', label: 'Code', icon: Code2 },
              { mode: 'custom', label: 'Custom', icon: SlidersHorizontal },
            ] as const
          ).map((item) => (
            <button
              key={item.mode}
              aria-pressed={mode === item.mode}
              onClick={() => switchMode(item.mode)}
              disabled={running}
            >
              <item.icon size={15} />
              {item.label}
            </button>
          ))}
        </div>
        <div className="typing-settings">
          {mode === 'code' && (
            <label>
              Language
              <select
                aria-label="Code language"
                value={language}
                disabled={running}
                onChange={(e) => reset({ language: e.target.value as Language })}
              >
                {languages.map((l) => (
                  <option key={l}>{l}</option>
                ))}
              </select>
            </label>
          )}
          {mode !== 'custom' && (
            <label>
              Level
              <select
                aria-label="Difficulty"
                value={difficulty}
                disabled={running}
                onChange={(e) => reset({ difficulty: e.target.value as Difficulty })}
              >
                {difficulties.map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </label>
          )}
          <label>
            Session
            <select
              aria-label="Session duration"
              value={seconds}
              disabled={running}
              onChange={(e) => reset({ seconds: Number(e.target.value) })}
            >
              <option value={0}>Full passage</option>
              {[30, 60, 120].map((s) => (
                <option key={s} value={s}>
                  {s} seconds
                </option>
              ))}
            </select>
          </label>
        </div>
        <button
          className="typing-icon"
          aria-label={dark ? 'Use light practice theme' : 'Use dark practice theme'}
          onClick={() => setDark(!dark)}
        >
          {dark ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </div>
      {mode === 'custom' && !running && !finished && (
        <section className="typing-custom">
          <label htmlFor="custom-passage">
            Your practice passage <span>English text or code · up to 2,000 characters</span>
          </label>
          <textarea
            id="custom-passage"
            value={customDraft}
            maxLength={2000}
            placeholder="Paste a passage or code snippet here…"
            onChange={(e) => setCustomDraft(e.target.value)}
          />
          <button className="typing-primary" onClick={startCustom}>
            Use this passage <ArrowRight size={14} />
          </button>
        </section>
      )}
      {notice && (
        <p role="status" className="typing-notice">
          {notice}
        </p>
      )}
      <section className="typing-card" aria-label="Typing session">
        <div className="typing-card-top">
          <span>
            <span className={`typing-dot${running ? ' is-live' : ''}`} />
            {finished ? 'SESSION COMPLETE' : running ? 'SESSION IN PROGRESS' : 'READY WHEN YOU ARE'}
          </span>
          <span>
            {mode === 'code' ? language : mode === 'custom' ? 'Your passage' : 'English'}{' '}
            <span className="typing-divider">/</span>{' '}
            {seconds ? `${seconds}s test` : 'Full passage'}
          </span>
        </div>
        <div className="typing-metrics">
          <div className="typing-main-metric">
            <strong data-testid="typing-wpm">{stats.wpm}</strong>
            <span>words / min</span>
          </div>
          <div>
            <strong data-testid="typing-accuracy">
              {session.attempts ? `${stats.accuracy}%` : '—'}
            </strong>
            <span>accuracy</span>
          </div>
          <div>
            <strong data-testid="typing-errors">{stats.errors}</strong>
            <span>errors</span>
          </div>
          <div>
            <strong data-testid="typing-time">
              {seconds ? `${remaining}s` : `${Math.floor(stats.elapsedMs / 1000)}s`}
            </strong>
            <span>{seconds ? 'remaining' : 'elapsed'}</span>
          </div>
          <div className="typing-best">
            <strong>{mode === 'custom' ? '—' : (best ?? '—')}</strong>
            <span>personal best</span>
          </div>
        </div>
        {finished ? (
          <div className="typing-result" role="status">
            <span className="typing-result-icon">
              <Check size={23} />
            </span>
            <h2>One session stronger.</h2>
            <p>
              {stats.accuracy >= 95
                ? 'Accurate work. Keep this rhythm in your next session.'
                : 'Slow down slightly and focus on the keys below.'}
            </p>
            <div className="typing-result-details">
              <span>{Math.round(stats.elapsedMs / 1000)} seconds</span>
              <span>{stats.rawWpm} raw WPM</span>
              <span>{stats.progress}% of passage</span>
            </div>
            <div className="typing-result-actions">
              <button
                className="typing-primary"
                onClick={() => {
                  reset()
                  requestAnimationFrame(() => inputRef.current?.focus())
                }}
              >
                <RotateCcw size={15} />
                Try again
              </button>
              {mode === 'text' && (
                <button onClick={() => reset({ nextRound: round + 1 })}>
                  Next passage <ArrowRight size={15} />
                </button>
              )}
            </div>
          </div>
        ) : (
          <>
            <div className={`typing-input-area${focused ? ' is-focused' : ''}`}>
              <div
                className={`typing-passage${mode === 'code' ? ' is-code' : ''}`}
                data-testid="typing-passage"
                aria-hidden="true"
                onClick={() => inputRef.current?.focus()}
              >
                {[...session.target].map((char, index) => (
                  <span
                    key={index}
                    ref={index === session.input.length ? caretRef : undefined}
                    className={
                      index < session.input.length
                        ? session.input[index] === char
                          ? 'is-correct'
                          : 'is-error'
                        : index === session.input.length
                          ? 'is-caret'
                          : ''
                    }
                  >
                    {char === '\n' ? <>↵{'\n'}</> : char === '\t' ? '⇥   ' : char}
                  </span>
                ))}
                {!session.target && <span>Choose a passage above to begin.</span>}
              </div>
              <textarea
                ref={inputRef}
                className="typing-capture"
                aria-label="Typing input"
                aria-describedby="typing-help typing-target"
                value={session.input}
                disabled={!session.target}
                autoCapitalize="off"
                autoCorrect="off"
                spellCheck={false}
                autoComplete="off"
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                onPaste={(e) => {
                  e.preventDefault()
                  setNotice(
                    'Type each character to measure your practice. Paste custom text in the passage box above.',
                  )
                }}
                onDrop={(e) => e.preventDefault()}
                onSelect={(e) => {
                  const el = e.currentTarget
                  if (el.selectionStart !== el.value.length || el.selectionEnd !== el.value.length)
                    el.setSelectionRange(el.value.length, el.value.length)
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    e.currentTarget.blur()
                    return
                  }
                  if (e.key === 'Tab' && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
                    const indentation = indentAt(session.target, session.input.length)
                    if (indentation) {
                      e.preventDefault()
                      insert(indentation)
                    }
                  }
                }}
                onChange={(e) => {
                  const value = e.target.value
                  const previous = session.input
                  if (value === previous.slice(0, -1)) {
                    const time = performance.now()
                    setNow(time)
                    setSession((s) => advance(s, { type: 'backspace', now: time }))
                  } else if (
                    value.startsWith(previous) &&
                    value.length === previous.length + 1 &&
                    /^[\x20-\x7e\n\t]$/.test(value.slice(-1))
                  )
                    insert(value.slice(-1))
                }}
              />
            </div>
            <span id="typing-target" className="typing-sr">
              Passage to type: {session.target}
            </span>
            <div className="typing-input-footer">
              <p id="typing-help">
                {focused
                  ? 'Backspace to correct · Enter for a new line · Tab for indentation · Esc to leave'
                  : 'Click the passage or tab here to start typing'}
              </p>
              <button aria-label="Restart typing session" onClick={() => reset()}>
                <RotateCcw size={15} /> Restart
              </button>
            </div>
          </>
        )}
        <div
          className="typing-progress"
          role="progressbar"
          aria-label="Passage progress"
          aria-valuenow={stats.progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span style={{ width: `${stats.progress}%` }} />
        </div>
      </section>
      <div className="typing-lower">
        <section className="typing-keyboard-panel">
          <div className="typing-section-title">
            <h2>
              <Keyboard size={17} /> Keyboard guide
            </h2>
            <button aria-pressed={keyboard} onClick={() => setKeyboard(!keyboard)}>
              {keyboard ? 'Hide' : 'Show'}
            </button>
          </div>
          {keyboard && (
            <div
              className="typing-keyboard"
              aria-label={`Next key: ${visibleKey(next) || 'none'}${shiftNeeded ? ' with Shift' : ''}`}
            >
              {keyRows.map((row, i) => (
                <div className="typing-key-row" key={i}>
                  {row.map((key, j) => (
                    <kbd
                      key={`${key}-${j}`}
                      className={`${key.length > 1 ? 'key-wide' : ''} ${!finished && (key === expectedKey || (key === 'Shift' && shiftNeeded)) ? 'key-next' : ''}`}
                    >
                      {key}
                    </kbd>
                  ))}
                </div>
              ))}
              <div className="typing-key-row">
                <kbd className={`key-space${!finished && next === ' ' ? ' key-next' : ''}`}>
                  space
                </kbd>
              </div>
            </div>
          )}
          <p className="typing-small">
            {finished
              ? 'Rest your hands, then try another round.'
              : 'Follow the highlighted key. Keep your hands relaxed.'}
          </p>
        </section>
        <aside className="typing-coach">
          <p className="typing-eyebrow">FOCUS ON ACCURACY</p>
          <h2>{stats.errors ? 'Your next small win.' : 'Make each keystroke count.'}</h2>
          <p>
            {stats.errors
              ? 'These characters caused errors in this session. Backspacing fixes the text; your accuracy still includes the original attempt.'
              : 'Keep your eyes on the text. Start at a comfortable pace and build a steady rhythm before chasing speed.'}
          </p>
          <div className="typing-weak-keys">
            {Object.entries(session.errors)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 5)
              .map(([key, count]) => (
                <span key={key}>
                  <kbd>{visibleKey(key)}</kbd> × {count}
                </span>
              ))}
          </div>
          <p className="typing-small">
            Code mode measures typing fluency. It does not run or grade code.
          </p>
        </aside>
      </div>
      <section className="typing-history">
        <div className="typing-section-title">
          <h2>
            <History size={17} /> Recent sessions <span>{history.length}</span>
          </h2>
          {history.length > 0 && (
            <button
              onClick={() => {
                if (clearHistory(userId)) setHistory([])
                else setNotice('Could not clear browser history. Please try again.')
              }}
            >
              Clear history
            </button>
          )}
        </div>
        {history.length === 0 ? (
          <p className="typing-empty">
            Your first finished session will appear here. Start with a comfortable pace.
          </p>
        ) : (
          <div className="typing-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Practice</th>
                  <th>Session</th>
                  <th>WPM</th>
                  <th>Accuracy</th>
                  <th>Errors</th>
                  <th>Completed</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 8).map((result) => (
                  <tr key={result.id}>
                    <td>
                      <strong>
                        {result.mode === 'code'
                          ? 'Code'
                          : result.mode === 'custom'
                            ? 'Custom'
                            : 'Text'}
                      </strong>
                      <span>{result.label}</span>
                    </td>
                    <td>{result.seconds ? `${result.seconds}s` : 'Passage'}</td>
                    <td>{result.wpm}</td>
                    <td>{result.accuracy}%</td>
                    <td>{result.errors}</td>
                    <td>
                      {new Date(result.date).toLocaleString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="typing-small">
          Last 50 results saved for your account in this browser. No cross-device sync. WPM =
          correct characters ÷ 5 ÷ elapsed minutes.
        </p>
      </section>
    </div>
  )
}
