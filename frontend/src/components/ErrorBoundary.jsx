import { Component } from 'react'

/**
 * Shows `fallback` instead of crashing the whole page when a child
 * component throws (used around the 3D hero and around each page).
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error) {
    console.error('ZYNTRA component error:', error)
  }

  render() {
    if (this.state.hasError) return this.props.fallback ?? null
    return this.props.children
  }
}
