import { marked, type Token, type Tokens } from 'marked'
import { Fragment, type ReactNode } from 'react'

const SAFE_URL = /^(https?:\/\/|mailto:)/i

function stripControls(value: string): string {
  let out = ''
  for (const char of value) {
    const code = char.charCodeAt(0)
    if (code <= 31 || code === 127) continue
    out += char
  }
  return out
}

/** marked escapes text for HTML. React text nodes must receive the decoded characters. */
function textOf(value: string): string {
  return value
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
}

/** Drop raw HTML tokens and refuse javascript:, data:, and protocol-relative links. */
function safeHref(href: string | null | undefined): string | null {
  if (!href) return null
  const compact = stripControls(href).replace(/\s+/g, '')
  if (!compact || compact.startsWith('//')) return null
  let decoded = compact
  try {
    decoded = decodeURIComponent(compact)
  } catch {
    return null
  }
  const scheme = stripControls(decoded).replace(/\s+/g, '').toLowerCase()
  if (/^(javascript|data|vbscript|file|blob):/.test(scheme)) return null
  if (compact.startsWith('/') || compact.startsWith('#')) return compact
  return SAFE_URL.test(compact) ? compact : null
}

function inline(tokens: Token[] | undefined, key: string): ReactNode {
  if (!tokens?.length) return null
  return tokens.map((token, index) => renderToken(token, `${key}.${index}`))
}

function renderToken(token: Token, key: string): ReactNode {
  switch (token.type) {
    case 'space':
    case 'def':
    case 'html':
      return null
    case 'heading': {
      const heading = token as Tokens.Heading
      const depth = Math.min(Math.max(heading.depth, 1), 4)
      const Tag = `h${depth}` as 'h1' | 'h2' | 'h3' | 'h4'
      return (
        <Tag key={key} className="learn-md-heading">
          {inline(heading.tokens, key)}
        </Tag>
      )
    }
    case 'paragraph':
      return <p key={key}>{inline((token as Tokens.Paragraph).tokens, key)}</p>
    case 'blockquote':
      return <blockquote key={key}>{inline((token as Tokens.Blockquote).tokens, key)}</blockquote>
    case 'list': {
      const list = token as Tokens.List
      const Tag = list.ordered ? 'ol' : 'ul'
      return (
        <Tag key={key} start={list.ordered && list.start !== '' ? list.start : undefined}>
          {list.items.map((item, index) => (
            <li key={`${key}.${index}`}>{inline(item.tokens, `${key}.${index}`)}</li>
          ))}
        </Tag>
      )
    }
    case 'code': {
      const code = token as Tokens.Code
      return (
        <div key={key} className="learn-md-scroll">
          <pre>
            <code>{textOf(code.text).replace(/\n$/, '')}</code>
          </pre>
        </div>
      )
    }
    case 'table': {
      const table = token as Tokens.Table
      return (
        <div key={key} className="learn-md-scroll">
          <table>
            <thead>
              <tr>
                {table.header.map((cell, index) => (
                  <th key={`${key}.h.${index}`} style={cell.align ? { textAlign: cell.align } : undefined}>
                    {inline(cell.tokens, `${key}.h.${index}`)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, rowIndex) => (
                <tr key={`${key}.r.${rowIndex}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={`${key}.r.${rowIndex}.${cellIndex}`} style={cell.align ? { textAlign: cell.align } : undefined}>
                      {inline(cell.tokens, `${key}.r.${rowIndex}.${cellIndex}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )
    }
    case 'hr':
      return <hr key={key} />
    case 'text':
      return <Fragment key={key}>{inline((token as Tokens.Text).tokens, key) ?? textOf((token as Tokens.Text).text)}</Fragment>
    case 'escape':
      return <Fragment key={key}>{textOf((token as Tokens.Escape).text)}</Fragment>
    case 'strong':
      return <strong key={key}>{inline((token as Tokens.Strong).tokens, key)}</strong>
    case 'em':
      return <em key={key}>{inline((token as Tokens.Em).tokens, key)}</em>
    case 'del':
      return <del key={key}>{inline((token as Tokens.Del).tokens, key)}</del>
    case 'codespan':
      return <code key={key}>{textOf((token as Tokens.Codespan).text)}</code>
    case 'br':
      return <br key={key} />
    case 'link': {
      const link = token as Tokens.Link
      const href = safeHref(link.href)
      if (!href) return <Fragment key={key}>{inline(link.tokens, key)}</Fragment>
      const external = /^https?:/i.test(href)
      return (
        <a key={key} href={href} {...(external ? { target: '_blank', rel: 'noreferrer noopener' } : {})}>
          {inline(link.tokens, key)}
        </a>
      )
    }
    case 'image':
      return <Fragment key={key}>{textOf((token as Tokens.Image).text)}</Fragment>
    default:
      return null
  }
}

export function SafeMarkdown({ source }: { source: string }) {
  const tokens = marked.lexer(source, { gfm: true, breaks: false })
  return <div className="learn-md">{tokens.map((token, index) => renderToken(token, String(index)))}</div>
}
