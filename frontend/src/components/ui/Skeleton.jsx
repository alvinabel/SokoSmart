export function Skeleton({ width = '100%', height = 16, radius = 8, className = '' }) {
  return <div className={`skeleton ${className}`} style={{ width, height, borderRadius: radius }} />
}

export function ListingCardSkeleton() {
  return (
    <div className="listing-card">
      <Skeleton height={170} radius={0} />
      <div className="listing-body">
        <Skeleton width="80%" />
        <Skeleton width="45%" height={20} />
        <Skeleton width="60%" height={12} />
      </div>
    </div>
  )
}

export default Skeleton