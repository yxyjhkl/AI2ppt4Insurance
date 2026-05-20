import { useState, useCallback, useRef } from 'react'

interface Snapshot<T> {
  past: T[]
  present: T
  future: T[]
}

export function useUndoRedo<T>(initial: T, maxHistory: number = 50) {
  const [state, setState] = useState<Snapshot<T>>({
    past: [],
    present: initial,
    future: [],
  })
  const skipRef = useRef(false)

  const canUndo = state.past.length > 0
  const canRedo = state.future.length > 0

  const set = useCallback((newPresent: T) => {
    if (skipRef.current) {
      setState(s => ({ ...s, present: newPresent }))
      skipRef.current = false
      return
    }

    setState(s => ({
      past: [...s.past.slice(-maxHistory + 1), s.present],
      present: newPresent,
      future: [],
    }))
  }, [maxHistory])

  const undo = useCallback(() => {
    setState(s => {
      if (s.past.length === 0) return s
      const previous = s.past[s.past.length - 1]
      const newFuture = [s.present, ...s.future].slice(0, maxHistory)
      return {
        past: s.past.slice(0, -1),
        present: previous,
        future: newFuture,
      }
    })
  }, [maxHistory])

  const redo = useCallback(() => {
    setState(s => {
      if (s.future.length === 0) return s
      const next = s.future[0]
      return {
        past: [...s.past, s.present],
        present: next,
        future: s.future.slice(1),
      }
    })
  }, [])

  const setWithoutHistory = useCallback((val: T) => {
    skipRef.current = true
    setState(s => ({ ...s, present: val }))
  }, [])

  const reset = useCallback((initial: T) => {
    setState({ past: [], present: initial, future: [] })
  }, [])

  return {
    present: state.present,
    set,
    undo,
    redo,
    canUndo,
    canRedo,
    setWithoutHistory,
    reset,
  }
}
