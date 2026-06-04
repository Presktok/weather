import { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

const ROUTE_STYLES = {
  a: {
    id: 'a',
    label: 'Route A',
    subtitle: 'Shortest',
    color: '#3b82f6',
    mutedColor: '#475569',
  },
  b: {
    id: 'b',
    label: 'Route B',
    subtitle: 'Avoidance',
    color: '#22c55e',
    mutedColor: '#475569',
  },
}

function FitBounds({ paths }) {
  const map = useMap()
  useEffect(() => {
    if (!paths?.length) return
    const allPoints = paths.flatMap((p) => p.map((pt) => [pt.lat, pt.lon]))
    if (allPoints.length) map.fitBounds(allPoints, { padding: [48, 48] })
  }, [map, paths])
  return null
}

function MapResize() {
  const map = useMap()
  useEffect(() => {
    const t = setTimeout(() => map.invalidateSize(), 0)
    const onResize = () => map.invalidateSize()
    window.addEventListener('resize', onResize)
    return () => {
      clearTimeout(t)
      window.removeEventListener('resize', onResize)
    }
  }, [map])
  return null
}

function pathToLatLng(path) {
  return path.map((pt) => [pt.lat, pt.lon])
}

/** Full-route silhouette so A vs B shape is obvious when overlaid */
function RouteOutline({ path, style, isActive, showRisk }) {
  if (!path?.length) return null
  const positions = pathToLatLng(path)
  const { color, mutedColor } = style

  return (
    <>
      <Polyline
        positions={positions}
        pathOptions={{
          color: isActive ? '#0f172a' : mutedColor,
          weight: isActive ? 10 : 6,
          opacity: isActive ? 0.85 : 0.35,
          lineCap: 'round',
          lineJoin: 'round',
        }}
      />
      <Polyline
        positions={positions}
        pathOptions={{
          color: isActive ? color : mutedColor,
          weight: isActive ? (showRisk ? 5 : 7) : 4,
          opacity: isActive ? 0.95 : 0.45,
          dashArray: isActive ? undefined : '10 8',
          lineCap: 'round',
          lineJoin: 'round',
        }}
      />
    </>
  )
}

function RiskColoredRoute({ path, legs, style, isActive, routeKey }) {
  if (!path?.length || !legs?.length || !isActive) return null

  return (
    <>
      {legs.map((leg, i) => {
        const start = path[i]
        const end = path[i + 1]
        if (!start || !end) return null
        const color = leg.risk_color || style.color
        return (
          <Polyline
            key={`${routeKey}-seg-${leg.to}-${i}`}
            positions={[
              [start.lat, start.lon],
              [end.lat, end.lon],
            ]}
            pathOptions={{
              color,
              weight: 7,
              opacity: 0.95,
              lineCap: 'round',
              lineJoin: 'round',
            }}
          />
        )
      })}
      {legs.map((leg, i) => (
        <CircleMarker
          key={`${routeKey}-wp-${i}`}
          center={[leg.to_lat, leg.to_lon]}
          radius={6}
          pathOptions={{
            color: '#fff',
            fillColor: leg.risk_color || style.color,
            fillOpacity: 1,
            weight: 2,
          }}
        >
          <Popup>
            <div className="text-sm text-slate-800 min-w-[200px]">
              <p className="text-[10px] font-semibold uppercase tracking-wide" style={{ color: style.color }}>
                {style.label} · {style.subtitle}
              </p>
              <p className="font-bold mt-0.5">{leg.to}</p>
              <p>Wind: {leg.weather.wind} kn · Wave: {leg.weather.wave} m</p>
              <p>
                Risk: <strong style={{ color: leg.risk_color }}>{leg.risk}</strong>
              </p>
              <hr className="my-1 border-slate-200" />
              <p>
                STW {leg.stw_kn} kn → SOG {leg.sog_kn} kn (loss {leg.speed_loss_kn} kn)
              </p>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </>
  )
}

function PortMarker({ point, label, style, role }) {
  if (!point) return null
  return (
    <CircleMarker
      center={[point.lat, point.lon]}
      radius={role === 'departure' ? 9 : 8}
      pathOptions={{
        color: '#fff',
        fillColor: style.color,
        fillOpacity: 1,
        weight: 3,
      }}
    >
      <Popup>
        <div className="text-sm text-slate-800">
          <p className="font-bold">{point.name || label}</p>
          <p className="text-xs text-slate-500">{role === 'departure' ? 'Departure' : 'Destination'}</p>
        </div>
      </Popup>
    </CircleMarker>
  )
}

function MapLegend({ showRouteA, showRouteB, activeRoute }) {
  return (
    <div className="absolute bottom-3 left-3 z-[1000] rounded-lg border border-slate-600/80 bg-ocean-900/95 backdrop-blur px-3 py-2 text-xs shadow-lg pointer-events-none">
      <p className="text-slate-400 font-medium mb-1.5">Routes</p>
      <div className="space-y-1 mb-2">
        {showRouteA && (
          <div className="flex items-center gap-2">
            <span
              className="w-6 h-1 rounded-full"
              style={{
                background: ROUTE_STYLES.a.color,
                opacity: activeRoute === 'a' ? 1 : 0.45,
                outline: activeRoute === 'a' ? '2px solid white' : 'none',
              }}
            />
            <span className={activeRoute === 'a' ? 'text-blue-300 font-medium' : 'text-slate-500'}>
              Route A — shortest {activeRoute === 'a' ? '(focused)' : ''}
            </span>
          </div>
        )}
        {showRouteB && (
          <div className="flex items-center gap-2">
            <span
              className="w-6 h-1 rounded-full border border-dashed border-green-500"
              style={{
                background: activeRoute === 'b' ? ROUTE_STYLES.b.color : 'transparent',
                opacity: activeRoute === 'b' ? 1 : 0.5,
              }}
            />
            <span className={activeRoute === 'b' ? 'text-green-300 font-medium' : 'text-slate-500'}>
              Route B — avoidance {activeRoute === 'b' ? '(focused)' : ''}
            </span>
          </div>
        )}
      </div>
      <p className="text-slate-500 border-t border-slate-700 pt-1.5 mb-1">Risk (active route legs)</p>
      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-slate-300">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-green-500" /> Low
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-yellow-500" /> Med
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500" /> High
        </span>
      </div>
    </div>
  )
}

function MapRouteBadges({ showRouteA, showRouteB, activeRoute }) {
  return (
    <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1.5 pointer-events-none">
      {showRouteA && (
        <div
          className={`rounded-md px-2.5 py-1 text-xs font-semibold border shadow-md ${
            activeRoute === 'a'
              ? 'bg-blue-600/95 border-blue-400 text-white'
              : 'bg-slate-800/90 border-slate-600 text-slate-400'
          }`}
        >
          A · Main
        </div>
      )}
      {showRouteB && (
        <div
          className={`rounded-md px-2.5 py-1 text-xs font-semibold border shadow-md ${
            activeRoute === 'b'
              ? 'bg-green-600/95 border-green-400 text-white'
              : 'bg-slate-800/90 border-slate-600 text-slate-400'
          }`}
        >
          B · Detour
        </div>
      )}
    </div>
  )
}

export default function VoyageMap({
  routeA,
  routeB,
  activeRoute,
  showRouteA = true,
  showRouteB = true,
}) {
  const paths = useMemo(() => {
    const result = []
    if (showRouteA && routeA?.analysis?.route?.path) result.push(routeA.analysis.route.path)
    if (showRouteB && routeB?.analysis?.route?.path) result.push(routeB.analysis.route.path)
    return result
  }, [routeA, routeB, showRouteA, showRouteB])

  const dep = routeA?.analysis?.route?.departure || routeB?.analysis?.route?.departure
  const dest = routeA?.analysis?.route?.destination || routeB?.analysis?.route?.destination

  const renderInactiveFirst = activeRoute === 'b'

  const routeAEl = showRouteA && routeA?.analysis?.route?.path && (
    <RouteLayer
      routeKey="a"
      analysis={routeA.analysis}
      style={ROUTE_STYLES.a}
      isActive={activeRoute === 'a'}
      showBoth={showRouteA && showRouteB}
    />
  )

  const routeBEl = showRouteB && routeB?.analysis?.route?.path && (
    <RouteLayer
      routeKey="b"
      analysis={routeB.analysis}
      style={ROUTE_STYLES.b}
      isActive={activeRoute === 'b'}
      showBoth={showRouteA && showRouteB}
    />
  )

  return (
    <div className="relative h-full w-full">
      <MapContainer
        center={[20, 50]}
        zoom={3}
        className="h-full w-full z-0"
        scrollWheelZoom
        style={{ minHeight: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapResize />
        <FitBounds paths={paths} />
        {renderInactiveFirst ? (
          <>
            {routeAEl}
            {routeBEl}
          </>
        ) : (
          <>
            {routeBEl}
            {routeAEl}
          </>
        )}
        {dep && (
          <PortMarker point={dep} label="Departure" style={ROUTE_STYLES.a} role="departure" />
        )}
        {dest && (
          <PortMarker point={dest} label="Destination" style={ROUTE_STYLES.b} role="destination" />
        )}
      </MapContainer>
      <MapLegend showRouteA={showRouteA} showRouteB={showRouteB} activeRoute={activeRoute} />
      <MapRouteBadges showRouteA={showRouteA} showRouteB={showRouteB} activeRoute={activeRoute} />
    </div>
  )
}

function RouteLayer({ routeKey, analysis, style, isActive, showBoth }) {
  const path = analysis.route.path
  const legs = analysis.legs
  const showRisk = isActive || !showBoth

  return (
    <>
      <RouteOutline path={path} style={style} isActive={isActive} showRisk={showRisk} />
      <RiskColoredRoute
        path={path}
        legs={legs}
        style={style}
        isActive={isActive}
        routeKey={routeKey}
      />
    </>
  )
}
