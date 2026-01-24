import React from 'react'   

export default function SkeletonCard() {
  return (
    <div className="skeleton-card skeleton" aria-hidden>
      <div style={{display:'flex', justifyContent:'space-between'}}>
        <div style={{width: '60%', height: 16, borderRadius: 6}} />
        <div style={{width: '20%', height: 12, borderRadius: 6}} />
      </div>

      <div style={{marginTop:12, width: '40%', height: 12, borderRadius:6}} />

      <div style={{display:'flex', gap:8, marginTop:18}}>
        <div style={{width:80, height:28, borderRadius:999}} />
        <div style={{width:100, height:28, borderRadius:999}} />
      </div>
    </div>
  )
}
