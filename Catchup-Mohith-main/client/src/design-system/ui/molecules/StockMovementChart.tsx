// client/src/design-system/ui/molecules/StockMovementChart.tsx
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type StockMovementData = {
  day: string
  stock_in?: number
  stock_out?: number
  stockIn?: number
  stockOut?: number
}

type StockMovementChartProps = {
  data: StockMovementData[]
}

export function StockMovementChart({ data }: StockMovementChartProps): JSX.Element {
  const normalizedData = data.map((entry) => ({
    day: entry.day,
    stock_in: entry.stock_in ?? entry.stockIn ?? 0,
    stock_out: entry.stock_out ?? entry.stockOut ?? 0,
  }))

  return (
    <ResponsiveContainer height={240} width="100%">
      <BarChart data={normalizedData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke="#e0e0e0" strokeDasharray="3 3" />
        <XAxis dataKey="day" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="stock_in" fill="#0e9c8e" name="Stock In" radius={[2, 2, 0, 0]} />
        <Bar
          dataKey="stock_out"
          fill="#8a3ffc"
          name="Stock Out"
          radius={[2, 2, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}
