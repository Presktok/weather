import { useCallback, useRef } from 'react'

/**
 * @param {(delta: number, event: MouseEvent) => void} onDelta - pixels moved since drag start
 * @param {{ axis?: 'x' | 'y' }} options
 */
export function useDragResize(onDelta, { axis = 'y' } = {}) {
  const onDeltaRef = useRef(onDelta)
  onDeltaRef.current = onDelta

  return useCallback(
    (e) => {
      e.preventDefault()
      const start = axis === 'y' ? e.clientY : e.clientX

      const onMove = (ev) => {
        const current = axis === 'y' ? ev.clientY : ev.clientX
        onDeltaRef.current(current - start, ev)
      }

      const onUp = () => {
        document.removeEventListener('mousemove', onMove)
        document.removeEventListener('mouseup', onUp)
        document.body.style.cursor = ''
        document.body.style.userSelect = ''
      }

      document.body.style.cursor = axis === 'y' ? 'ns-resize' : 'ew-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', onMove)
      document.addEventListener('mouseup', onUp)
    },
    [axis],
  )
}

export function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n))
}
