import { useEffect, useState } from 'react'
import Editor from '@monaco-editor/react'
import { Sparkles } from 'lucide-react'

import { cn } from '@/utils/cn'

const FONT_STORAGE_KEY = 'jrp-dsa-editor-font'

type EditorFontPreset = 'small' | 'medium' | 'large'

const FONT_PRESETS: Record<
  EditorFontPreset,
  { fontSize: number; lineHeight: number; label: string }
> = {
  small: { fontSize: 14, lineHeight: 22, label: 'Small' },
  medium: { fontSize: 16, lineHeight: 26, label: 'Medium' },
  large: { fontSize: 18, lineHeight: 30, label: 'Large' },
}

function readFontPreset(fallbackSize?: number): EditorFontPreset {
  if (typeof window === 'undefined') return 'medium'
  const stored = window.localStorage.getItem(FONT_STORAGE_KEY)
  if (stored === 'small' || stored === 'medium' || stored === 'large') return stored
  if (fallbackSize != null) {
    if (fallbackSize <= 14) return 'small'
    if (fallbackSize >= 18) return 'large'
  }
  return 'medium'
}

interface CodeEditorProps {
  value: string
  language: string
  onChange: (value: string) => void
  height?: string
  readOnly?: boolean
  fontSize?: number
  wordWrap?: 'on' | 'off'
  languageLabel?: string
  showHeader?: boolean
  onFontSizeChange?: (size: number) => void
}

export function CodeEditor({
  value,
  language,
  onChange,
  height = '100%',
  readOnly = false,
  fontSize,
  wordWrap = 'on',
  languageLabel,
  showHeader = true,
  onFontSizeChange,
}: CodeEditorProps) {
  const [fontPreset, setFontPreset] = useState<EditorFontPreset>(() =>
    readFontPreset(fontSize),
  )
  const preset = FONT_PRESETS[fontPreset]
  const effectiveFontSize = fontSize ?? preset.fontSize

  useEffect(() => {
    window.localStorage.setItem(FONT_STORAGE_KEY, fontPreset)
    onFontSizeChange?.(FONT_PRESETS[fontPreset].fontSize)
  }, [fontPreset, onFontSizeChange])

  return (
    <div className="dsa-workbench flex h-full min-h-0 flex-col overflow-hidden">
      {showHeader && !readOnly && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--color-border)] bg-[var(--color-surface-muted)] px-3 py-1.5">
          <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
            <span className="font-medium text-[var(--color-text)]">
              {languageLabel ?? language} · editor
            </span>
            <span className="inline-flex items-center gap-1 rounded bg-[var(--color-surface)] px-1.5 py-0.5">
              <Sparkles className="h-3 w-3" />
              Ctrl+Space for suggestions
            </span>
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
      <div className="min-h-0 flex-1 overflow-hidden">
        <Editor
          height={height}
          language={language}
          value={value}
          onChange={(next) => onChange(next ?? '')}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: effectiveFontSize,
            lineHeight: preset.lineHeight,
            wordWrap,
            scrollBeyondLastLine: false,
            readOnly,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  )
}
