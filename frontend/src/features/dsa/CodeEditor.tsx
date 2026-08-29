import Editor from '@monaco-editor/react'

interface CodeEditorProps {
  value: string
  language: string
  onChange: (value: string) => void
  height?: string
  readOnly?: boolean
}

export function CodeEditor({
  value,
  language,
  onChange,
  height = '100%',
  readOnly = false,
}: CodeEditorProps) {
  return (
    <Editor
      height={height}
      language={language}
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
