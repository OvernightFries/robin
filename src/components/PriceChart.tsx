'use client'

import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  Filler
} from 'chart.js';
import { DailyData } from '@/types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PriceChartProps {
  dailyData: DailyData;
  symbol: string;
}

const PriceChart: React.FC<PriceChartProps> = ({ dailyData, symbol }) => {
  const [chartData, setChartData] = useState<any>(null);

  useEffect(() => {
    if (!dailyData || !dailyData.dates || dailyData.dates.length === 0) {
      setChartData(null);
      return;
    }

    const formatDate = (timestamp: string) => {
      const date = new Date(timestamp);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
    };

    const dates = dailyData.dates.map(formatDate);
    const prices = dailyData.prices;
    const volumes = dailyData.volumes;

    const data = {
      labels: dates,
      datasets: [
        {
          label: 'Price',
          data: prices,
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          tension: 0.1,
          yAxisID: 'y',
          fill: true,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: 'Volume',
          data: volumes,
          borderColor: 'rgb(53, 162, 235)',
          backgroundColor: 'rgba(53, 162, 235, 0.1)',
          fill: true,
          tension: 0.1,
          yAxisID: 'y1',
          pointRadius: 0,
          borderWidth: 2
        }
      ]
    };

    setChartData(data);
  }, [dailyData]);

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false
    },
    scales: {
      x: {
        grid: {
          display: false
        }
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Price ($)'
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)'
        }
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: {
          display: true,
          text: 'Volume'
        },
        grid: {
          display: false
        }
      }
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20
        }
      },
      title: {
        display: true,
        text: `${symbol} Price and Volume`,
        padding: {
          top: 10,
          bottom: 20
        }
      }
    }
  };

  if (!chartData) {
    return (
      <div className="w-full h-[400px] bg-wizard-background/50 rounded-lg p-4 flex items-center justify-center">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-wizard-green rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-4 h-4 bg-wizard-blue rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-4 h-4 bg-wizard-purple rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-[400px] bg-wizard-background/50 rounded-lg p-4">
      <Line options={options} data={chartData} />
    </div>
  );
};

export default PriceChart; 
