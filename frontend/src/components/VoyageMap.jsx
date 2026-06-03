import { useEffect, useLayoutEffect, useMemo, useState } from 'react'
import { createPortal } from 'react-dom'
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet'

function FitBounds({ paths }) {
  const map = useMap()
  useEffect(() => {
    if (!paths?.length) return
    const allPoints = paths.flatMap((p) => p.map((pt) => [pt.lat, pt.lon]))
    if (allPoints.length) map.fitBounds(allPoints, { padding: [40, 40] })
  }, [map, paths])
  return null
}

/** Week 1: one polyline segment per leg, colored by risk */
function RiskColoredRoute({ path, legs, muted, routeColor }) {
  if (!path?.length || !legs?.length) return null

  const fallbackColor = routeColor || '#64748b'

  return (
    <>
      {legs.map((leg, i) => {
        const start = path[i]
        const end = path[i + 1]
        if (!start || !end) return null
        const color = muted ? '#64748b' : leg.risk_color || fallbackColor
        return (
          <Polyline
            key={`seg-${leg.to}-${i}`}
            positions={[
              [start.lat, start.lon],
              [end.lat, end.lon],
            ]}
            pathOptions={{
              color,
              weight: muted ? 3 : 6,
              opacity: muted ? 0.35 : 0.9,
              dashArray: muted ? '6 8' : undefined,
            }}
          />
        )
      })}
      {legs.map((leg, i) => (
        <CircleMarker
          key={`wp-${i}`}
          center={[leg.to_lat, leg.to_lon]}
          radius={muted ? 5 : 7}
          pathOptions={{
            color: '#fff',
            fillColor: muted ? '#64748b' : leg.risk_color,
            fillOpacity: muted ? 0.5 : 0.95,
            weight: 2,
          }}
        >
          <Popup>
            <div className="text-sm text-slate-800 min-w-[180px]">
              <p className="font-bold">{leg.to}</p>
              <p>Wind: {leg.weather.wind} kn</p>
              <p>Wave: {leg.weather.wave} m</p>
              <p>Risk: <strong style={{ color: leg.risk_color }}>{leg.risk}</strong></p>
              <hr className="my-1" />
              <p>STW: {leg.stw_kn} kn → SOG: {leg.sog_kn} kn</p>
              <p>Loss: {leg.speed_loss_kn} kn</p>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </>
  )
}

function useAnchorRect(anchorRef) {
  const [rect, setRect] = useState(null)

  useLayoutEffect(() => {
    const anchor = anchorRef?.current
    if (!anchor) return

    const update = () => {
      const { top, left, width, height } = anchor.getBoundingClientRect()
      setRect({ top, left, width, height })
    }

    update()
    const observer = new ResizeObserver(update)
    observer.observe(anchor)
    window.addEventListener('resize', update)
    window.addEventListener('scroll', update, true)

    return () => {
      observer.disconnect()
      window.removeEventListener('resize', update)
      window.removeEventListener('scroll', update, true)
    }
  }, [anchorRef])

  return rect
}

export default function VoyageMap({
  routeA,
  routeB,
  activeRoute,
  anchorRef,
  showRouteA = true,
  showRouteB = true,
}) {
  const paths = useMemo(() => {
    const result = []
    if (showRouteA && routeA?.analysis?.route?.path) result.push(routeA.analysis.route.path)
    if (showRouteB && routeB?.analysis?.route?.path) result.push(routeB.analysis.route.path)
    return result
  }, [routeA, routeB, showRouteA, showRouteB])

  const anchorRect = useAnchorRect(anchorRef)
  const mapRoot = typeof document !== 'undefined' ? document.getElementById('map-root') : null

  const map = (
    <MapContainer center={[20, 50]} zoom={3} className="h-full w-full" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds paths={paths} />
      {showRouteA && routeA && (
        <RiskColoredRoute
          path={routeA.analysis.route.path}
          legs={routeA.analysis.legs}
          muted={showRouteB && activeRoute !== 'a'}
          routeColor="#3b82f6"
        />
      )}
      {showRouteB && routeB && (
        <RiskColoredRoute
          path={routeB.analysis.route.path}
          legs={routeB.analysis.legs}
          muted={showRouteA && activeRoute !== 'b'}
          routeColor="#22c55e"
        />
      )}
    </MapContainer>
  )

  if (mapRoot && anchorRect) {
    return createPortal(
      <div
        className="pointer-events-auto overflow-hidden"
        style={{
          position: 'fixed',
          top: anchorRect.top,
          left: anchorRect.left,
          width: anchorRect.width,
          height: anchorRect.height,
          zIndex: 15,
        }}
      >
        {map}
      </div>,
      mapRoot,
    )
  }

  return map
}
