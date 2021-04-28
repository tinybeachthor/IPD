import React from 'react'
import { Emojione } from 'react-emoji-render'

import './Spatial.css'

const Selected = ({children, color}) =>
  <div
    style={{
      backgroundColor: color,
    }}>
    {children}
  </div>

const Badge = ({children, badge}) =>
  <div>
    <div className="BadgeOverlay">
      {badge}
    </div>
    {children}
  </div>

const Shout = ({children, text, range}) =>
  <div>
    <div className="ShoutOverlay">
      <Emojione
        svg
        text={text}
      />
    </div>
    {range && <div className="ShoutRange"></div>}
    {children}
  </div>

const Empty = () => <div className="Empty"></div>

const Emoji = ({emoji}) =>
  <div>
    <Emojione
      svg
      text={emoji}
      options={{className: "Emoji"}}
    />
  </div>

const Grid = ({children}) => {
  return (
    <div className="Grid">
      {children}
    </div>
  )
}

export { Grid, Empty, Emoji, Selected, Badge, Shout }
