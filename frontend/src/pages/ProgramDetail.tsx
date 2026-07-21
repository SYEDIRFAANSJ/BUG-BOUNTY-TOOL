import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getProgram, getProgramAssets, getProgramEndpoints, getProgramReports } from '../lib/api';
import { StatsCard } from '../components/StatsCard';
import { Badge } from '../components/Badge';
import { DataTable } from '../components/DataTable';

export const ProgramDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'scope' | 'assets' | 'endpoints' | 'reports'>('scope');

  const { data: programRes, isLoading: programLoading } = useQuery({
    queryKey: ['program', id],
    queryFn: () => getProgram(id!).then(res => res.data),
    enabled: !!id,
  });

  const { data: assetsRes, isLoading: assetsLoading } = useQuery({
    queryKey: ['programAssets', id],
    queryFn: () => getProgramAssets(id!).then(res => res.data),
    enabled: activeTab === 'assets' && !!id,
  });

  const { data: endpointsRes, isLoading: endpointsLoading } = useQuery({
    queryKey: ['programEndpoints', id],
    queryFn: () => getProgramEndpoints(id!).then(res => res.data),
    enabled: activeTab === 'endpoints' && !!id,
  });

  const program = programRes;
  const inScope = program?.scopes?.filter((s: any) => s.eligibility_for_bounty || s.is_in_scope) || [];
  const outOfScope = program?.scopes?.filter((s: any) => !s.eligibility_for_bounty && !s.is_in_scope) || [];

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="glass-card p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-bold text-white tracking-tight">{program?.name || 'Loading...'}</h1>
            {program?.platform && (
              <Badge label={program.platform} type="default" />
            )}
          </div>
          <a href={program?.url} target="_blank" rel="noopener noreferrer" className="text-cyber-cyan hover:text-cyber-cyan/80 text-sm flex items-center gap-1 transition-colors">
            {program?.url}
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
        <button className="px-6 py-2.5 bg-white/5 border border-white/10 rounded-xl text-white font-medium hover:bg-white/10 hover:border-cyber-cyan/50 transition-all flex items-center gap-2 group">
          <svg className="w-5 h-5 text-gray-400 group-hover:text-cyber-cyan transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          Watch Program
        </button>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatsCard label="In-Scope Assets" value={inScope.length} />
        <StatsCard label="Total Subdomains" value={program?.stats?.subdomains || 0} />
        <StatsCard label="Live Assets" value={program?.stats?.live || 0} />
        <StatsCard label="Endpoints" value={program?.stats?.endpoints || 0} />
        <StatsCard label="High-Risk" value={program?.stats?.high_risk || 0} trend={{value: 0, isPositive: false}} />
      </div>

      {/* Tabs */}
      <div className="border-b border-white/10">
        <nav className="flex space-x-8">
          {(['scope', 'assets', 'endpoints', 'reports'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab
                  ? 'border-cyber-cyan text-cyber-cyan'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-500'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'scope' && (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <div className="w-2 h-6 bg-cyber-emerald rounded-full"></div>
                In Scope
              </h3>
              <div className="glass-card overflow-hidden">
                <table className="w-full text-left text-sm text-gray-300">
                  <thead className="bg-white/5 text-xs uppercase text-gray-400">
                    <tr><th className="px-6 py-4">Asset</th><th className="px-6 py-4">Type</th><th className="px-6 py-4">Eligibility</th></tr>
                  </thead>
                  <tbody>
                    {inScope.map((s: any, i: number) => (
                      <tr key={i} className="border-t border-white/10 hover:bg-white/5 transition-colors">
                        <td className="px-6 py-4 font-mono text-white">{s.asset_identifier}</td>
                        <td className="px-6 py-4"><Badge label={s.asset_type} type="default" /></td>
                        <td className="px-6 py-4"><Badge label="Bounty" type="low" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <div className="w-2 h-6 bg-cyber-red rounded-full"></div>
                Out of Scope
              </h3>
              <div className="glass-card overflow-hidden">
                <table className="w-full text-left text-sm text-gray-300">
                  <thead className="bg-white/5 text-xs uppercase text-gray-400">
                    <tr><th className="px-6 py-4">Asset</th><th className="px-6 py-4">Type</th></tr>
                  </thead>
                  <tbody>
                    {outOfScope.map((s: any, i: number) => (
                      <tr key={i} className="border-t border-white/10 hover:bg-white/5 transition-colors opacity-75">
                        <td className="px-6 py-4 font-mono text-gray-400">{s.asset_identifier}</td>
                        <td className="px-6 py-4"><Badge label={s.asset_type} type="default" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'assets' && (
          <DataTable
            isLoading={assetsLoading}
            data={assetsRes?.items || []}
            columns={[
              { key: 'domain', header: 'Subdomain', render: (row: any) => <span className="font-mono text-white">{row.domain}</span> },
              { key: 'ip_address', header: 'IP Address' },
              { key: 'status_code', header: 'Status', render: (row: any) => <Badge label={row.status_code?.toString() || 'N/A'} type={row.status_code === 200 ? 'low' : 'medium'} /> },
              { key: 'technologies', header: 'Tech Stack', render: (row: any) => (
                <div className="flex flex-wrap gap-1">
                  {row.technologies?.map((t: string) => <Badge key={t} label={t} type="default" />)}
                </div>
              )}
            ]}
          />
        )}

        {activeTab === 'endpoints' && (
          <DataTable
            isLoading={endpointsLoading}
            data={endpointsRes?.items || []}
            columns={[
              { key: 'method', header: 'Method', render: (row: any) => <Badge label={row.method} type="new" /> },
              { key: 'url', header: 'URL', render: (row: any) => <span className="font-mono text-gray-300 truncate max-w-md block" title={row.url}>{row.url}</span> },
              { key: 'risk', header: 'Risk', render: (row: any) => <Badge label={row.risk_priority || 'low'} type={row.risk_priority === 'high' ? 'high' : row.risk_priority === 'medium' ? 'medium' : 'low'} /> }
            ]}
          />
        )}

        {activeTab === 'reports' && (
          <div className="glass-card p-8 text-center text-gray-400">
            Reports module coming soon.
          </div>
        )}
      </div>
    </div>
  );
};
