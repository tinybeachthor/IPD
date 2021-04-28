import React from 'react'
import { useDeck } from 'mdx-deck'

import logoTudelft from './logo-tudelft.svg'

const Footer = () => {
  const state = useDeck()

  const slideNumber = state.index + 1
  const slidesTotal = state.length

  return (
    <footer
      style={{
        padding: '0.5rem 2rem',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'baseline',
      }}
    >
      <img
        src={logoTudelft}
        style={{
          maxHeight: '40px',
        }}
      />
      <span>{slideNumber} of {slidesTotal}</span>
    </footer>
  )
}

export default Footer
