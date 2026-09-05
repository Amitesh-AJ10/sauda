import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DispatchSprite } from './DispatchSprite'

describe('DispatchSprite', () => {
  it('renders a driver sprite', () => {
    render(<DispatchSprite />)
    expect(screen.getByTestId('dispatch-sprite')).toBeInTheDocument()
  })
})
