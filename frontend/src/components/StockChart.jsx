import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function StockChart({ stock, prices }) {
  const chartData = prices.map(p => ({
    date: new Date(p.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
    종가: p.close,
    고가: p.high,
    저가: p.low,
  }))

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold mb-4">
        {stock.name} ({stock.symbol})
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="종가" stroke="#2563eb" strokeWidth={2} />
          <Line type="monotone" dataKey="고가" stroke="#10b981" strokeWidth={1} />
          <Line type="monotone" dataKey="저가" stroke="#ef4444" strokeWidth={1} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default StockChart
