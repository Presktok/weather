function RiskBadge({ risk }) {
  const colors = {
    LOW: 'bg-green-500/20 text-green-400 border-green-500/40',
    MEDIUM: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
    HIGH: 'bg-red-500/20 text-red-400 border-red-500/40',
    SAFE: 'bg-green-500/20 text-green-400 border-green-500/40',
    EARLY: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
    'HIGH RISK': 'bg-red-500/20 text-red-400 border-red-500/40',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${colors[risk] || colors.LOW}`}>
      {risk}
    </span>
  )
}

function MetricRow({ label, value, highlight }) {
  return (
    <div className={`flex justify-between py-2 border-b border-slate-700/50 last:border-0 ${highlight ? 'text-amber-300' : ''}`}>
      <span className="text-slate-400 text-sm">{label}</span>
      <span className={`font-medium text-sm ${highlight ? 'text-amber-300' : 'text-white'}`}>{value}</span>
    </div>
  )
}

function ImpactLine({ label, amount, unit = '', isPositive }) {
  const n = Number(amount)
  const formatted = unit === '$'
    ? `$${n.toLocaleString()}`
    : `${n.toLocaleString()}${unit ? ` ${unit}` : ''}`
  return (
    <p className={isPositive ? 'text-green-300' : 'text-red-300'}>
      {label}: <span className="font-bold">+{formatted}</span>
    </p>
  )
}

export default function Dashboard({ data, loading }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        <div className="animate-pulse">Loading voyage analysis...</div>
      </div>
    )
  }

  if (!data) return null

  const {
    route_a: routeA,
    route_b: routeB,
    comparison,
    recommendation,
    weather_impact: weatherImpact,
    high_risk_zones: riskZones,
    route_scores: scores,
    savings,
    laycan_context: laycanCtx,
    charter_warning: charterWarning,
    weather_sources: weatherSources,
    distance,
    operational_advice: operationalAdvice,
  } = data

  const charterAlert = charterWarning || recommendation.charter_warning
  const recCard = recommendation.recommendation_card
  const recIsB = recommendation.route_id === routeB.analysis.route.id
  const breakdown = recommendation.score_breakdown || scores.breakdown
  const net = savings.net_impact
  const scoreGap = scores.score_gap ?? Math.abs(scores.route_b - scores.route_a)

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-green-500/40 bg-green-500/10 p-4">
        {charterAlert && (
          <div className="mb-4 rounded-lg border border-red-500/50 bg-red-500/15 p-3">
            <p className="text-sm font-bold text-red-300 uppercase tracking-wide">
              {charterAlert.title || 'WARNING'}
            </p>
            <p className="text-sm text-red-200/90 mt-2">{charterAlert.message}</p>
            {charterAlert.remediation && (
              <div className="mt-3 pt-2 border-t border-red-500/30 grid grid-cols-1 gap-1 text-sm">
                <p className="text-amber-100">
                  Estimated speed required to meet laycan:{' '}
                  <strong className="text-white">~{charterAlert.remediation.estimated_speed_required_kn} kn</strong>
                  {' '}(commanded {charterAlert.remediation.current_commanded_speed_kn} kn)
                </p>
                <p className="text-amber-100">
                  Required departure:{' '}
                  <strong className="text-white">Before {charterAlert.remediation.required_departure_before}</strong>
                </p>
                {charterAlert.remediation.note && (
                  <p className="text-xs text-slate-400">{charterAlert.remediation.note}</p>
                )}
              </div>
            )}
            {charterAlert.actions?.length > 0 && (
              <ul className="mt-2 space-y-1">
                {charterAlert.actions.map((action) => (
                  <li key={action} className="text-xs text-amber-200/90 flex gap-2">
                    <span className="shrink-0">→</span>
                    {action}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        <h3 className="font-bold text-green-400 text-lg">
          Recommended {recommendation.route_label}
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">{recommendation.route_name}</p>
        {recommendation.summary && (
          <p className="text-sm text-slate-300 mt-2">{recommendation.summary}</p>
        )}
        {recommendation.timing_note && (
          <p className="text-sm text-amber-200/90 mt-2 p-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
            {recommendation.timing_note}
          </p>
        )}
        {recCard?.reasons?.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs text-slate-500 uppercase tracking-wide">Reason</p>
            <ul className="mt-1.5 space-y-1.5">
              {recCard.reasons.map((r) => (
                <li key={r} className="text-sm text-slate-200 flex gap-2">
                  <span className="text-green-400 shrink-0">✓</span>
                  {r}
                </li>
              ))}
            </ul>
            {recCard.tradeoffs?.length > 0 && (
              <>
                <p className="text-xs text-slate-500 uppercase tracking-wide mt-3">Tradeoff</p>
                <ul className="mt-1.5 space-y-1">
                  {recCard.tradeoffs.map((t) => (
                    <li key={t} className="text-sm text-amber-300/90 flex gap-2">
                      <span className="shrink-0">△</span>
                      {t}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        ) : (
          <>
            <p className="text-xs text-slate-500 mt-2 uppercase tracking-wide">Why this route (safety first)</p>
            <ul className="mt-2 space-y-1.5">
              {recommendation.benefits?.map((b) => (
                <li key={b} className="text-sm text-slate-200 flex gap-2">
                  <span className="text-green-400 shrink-0">✓</span>
                  {b}
                </li>
              ))}
            </ul>
          </>
        )}
        {recommendation.secondary_benefits?.length > 0 && (
          <ul className="mt-2 space-y-1 pl-1">
            {recommendation.secondary_benefits.map((b) => (
              <li key={b} className="text-xs text-slate-500 flex gap-2">
                <span className="shrink-0">·</span>
                {b}
              </li>
            ))}
          </ul>
        )}
        {recommendation.tradeoffs?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-green-500/20">
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Tradeoff</p>
            <ul className="space-y-1">
              {recommendation.tradeoffs.map((t) => (
                <li key={t} className="text-sm text-amber-300/90 flex gap-2">
                  <span className="shrink-0">△</span>
                  {t}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {weatherSources && (
        <div className="rounded-xl border border-slate-700 bg-ocean-800 p-4">
          <h3 className="font-semibold text-white mb-2">Weather Data Source</h3>
          <MetricRow label="Primary" value={weatherSources.primary} />
          {weatherSources.fallback && (
            <MetricRow label="Fallback" value={weatherSources.fallback} />
          )}
          <p className="text-[10px] text-slate-500 mt-2">
            {weatherSources.legs_open_meteo} legs Open-Meteo · {weatherSources.legs_demo} legs demo model
          </p>
        </div>
      )}

      {distance && (
        <div className="rounded-xl border border-slate-700 bg-ocean-800 p-4">
          <h3 className="font-semibold text-white mb-2">Route Distance</h3>
          <MetricRow label="Route A" value={`${distance.route_a_nm.toLocaleString()} nm`} />
          <MetricRow label="Route B" value={`${distance.route_b_nm.toLocaleString()} nm`} />
          <MetricRow
            label="Extra distance (B vs A)"
            value={`${distance.extra_nm >= 0 ? '+' : ''}${distance.extra_nm.toLocaleString()} nm`}
            highlight={distance.extra_nm > 0}
          />
        </div>
      )}

      {operationalAdvice && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
          <h3 className="font-semibold text-amber-200 mb-2">Operational Advice</h3>
          <MetricRow label="Current average SOG" value={`${operationalAdvice.current_average_sog_kn} kn`} />
          <MetricRow label="Commanded speed" value={`${operationalAdvice.commanded_speed_kn} kn`} />
          {operationalAdvice.required_speed_kn != null && (
            <MetricRow
              label="Speed required for laycan"
              value={`~${operationalAdvice.required_speed_kn} kn`}
              highlight
            />
          )}
          {operationalAdvice.required_departure_before && (
            <MetricRow
              label="Depart before"
              value={operationalAdvice.required_departure_before}
              highlight
            />
          )}
          {operationalAdvice.note && (
            <p className="text-xs text-slate-500 mt-2">{operationalAdvice.note}</p>
          )}
        </div>
      )}

      <div className="rounded-xl border border-slate-700 bg-ocean-800 p-4">
        <h3 className="font-semibold text-white mb-1">Route Score</h3>
        <p className="text-xs text-slate-500 mb-3">Normalized 0–100 scale (higher = better voyage quality)</p>
        {scores.laycan_penalty_note && (
          <p className="text-xs text-amber-400/90 mb-3 p-2 rounded bg-amber-500/10 border border-amber-500/20">
            {scores.laycan_penalty_note}
          </p>
        )}
        <div className="grid grid-cols-2 gap-3">
          <div className={`rounded-lg p-3 border ${recIsB ? 'border-slate-700' : 'border-green-500/50 bg-green-500/5'}`}>
            <p className="text-xs text-blue-400">Route A</p>
            <p className="text-2xl font-bold text-white mt-1">{scores.route_a}<span className="text-base text-slate-400">/100</span></p>
            <p className="text-[10px] text-slate-500 mt-1">
              cost {scores.components.route_a.cost} + delay {scores.components.route_a.delay} + risk {scores.components.route_a.risk} + laycan {scores.components.route_a.laycan}
            </p>
          </div>
          <div className={`rounded-lg p-3 border ${recIsB ? 'border-green-500/50 bg-green-500/5' : 'border-slate-700'}`}>
            <p className="text-xs text-green-400">Route B</p>
            <p className="text-2xl font-bold text-white mt-1">{scores.route_b}<span className="text-base text-slate-400">/100</span></p>
            <p className="text-[10px] text-slate-500 mt-1">
              cost {scores.components.route_b.cost} + delay {scores.components.route_b.delay} + risk {scores.components.route_b.risk} + laycan {scores.components.route_b.laycan}
            </p>
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-3">
          Weights: Cost {scores.weights.cost * 100}% · Delay {scores.weights.delay * 100}% · Risk {scores.weights.risk * 100}% · Laycan {scores.weights.laycan * 100}%
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Score gap: <span className="text-white font-medium">{scoreGap} points</span>
          {recIsB ? ' (Route B leads)' : ' (Route A leads)'}
        </p>
        {breakdown?.components?.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-700">
            <p className="text-xs text-slate-400 uppercase tracking-wide mb-2">
              Score drivers ({recommendation.route_label} vs {recommendation.alternative_label})
            </p>
            <ul className="space-y-1">
              {breakdown.components.map((c) => (
                <li key={c.dimension} className="text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">{c.label}</span>
                    <span className={c.points >= 0 && !c.penalty_applied_each ? 'text-green-400 font-medium' : 'text-red-400 font-medium'}>
                      {c.penalty_applied_each ? `-${Math.abs(c.points)} pts each` : `${c.points >= 0 ? '+' : ''}${c.points} pts`}
                    </span>
                  </div>
                  {c.detail && c.penalty_applied_each && (
                    <p className="text-[10px] text-slate-500 mt-0.5">{c.detail}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-slate-700 bg-ocean-800 p-4">
        <h3 className="font-semibold text-white mb-3">Laycan & ETA</h3>
        <MetricRow label="Departure" value={laycanCtx?.departure} />
        <MetricRow label="Laycan window" value={`${laycanCtx?.laycan_start} → ${laycanCtx?.laycan_end}`} />
        <div className="mt-3 grid grid-cols-1 gap-2 text-sm">
          {[['Route A', laycanCtx?.route_a], ['Route B', laycanCtx?.route_b]].map(([name, lc]) => (
            <div key={name} className="rounded-lg bg-ocean-900/80 p-3 border border-slate-700">
              <div className="flex justify-between items-center mb-1">
                <span className="text-slate-400 text-xs">{name}</span>
                <RiskBadge risk={lc?.risk} />
              </div>
              <p className="text-white text-sm">ETA: {lc?.predicted_eta_display} ({lc?.voyage_days}d voyage)</p>
              <p className="text-xs text-slate-500 mt-1">{lc?.detail}</p>
            </div>
          ))}
        </div>
      </div>

      {weatherImpact && (
        <div className="rounded-xl border border-slate-700 bg-ocean-800 p-4">
          <h3 className="font-semibold text-white mb-1">Weather Impact Summary (Route A)</h3>
          <p className="text-xs text-slate-500 mb-3">{weatherImpact.baseline_note}</p>
          <MetricRow label="Average speed loss" value={`${weatherImpact.average_speed_loss_kn} kn`} />
          <MetricRow label="Weather delay" value={`${weatherImpact.total_weather_delay_hours} hrs`} />
          <MetricRow label="High-risk legs" value={`${weatherImpact.high_risk_leg_count}`} highlight={weatherImpact.high_risk_leg_count > 0} />
          <MetricRow label="Max wave height" value={`${weatherImpact.max_wave_height_m} m`} />
          {weatherImpact.weather_fuel_penalty_mt > 0 && (
            <MetricRow
              label="Extra fuel from weather"
              value={`${weatherImpact.weather_fuel_penalty_mt} MT`}
              highlight
            />
          )}
          <MetricRow
            label="Cost of weather delay"
            value={`$${weatherImpact.weather_delay_cost_usd.toLocaleString()}`}
            highlight={weatherImpact.weather_delay_cost_usd > 0}
          />
          <div className="flex justify-between pt-2 mt-1">
            <span className="text-slate-400 text-sm">Laycan status</span>
            <RiskBadge risk={weatherImpact.laycan_status} />
          </div>
        </div>
      )}

      <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
        <h3 className="font-semibold text-red-400 mb-3">High Risk Zones (Route A)</h3>
        {riskZones.length === 0 ? (
          <p className="text-sm text-slate-400">No high-risk segments on main route.</p>
        ) : (
          <ul className="space-y-3">
            {riskZones.map((z) => (
              <li key={z.waypoint} className="rounded-lg bg-ocean-900/80 p-3 border border-red-500/20">
                <p className="font-medium text-white text-sm">{z.waypoint}</p>
                <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-300">
                  {z.wave_height_m != null && (
                    <span>Wave: <strong className="text-slate-100">{z.wave_height_m} m</strong></span>
                  )}
                  {z.wind_speed_kn != null && (
                    <span>Wind: <strong className="text-slate-100">{z.wind_speed_kn} kn</strong></span>
                  )}
                  <span>Speed loss: <strong className="text-slate-100">{z.expected_speed_loss_kn} kn</strong></span>
                  <span>Delay: <strong className="text-slate-100">{z.expected_delay_hours} hrs</strong></span>
                  <span className="col-span-2">Risk: <RiskBadge risk={z.risk_level} /></span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rounded-xl border border-blue-500/30 bg-blue-500/5 p-4">
        <h3 className="font-semibold text-blue-300 mb-3">Route Comparison vs Baseline</h3>
        <div className="grid grid-cols-1 gap-3 text-sm">
          <div className="rounded-lg bg-ocean-900 p-3">
            <p className="text-xs text-slate-500 uppercase">{savings.without_optimization.label}</p>
            <p className="text-slate-300 mt-1">Fuel: <span className="text-white font-semibold">{savings.without_optimization.fuel_mt} MT</span></p>
            <p className="text-slate-300">Cost: <span className="text-white font-semibold">${savings.without_optimization.fuel_cost_usd.toLocaleString()}</span></p>
            <p className="text-slate-300">Delay: <span className="text-white font-semibold">{savings.without_optimization.delay_hours} hrs</span></p>
          </div>
          <div className="rounded-lg bg-ocean-900 p-3 border border-green-500/30">
            <p className="text-xs text-green-500/80 uppercase">{savings.with_recommended.label}</p>
            <p className="text-slate-300 mt-1">Fuel: <span className="text-white font-semibold">{savings.with_recommended.fuel_mt} MT</span></p>
            <p className="text-slate-300">Cost: <span className="text-white font-semibold">${savings.with_recommended.fuel_cost_usd.toLocaleString()}</span></p>
            <p className="text-slate-300">Delay: <span className="text-white font-semibold">{savings.with_recommended.delay_hours} hrs</span></p>
          </div>
          <div className={`rounded-lg p-3 border ${net.fuel_cost_is_savings ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
            <p className={`text-xs uppercase font-semibold ${net.fuel_cost_is_savings ? 'text-green-400' : 'text-red-400'}`}>
              {net.fuel_cost_is_savings ? 'Net savings vs Route A' : 'Additional cost vs Route A'}
            </p>
            {net.fuel_cost_is_savings ? (
              <>
                <ImpactLine label="Fuel savings" amount={net.fuel_cost_usd} unit="$" isPositive />
                <ImpactLine label="Fuel saved" amount={net.fuel_mt} unit="MT" isPositive />
              </>
            ) : (
              <>
                <ImpactLine label="Additional fuel cost" amount={net.fuel_cost_usd} unit="$" isPositive={false} />
                <ImpactLine label="Additional fuel" amount={net.fuel_mt} unit="MT" isPositive={false} />
              </>
            )}
            {net.delay_is_reduction ? (
              <ImpactLine label="Delay reduction" amount={net.delay_hours} unit="hrs" isPositive />
            ) : (
              <ImpactLine label="Additional delay" amount={net.delay_hours} unit="hrs" isPositive={false} />
            )}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-ocean-900">
            <tr>
              <th className="text-left p-3 text-slate-400">Metric</th>
              <th className="text-right p-3 text-blue-400">Route A</th>
              <th className="text-right p-3 text-green-400">Route B</th>
            </tr>
          </thead>
          <tbody>
            {comparison.metrics.map((row) => (
              <tr key={row.metric} className="border-t border-slate-700">
                <td className="p-3 text-slate-300">{row.metric}</td>
                <td className="p-3 text-right">{row.route_a}</td>
                <td className="p-3 text-right">{row.route_b}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="rounded-xl border border-slate-700 overflow-hidden max-h-48 overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="bg-ocean-900 sticky top-0">
            <tr>
              <th className="text-left p-2 text-slate-400">Waypoint</th>
              <th className="text-right p-2 text-slate-400">Wind</th>
              <th className="text-right p-2 text-slate-400">Wave</th>
              <th className="text-right p-2 text-slate-400">SOG</th>
              <th className="text-right p-2 text-slate-400">Risk</th>
            </tr>
          </thead>
          <tbody>
            {routeA.analysis.legs.map((leg) => (
              <tr key={leg.to} className="border-t border-slate-800">
                <td className="p-2 text-slate-300">{leg.to}</td>
                <td className="p-2 text-right">{leg.weather.wind} kn</td>
                <td className="p-2 text-right">{leg.weather.wave} m</td>
                <td className="p-2 text-right">{leg.sog_kn} kn</td>
                <td className="p-2 text-right"><RiskBadge risk={leg.risk} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
