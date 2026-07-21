import React from 'react';
import { useParams } from 'react-router-dom';
import { StatsCard } from '../components/StatsCard';

export const ReportView = () => {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="space-y-6 fade-in max-w-5xl mx-auto">
      <div className="flex justify-between items-center glass-card p-6">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">Recon Report #{id}</h1>
          <p className="text-sm text-gray-400">Generated on {new Date().toLocaleDateString()}</p>
        </div>
        <button className="bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30 hover:bg-cyber-cyan/20 px-4 py-2 rounded-xl transition-colors flex items-center gap-2">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download PDF
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatsCard label="New Assets" value="24" trend={{ value: 5, isPositive: true }} />
        <StatsCard label="Exposed Endpoints" value="12" />
        <StatsCard label="High Risks Found" value="2" trend={{ value: 2, isPositive: false }} />
      </div>

      <div className="glass-card p-8 min-h-[600px] bg-white text-gray-900 rounded-2xl">
        {/* Placeholder for HTML report */}
        <h2 className="text-2xl font-bold mb-4">Executive Summary</h2>
        <p className="mb-4">This automated recon report covers recent findings for the target program. Several new subdomains were discovered along with exposed API endpoints that require review.</p>
        
        <h3 className="text-xl font-bold mb-2 mt-6">Top Findings</h3>
        <ul className="list-disc pl-5 mb-4">
          <li>Exposed admin panel at `admin.target.com`</li>
          <li>GraphQL introspection enabled at `api.target.com/graphql`</li>
        </ul>
      </div>
    </div>
  );
};
