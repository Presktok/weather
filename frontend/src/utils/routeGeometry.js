/** Great-circle interpolation for smoother map polylines (display only). */

const toRad = (deg) => (deg * Math.PI) / 180
const toDeg = (rad) => (rad * 180) / Math.PI

export function interpolateGreatCircle(lat1, lon1, lat2, lon2, steps = 8) {
  const φ1 = toRad(lat1)
  const λ1 = toRad(lon1)
  const φ2 = toRad(lat2)
  const λ2 = toRad(lon2)

  const sinΔ =
    Math.sin((φ2 - φ1) / 2) ** 2 +
    Math.cos(φ1) * Math.cos(φ2) * Math.sin((λ2 - λ1) / 2) ** 2
  const Δ = 2 * Math.asin(Math.min(1, Math.sqrt(sinΔ)))

  if (Δ < 1e-8) {
    return [{ lat: lat1, lon: lon1 }]
  }

  const points = []
  for (let i = 0; i <= steps; i++) {
    const f = i / steps
    const a = Math.sin((1 - f) * Δ) / Math.sin(Δ)
    const b = Math.sin(f * Δ) / Math.sin(Δ)
    const x = a * Math.cos(φ1) * Math.cos(λ1) + b * Math.cos(φ2) * Math.cos(λ2)
    const y = a * Math.cos(φ1) * Math.sin(λ1) + b * Math.cos(φ2) * Math.sin(λ2)
    const z = a * Math.sin(φ1) + b * Math.sin(φ2)
    points.push({
      lat: toDeg(Math.atan2(z, Math.sqrt(x * x + y * y))),
      lon: toDeg(Math.atan2(y, x)),
    })
  }
  return points
}

/** Add intermediate points along each leg for curved map display. */
export function densifyPath(path, stepsPerLeg = 8) {
  if (!path?.length) return []
  if (path.length < 2) return [...path]

  const out = []
  for (let i = 0; i < path.length - 1; i++) {
    const seg = interpolateGreatCircle(
      path[i].lat,
      path[i].lon,
      path[i + 1].lat,
      path[i + 1].lon,
      stepsPerLeg,
    )
    if (i > 0) seg.shift()
    out.push(...seg)
  }
  return out
}

export function pathToLatLng(path) {
  return path.map((pt) => [pt.lat, pt.lon])
}

export function densifyPathLatLng(path, stepsPerLeg = 8) {
  return pathToLatLng(densifyPath(path, stepsPerLeg))
}
