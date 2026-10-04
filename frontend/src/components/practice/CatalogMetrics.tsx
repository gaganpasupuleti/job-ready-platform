interface Metric {
  label: string
  value: string
}

export function CatalogMetrics({ metrics }: { metrics: Metric[] }) {
  return (
    <dl className="catalog-metrics">
      {metrics.map((metric) => (
        <div key={metric.label}>
          <dt>{metric.label}</dt>
          <dd>{metric.value}</dd>
        </div>
      ))}
    </dl>
  )
}
