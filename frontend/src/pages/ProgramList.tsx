import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DataTable } from '../components/DataTable';
import { StatsCard } from '../components/StatsCard';
import { Badge } from '../components/Badge';
import { getPrograms } from '../lib/api';

export const ProgramList = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data: response, isLoading } = useQuery({
    queryKey: ['programs'],
    queryFn: () => getPrograms().then(res => res.data),
    refetchInterval: 60000,
  });

  const programs = response?.items || [];
  
  const filteredPrograms = programs.filter((p: any) => 
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
    (statusFilter ? p.status === statusFilter : true)
  );

  const columns = [
    { 
      key: 'name', 
      header: 'Program Name',
      render: (row: any) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center text-xs font-bold border border-white/20">
            {row.platform === 'hackerone' ? 'H1' : row.platform === 'bugcrowd' ? 'BC' : 'IN'}
          </div>
          <div>
            <div className="font-semibold text-white">{row.name}</div>
            <div className="text-xs text-gray-500">{row.platform}</div>
          </div>
          {row.isNew && <Badge label="New" type="new" className="ml-2" />}
        </div>
      )
    },
    { 
      key: 'status', 
      header: 'Status',
      render: (row: any) => (
        <Badge label={row.status} type={row.status === 'active' ? 'low' : 'medium'} />
      )
    },
    { key: 'bounty_status', header: 'Bounty' },
    { 
      key: 'last_updated', 
      header: 'Last Updated',
      render: (row: any) => new Date(row.last_updated).toLocaleDateString()
    },
    { key: 'assets_count', header: 'Assets Count' },
  ];

  return (
    <div className="space-y-6 fade-in">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard label="Total Programs" value={programs.length} trend={{ value: 12, isPositive: true }} />
        <StatsCard label="New This Week" value="5" trend={{ value: 2, isPositive: true }} />
        <StatsCard label="Scope Changes" value="14" trend={{ value: 8, isPositive: false }} />
        <StatsCard label="High-Risk Findings" value="3" trend={{ value: 10, isPositive: false }} />
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-center glass-card p-4">
        <div className="relative w-full sm:w-96">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search programs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-navy-950/50 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-cyber-cyan/50 focus:ring-1 focus:ring-cyber-cyan/50 transition-all placeholder-gray-600"
          />
        </div>
        
        <div className="flex gap-4 w-full sm:w-auto">
          <select 
            className="bg-navy-950/50 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-cyber-cyan/50 appearance-none min-w-[120px]"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <DataTable
        columns={columns}
        data={filteredPrograms}
        isLoading={isLoading}
        onRowClick={(row) => navigate(`/programs/${row.id}`)}
      />
    </div>
  );
};
