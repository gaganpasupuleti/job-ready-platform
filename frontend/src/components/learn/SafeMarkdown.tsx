import { marked, type Token, type Tokens } from 'marked'
import { Fragment, type ReactNode } from 'react'

import { VisualExplanation } from '@/components/learn/VisualExplanation'
import { approvedLearningImageSrc, splitLessonParagraph } from '@/lib/learningVisuals'
import { isDroppedMarkdownToken, omitChromeOwnedBlocks, safeHref } from '@/lib/richText'
import { cn } from '@/utils/cn'

/** marked escapes text for HTML. React text nodes must receive the decoded characters. */
function textOf(value: string): string {
  return value
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, '&')
}

function inline(tokens: Token[] | undefined, key: string, placement: 'flow' | 'phrasing' = 'phrasing'): ReactNode {
  if (!tokens?.length) return null
  return tokens.map((token, index) => renderToken(token, `${key}.${index}`, placement))
}

function renderToken(token: Token, key: string, placement: 'flow' | 'phrasing' = 'flow'): ReactNode {
  if (isDroppedMarkdownToken(token.type)) return null
  switch (token.type) {
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
    case 'paragraph': {
      const paragraph = token as Tokens.Paragraph
      const segments = splitLessonParagraph(paragraph.tokens ?? [])
      const blocks = segments.map((segment, index) => {
        if (segment.kind === 'diagram') return renderToken(segment.token as Token, `${key}.d.${index}`, 'flow')
        return (
          <p key={`${key}.p.${index}`}>{inline(segment.tokens, `${key}.p.${index}`)}</p>
        )
      })
      if (segments.length === 1 && segments[0].kind === 'inline') return blocks[0]
      return <Fragment key={key}>{blocks}</Fragment>
    }
    case 'blockquote':
      return <blockquote key={key}>{inline((token as Tokens.Blockquote).tokens, key, 'flow')}</blockquote>
    case 'list': {
      const list = token as Tokens.List
      const Tag = list.ordered ? 'ol' : 'ul'
      return (
        <Tag key={key} start={list.ordered && list.start !== '' ? list.start : undefined}>
          {list.items.map((item, index) => (
            <li key={`${key}.${index}`}>{inline(item.tokens, `${key}.${index}`, 'flow')}</li>
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
                    {inline(cell.tokens, `${key}.h.${index}`, 'flow')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, rowIndex) => (
                <tr key={`${key}.r.${rowIndex}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={`${key}.r.${rowIndex}.${cellIndex}`} style={cell.align ? { textAlign: cell.align } : undefined}>
                      {inline(cell.tokens, `${key}.r.${rowIndex}.${cellIndex}`, 'flow')}
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
    case 'image': {
      const image = token as Tokens.Image
      const alt = textOf(image.text)
      const src = approvedLearningImageSrc(image.href)
      if (!src || placement === 'phrasing') return <Fragment key={key}>{alt}</Fragment>
      return <VisualExplanation key={key} src={src} alt={alt} caption={image.title ? textOf(image.title) : null} />
    }
    default:
      return null
  }
}

export function SafeMarkdown({
  source,
  breaks = false,
  className,
  pageTitle,
  ownedHeadings,
}: {
  source: string
  breaks?: boolean
  className?: string
  pageTitle?: string | null
  ownedHeadings?: string[]
}) {
  const tokens = omitChromeOwnedBlocks(marked.lexer(source, { gfm: true, breaks }), {
    title: pageTitle,
    headings: ownedHeadings,
  })
  return (
    <div className={cn('learn-md', className)}>
      {tokens.map((token, index) => renderToken(token, String(index)))}
    </div>
  )
}
