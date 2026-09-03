import Editor, { type OnMount } from '@monaco-editor/react'
import { useCallback } from 'react'

interface SqlEditorProps {
  value: string
  onChange: (value: string) => void
  height?: string
  readOnly?: boolean
}

export function SqlEditor({
  value,
  onChange,
  height = '100%',
  readOnly = false,
}: SqlEditorProps) {
  const handleMount = useCallback<OnMount>((editor) => {
    // Expose for reliable E2E fills (Playwright cannot drive React state via textarea alone).
    const w = window as unknown as { __jobReadyMonaco?: { setValue: (v: string) => void; getValue: () => string } }
    w.__jobReadyMonaco = editor
  }, [])

  return (
    <Editor
      height={height}
      language="sql"
      value={value}
      onChange={(next) => onChange(next ?? '')}
      onMount={handleMount}
      theme="vs-dark"
      options={{
        minimap: { enabled: false },
        fontSize: 14,
        scrollBeyondLastLine: false,
        readOnly,
        automaticLayout: true,
      }}
    />
  )
}
