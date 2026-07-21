import React from 'react';

interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export const StatsCard: React.FC<StatsCardProps> = ({ label, value, icon, trend }) => {
  return (
    <div className="glass-card p-6 relative overflow-hidden group hover:border-cyber-cyan/50 transition-colors">
      <div className="absolute -right-6 -top-6 w-24 h-24 bg-cyber-cyan/10 rounded-full blur-2xl group-hover:bg-cyber-cyan/20 transition-colors" />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium mb-1">{label}</p>
          <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
          
          {trend && (
            <div className={`mt-2 text-xs font-medium flex items-center ${trend.isPositive ? 'text-cyber-emerald' : 'text-cyber-red'}`}>
              <span className="mr-1">{trend.isPositive ? '↑' : '↓'}</span>
              {trend.value}% from last week
            </div>
          )}
        </div>
        
        {icon && (
          <div className="p-3 bg-white/5 rounded-xl border border-white/10 text-cyber-cyan">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
};
