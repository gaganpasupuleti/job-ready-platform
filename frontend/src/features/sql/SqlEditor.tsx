import Editor from '@monaco-editor/react'

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
  return (
    <Editor
      height={height}
      language="sql"
      value={value}
      onChange={(next) => onChange(next ?? '')}
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
