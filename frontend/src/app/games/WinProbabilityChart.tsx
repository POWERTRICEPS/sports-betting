
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';


export interface ProbabilityDataPoint {
  time: string;
  home_prob: number;
  away_prob: number;
}

interface WinProbabilityChartProps {
  data: ProbabilityDataPoint[];
}

export default function WinProbabilityChart({ data }: WinProbabilityChartProps) {

  if (!data || data.length === 0) {
    return <div>No probability data available.</div>;
  }

  return (
    <div style={{ width: '100%', height: 400, backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <h3 style={{ textAlign: 'center', marginBottom: '20px' }}>Live Win Probability</h3>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          
          <XAxis 
            dataKey="time" 
            tick={{ fill: '#666' }} 
            tickMargin={10}
          />
          
          <YAxis 
            domain={[0, 1]} 
            tickFormatter={(tick: number) => `${(tick * 100).toFixed(0)}%`} 
            tick={{ fill: '#666' }}
          />
          
          <Tooltip 
            labelFormatter={(label: string) => `Time: ${label}`}
            formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
          />
          <Legend verticalAlign="top" height={36}/>
          
          <Line 
            type="stepAfter" 
            dataKey="home_prob" 
            name="Home Team Win %" 
            stroke="#1d2ae0" 
            strokeWidth={3} 
            dot={false} 
          />
          <Line 
            type="stepAfter" 
            dataKey="away_prob" 
            name="Away Team Win %" 
            stroke="#f3121d" 
            strokeWidth={3} 
            dot={false} 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}