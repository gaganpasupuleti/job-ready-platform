import Editor, { type Monaco, type OnMount } from '@monaco-editor/react'
import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from 'react'
import type { IDisposable, editor as MonacoEditor } from 'monaco-editor'
import { Keyboard, Sparkles } from 'lucide-react'

import { registerSqlCompletionProvider } from '@/features/sql/editor-intelligence/sqlCompletionProvider'
import { insertSnippetAtCursor } from '@/features/sql/utils/sqlEditorInsert'
import type { SqlTableSchemaPublic } from '@/types/sql'
import { cn } from '@/utils/cn'

const FONT_STORAGE_KEY = 'jrp-sql-editor-font'
const MONACO_MOUNT_TIMEOUT_MS = 12_000

type EditorFontPreset = 'small' | 'medium' | 'large'

const FONT_PRESETS: Record<
  EditorFontPreset,
  { fontSize: number; lineHeight: number; label: string }
> = {
  small: { fontSize: 14, lineHeight: 22, label: 'Small' },
  medium: { fontSize: 16, lineHeight: 26, label: 'Medium' },
  large: { fontSize: 18, lineHeight: 30, label: 'Large' },
}

function readFontPreset(): EditorFontPreset {
  if (typeof window === 'undefined') return 'medium'
  const stored = window.localStorage.getItem(FONT_STORAGE_KEY)
  if (stored === 'small' || stored === 'medium' || stored === 'large') return stored
  return 'medium'
}

export interface SqlEditorHandle {
  insertSnippet: (snippet: string) => void
  replaceSql: (sql: string) => void
  getCursorOffset: () => number
  focus: () => void
}

interface SqlEditorProps {
  value: string
  onChange: (value: string) => void
  height?: string
  readOnly?: boolean
  schemaTables?: SqlTableSchemaPublic[]
  onRun?: () => void
  onSubmit?: () => void
  onFormatSql?: () => void
  onClearOutput?: () => void
  editorStatus?: string | null
  showHeader?: boolean
}

function isEditableShortcutTarget(
  active: Element | null,
  editorArea: HTMLElement | null,
): boolean {
  if (!active || !editorArea) return false
  if (!editorArea.contains(active)) return false
  if (active instanceof HTMLTextAreaElement) return true
  if (
    active instanceof HTMLInputElement ||
    active instanceof HTMLSelectElement ||
    active instanceof HTMLButtonElement
  ) {
    return false
  }
  return (
    active.closest('.monaco-editor') !== null ||
    active.getAttribute('contenteditable') === 'true'
  )
}

export const SqlEditor = forwardRef<SqlEditorHandle, SqlEditorProps>(function SqlEditor(
  {
    value,
    onChange,
    height = '100%',
    readOnly = false,
    schemaTables = [],
    onRun,
    onSubmit,
    onFormatSql,
    onClearOutput,
    editorStatus,
    showHeader = true,
  },
  ref,
) {
  const [useFallback, setUseFallback] = useState(false)
  const [fontPreset, setFontPreset] = useState<EditorFontPreset>(readFontPreset)
  const monacoMountedRef = useRef(false)
  const monacoRef = useRef<Monaco | null>(null)
  const editorRef = useRef<MonacoEditor.IStandaloneCodeEditor | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  const editorAreaRef = useRef<HTMLDivElement | null>(null)
  const sqlCompletionRef = useRef<IDisposable | null>(null)
  const { fontSize, lineHeight } = FONT_PRESETS[fontPreset]

  useEffect(() => {
    window.localStorage.setItem(FONT_STORAGE_KEY, fontPreset)
  }, [fontPreset])

  const getCursorOffset = useCallback((): number => {
    if (useFallback && textareaRef.current) {
      return textareaRef.current.selectionStart ?? value.length
    }
    const editor = editorRef.current
    const model = editor?.getModel()
    const position = editor?.getPosition()
    if (!editor || !model || !position) return value.length
    return model.getOffsetAt(position)
  }, [useFallback, value.length])

  const applySqlUpdate = useCallback(
    (nextSql: string, cursorOffset?: number) => {
      onChange(nextSql)
      const offset = cursorOffset ?? nextSql.length
      if (useFallback) {
        requestAnimationFrame(() => {
          const el = textareaRef.current
          if (!el) return
          el.focus()
          const safeOffset = Math.min(offset, nextSql.length)
          el.setSelectionRange(safeOffset, safeOffset)
        })
        return
      }
      const editor = editorRef.current
      const model = editor?.getModel()
      if (!editor || !model) return
      const position = model.getPositionAt(Math.min(offset, nextSql.length))
      editor.setPosition(position)
      editor.focus()
    },
    [onChange, useFallback],
  )

  useImperativeHandle(
    ref,
    () => ({
      insertSnippet(snippet: string) {
        const { text, cursorOffset } = insertSnippetAtCursor(value, snippet, getCursorOffset())
        applySqlUpdate(text, cursorOffset)
      },
      replaceSql(nextSql: string) {
        applySqlUpdate(nextSql, nextSql.length)
      },
      getCursorOffset,
      focus() {
        if (useFallback) textareaRef.current?.focus()
        else editorRef.current?.focus()
      },
    }),
    [applySqlUpdate, getCursorOffset, useFallback, value],
  )

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isEditableShortcutTarget(document.activeElement, editorAreaRef.current)) return
      if (readOnly) return

      const mod = event.ctrlKey || event.metaKey
      if (!mod) return

      if (event.key === 'Enter' && event.shiftKey) {
        if (!onSubmit) return
        event.preventDefault()
        onSubmit()
        return
      }

      if (event.key === 'Enter' && !event.shiftKey) {
        if (!onRun) return
        event.preventDefault()
        onRun()
        return
      }

      if (event.key.toLowerCase() === 'f' && event.shiftKey) {
        if (!onFormatSql) return
        event.preventDefault()
        onFormatSql()
        return
      }

      if (event.key.toLowerCase() === 'l' && event.shiftKey) {
        if (!onClearOutput) return
        event.preventDefault()
        onClearOutput()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClearOutput, onFormatSql, onRun, onSubmit, readOnly])

  useEffect(() => {
    if (readOnly) return
    monacoMountedRef.current = false
    setMonacoReady(false)
    setUseFallback(false)
    const timer = window.setTimeout(() => {
      if (!monacoMountedRef.current) {
        setUseFallback(true)
      }
    }, MONACO_MOUNT_TIMEOUT_MS)
    return () => window.clearTimeout(timer)
  }, [readOnly])

  const [monacoReady, setMonacoReady] = useState(false)

  const handleMount = useCallback<OnMount>((editor, monaco) => {
    monacoMountedRef.current = true
    monacoRef.current = monaco
    editorRef.current = editor
    setUseFallback(false)
    setMonacoReady(true)
    const w = window as unknown as {
      __jobReadyMonaco?: { setValue: (v: string) => void; getValue: () => string }
    }
    w.__jobReadyMonaco = editor
  }, [])

  useEffect(() => {
    const monaco = monacoRef.current
    if (!monaco || !monacoReady || useFallback || readOnly) return
    sqlCompletionRef.current?.dispose()
    sqlCompletionRef.current = registerSqlCompletionProvider(monaco, schemaTables)
    return () => {
      sqlCompletionRef.current?.dispose()
      sqlCompletionRef.current = null
    }
  }, [monacoReady, readOnly, schemaTables, useFallback])
  useEffect(() => {
    editorRef.current?.updateOptions({ fontSize, lineHeight })
  }, [fontSize, lineHeight])

  return (
    <div ref={editorAreaRef} className="flex h-full min-h-0 flex-col overflow-hidden">
      {showHeader && !readOnly && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface-muted)] px-3 py-1.5">
          <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--color-text-muted)]">
            <span className="font-medium text-[var(--color-text)]">Query Editor</span>
            {useFallback ? (
              <span className="inline-flex items-center gap-1 rounded bg-[var(--color-surface)] px-1.5 py-0.5">
                <Keyboard className="h-3 w-3" />
                Basic editor mode
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded bg-[var(--color-surface)] px-1.5 py-0.5">
                <Sparkles className="h-3 w-3" />
                SQL suggestions · Ctrl + Space
              </span>
            )}
            {editorStatus && <span className="text-[var(--color-text-subtle)]">{editorStatus}</span>}
          </div>
          <div className="flex items-center gap-1">
            {(Object.keys(FONT_PRESETS) as EditorFontPreset[]).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setFontPreset(key)}
                className={cn(
                  'rounded px-2 py-0.5 text-xs font-medium transition-colors',
                  fontPreset === key
                    ? 'bg-[var(--color-accent)] text-white'
                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)]',
                )}
              >
                {FONT_PRESETS[key].label}
              </button>
            ))}
          </div>
        </div>
      )}
      <div className="min-h-0 flex-1 overflow-hidden" style={{ height: showHeader ? undefined : height }}>
        {useFallback && !readOnly ? (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            spellCheck={false}
            className="h-full min-h-[240px] w-full resize-none border-0 bg-[#1e1e1e] p-4 font-mono text-[#d4d4d4] outline-none"
            style={{ fontSize, lineHeight: `${lineHeight}px` }}
            aria-label="SQL query editor fallback"
            placeholder="Write your SQL query here…"
          />
        ) : (
          <Editor
            height={height === '100%' ? '100%' : height}
            language="sql"
            value={value}
            onChange={(next) => onChange(next ?? '')}
            onMount={handleMount}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize,
              lineHeight,
              scrollBeyondLastLine: false,
              readOnly,
              automaticLayout: true,
              quickSuggestions: !readOnly,
              suggestOnTriggerCharacters: !readOnly,
              tabCompletion: readOnly ? 'off' : 'on',
            }}
          />
        )}
      </div>
      {!readOnly && (
        <div className="border-t border-[var(--color-border)] px-3 py-1 text-[10px] text-[var(--color-text-subtle)]">
          Run: Ctrl/Cmd+Enter · Submit: Ctrl/Cmd+Shift+Enter · Format: Ctrl/Cmd+Shift+F · Clear:
          Ctrl/Cmd+Shift+L
        </div>
      )}
    </div>
  )
})
