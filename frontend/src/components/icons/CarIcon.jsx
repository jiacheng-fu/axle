import React from 'react'

export default function CarIcon({className = 'icon', width=28, height=28}){
  return (
    <svg className={className} width={width} height={height} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M3 12l1.5-4.5A2 2 0 0 1 6.4 6h11.2a2 2 0 0 1 1.9 1.5L21 12" stroke="#0B0B0C" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M5 16v1.5A1.5 1.5 0 0 0 6.5 19H7" stroke="#0B0B0C" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M19 16v1.5A1.5 1.5 0 0 1 17.5 19H17" stroke="#0B0B0C" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="7.5" cy="16.5" r="1" fill="#0B0B0C" />
      <circle cx="16.5" cy="16.5" r="1" fill="#0B0B0C" />
    </svg>
  )
}
