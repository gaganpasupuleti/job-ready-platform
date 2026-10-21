import type { CSSProperties } from 'react'
import { Handle, Position } from '@xyflow/react'

type Side = 'left' | 'right' | 'top' | 'bottom'

const HANDLE_SIDES: Record<string, { position: Position; side: Side }> = {
  x1: { position: Position.Left, side: 'left' },
  w1: { position: Position.Left, side: 'left' },
  x2: { position: Position.Right, side: 'right' },
  w2: { position: Position.Right, side: 'right' },
  y1: { position: Position.Top, side: 'top' },
  z1: { position: Position.Top, side: 'top' },
  y2: { position: Position.Bottom, side: 'bottom' },
  z2: { position: Position.Bottom, side: 'bottom' },
}

function handleStyle(side: Side): CSSProperties {
  switch (side) {
    case 'left':
    case 'right':
      return { top: '50%', transform: 'translateY(-50%)' }
    case 'top':
    case 'bottom':
      return { left: '50%', transform: 'translateX(-50%)' }
    default: {
      const _exhaustive: never = side
      return _exhaustive
    }
  }
}

export function RoadmapHandles() {
  return (
    <>
      {Object.entries(HANDLE_SIDES).flatMap(([id, { position, side }]) => [
        <Handle
          key={`${id}-s`}
          id={`${id}-s`}
          type="source"
          position={position}
          className="ors-handle"
          style={handleStyle(side)}
        />,
        <Handle
          key={`${id}-t`}
          id={`${id}-t`}
          type="target"
          position={position}
          className="ors-handle"
          style={handleStyle(side)}
        />,
      ])}
    </>
  )
}
