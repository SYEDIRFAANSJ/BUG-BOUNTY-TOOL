import React from 'react';

interface BadgeProps {
  label: string;
  type?: 'high' | 'medium' | 'low' | 'new' | 'default';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ label, type = 'default', className = '' }) => {
  let typeClasses = 'bg-gray-500/20 text-gray-300 border-gray-500/30';
  
  if (type === 'high') typeClasses = 'badge-high';
  if (type === 'medium') typeClasses = 'badge-medium';
  if (type === 'low') typeClasses = 'badge-low';
  if (type === 'new') typeClasses = 'bg-cyber-cyan/20 text-cyber-cyan border-cyber-cyan/30 pulse-new';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${typeClasses} ${className}`}>
      {label}
    </span>
  );
};
