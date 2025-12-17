
import React, { useEffect, useState } from 'react';
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts';
import { FileText, Download, X, Info, Filter } from 'lucide-react';
import ReactMarkdown from 'react-markdown'; // Assuming we have this or native rendering, actually we don't have react-markdown installed. Let's use simple <pre> or dangerouslySetInnerHTML or install it. 
// We likely don't have react-markdown. I'll stick to whitespace-pre-wrap div.

export default function AnalyticsDashboard() {
    const [data, setData] = useState(null);
    const [globalData, setGlobalData] = useState(null); // For Pie Chart Context
    const [loading, setLoading] = useState(true);
    const [impactFilter, setImpactFilter] = useState('All');

    useEffect(() => {
        fetchStats();
    }, [impactFilter]);

    // Fetch Global Stats once on mount for Pie Context
    useEffect(() => {
        const fetchGlobal = async () => {
            try {
                const API = `http://${window.location.hostname}:8005`;
                const res = await fetch(`${API}/stats?impact=All`);
                const json = await res.json();
                setGlobalData(json);
            } catch (e) {
                console.error("Global stats fetch failed", e);
            }
        };
        fetchGlobal();
    }, []);

    const fetchStats = async () => {
        try {
            const API = `http://${window.location.hostname}:8005`;
            const res = await fetch(`${API}/stats?impact=${impactFilter}`);
            const json = await res.json();
            setData(json);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading || !data || !globalData) return <div className="p-10 text-center text-gray-500">Loading Analytics...</div>;

    const COLORS = {
        High: '#ef4444',
        Medium: '#f59e0b',
        Low: '#64748b'
    };

    return (
        <div
            className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500 min-h-screen"
            onClick={() => setImpactFilter('All')}
        >
            {/* ... (Header & Legend code remains same, skipping for brevity in replace block if possible) ... */}
            {/* Actually, replace_file_content needs contiguous block. 
                I will skip the middle parts and focus on the Pie Chart section if possible, 
                but I updated state definition at the top. I need a big block or multiple blocks. 
                Let's do the top state block first.
            */}
            <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Analytics</h2>
                    <p className="text-gray-400">Overview of regulatory landscape</p>
                </div>
                {/* Filter buttons removed as per request */}
            </div>

            {/* Impact Legend - Clickable Filters */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* HIGH IMPACT */}
                <div
                    onClick={(e) => { e.stopPropagation(); setImpactFilter(impactFilter === 'High' ? 'All' : 'High'); }}
                    className={`p-4 rounded-xl border border-gray-800 bg-red-900/10 cursor-pointer transition-all hover:bg-red-900/20 active:scale-[0.98] ${impactFilter === 'High' ? 'ring-2 ring-red-500 shadow-lg shadow-red-900/20 scale-[1.02]' : 'hover:border-red-500/30'}`}
                >
                    <div className="flex items-center gap-2 mb-2">
                        <span className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
                        <h4 className="font-bold text-red-400 uppercase tracking-wider text-xs">High Impact</h4>
                    </div>
                    <p className="text-sm text-gray-400">
                        New Laws, Bills Passed, Penalties, Major Policy Shifts.
                        {/* Removed: Requires immediate attention. */}
                    </p>
                </div>

                {/* MEDIUM IMPACT */}
                <div
                    onClick={(e) => { e.stopPropagation(); setImpactFilter(impactFilter === 'Medium' ? 'All' : 'Medium'); }}
                    className={`p-4 rounded-xl border border-gray-800 bg-amber-900/10 cursor-pointer transition-all hover:bg-amber-900/20 active:scale-[0.98] ${impactFilter === 'Medium' ? 'ring-2 ring-amber-500 shadow-lg shadow-amber-900/20 scale-[1.02]' : 'hover:border-amber-500/30'}`}
                >
                    <div className="flex items-center gap-2 mb-2">
                        <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                        <h4 className="font-bold text-amber-400 uppercase tracking-wider text-xs">Medium Impact</h4>
                    </div>
                    <p className="text-sm text-gray-400">
                        Public Consultations, Draft Standards, Advisories, Guidelines.
                        {/* Modified: Removed Grants/Speeches, Added Advisories/Guidelines. Removed footer text. */}
                    </p>
                </div>

                {/* LOW IMPACT */}
                <div
                    onClick={(e) => { e.stopPropagation(); setImpactFilter(impactFilter === 'Low' ? 'All' : 'Low'); }}
                    className={`p-4 rounded-xl border border-gray-800 bg-slate-800/20 cursor-pointer transition-all hover:bg-slate-800/40 active:scale-[0.98] ${impactFilter === 'Low' ? 'ring-2 ring-slate-500 shadow-lg shadow-slate-900/20 scale-[1.02]' : 'hover:border-slate-500/30'}`}
                >
                    <div className="flex items-center gap-2 mb-2">
                        <span className="w-3 h-3 rounded-full bg-slate-500"></span>
                        <h4 className="font-bold text-slate-400 uppercase tracking-wider text-xs">Low Impact</h4>
                    </div>
                    <p className="text-sm text-gray-400">
                        Community Events, Awards, Routine Updates, Reminders, Speeches.
                        {/* Added: Speeches. Removed: Informational only. */}
                    </p>
                </div>
            </div>

            {/* Stats Grid - Always 3 Columns now (`Total+Breakdown` OR `Impact Card` + `Sector` + `Agency`) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {impactFilter === 'All' ? (
                    /* Combined Card for All View */
                    <div className="bg-gray-900/50 border border-gray-800 p-6 rounded-2xl flex flex-col justify-between">
                        <div>
                            <h4 className="text-sm text-gray-500 uppercase tracking-widest font-mono mb-2">Total Items</h4>
                            <div className="text-3xl font-bold text-white mb-4">{data.total}</div>
                        </div>
                        <div className="flex gap-4 text-xs font-medium border-t border-gray-800 pt-4">
                            <div className="flex flex-col">
                                <span className="text-red-400">High</span>
                                <span className="text-white text-lg">{data.impact.find(d => d.name === 'High')?.value || 0}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-amber-400">Medium</span>
                                <span className="text-white text-lg">{data.impact.find(d => d.name === 'Medium')?.value || 0}</span>
                            </div>
                            <div className="flex flex-col">
                                <span className="text-slate-400">Low</span>
                                <span className="text-white text-lg">{data.impact.find(d => d.name === 'Low')?.value || 0}</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    /* Filtered View: Only the active Impact Card */
                    <StatCard
                        title={`${impactFilter} Impact`}
                        value={data.total}
                        color={
                            impactFilter === 'High' ? 'text-red-400' :
                                impactFilter === 'Medium' ? 'text-amber-400' : 'text-slate-400'
                        }
                    />
                )}

                <StatCard title="Top Sector" value={data.sectors[0]?.name || '-'} />
                <StatCard title="Top Agency" value={data.agencies[0]?.name || '-'} />
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 min-h-[400px]">
                {/* Impact Mix - Uses Global Context */}
                <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-gray-200 mb-6">Impact Distribution</h3>
                    <ResponsiveContainer width="100%" height="85%">
                        <PieChart>
                            <Pie
                                data={globalData.impact}
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {globalData.impact.map((entry, index) => {
                                    // Highlight Logic
                                    const isActive = impactFilter === 'All' || entry.name === impactFilter;
                                    const opacity = isActive ? 1 : 0.2; // Dim others
                                    // Make selected segment slightly larger? Optional.
                                    return (
                                        <Cell
                                            key={`cell-${index}`}
                                            fill={COLORS[entry.name] || '#8884d8'}
                                            fillOpacity={opacity}
                                            stroke={isActive ? '#fff' : 'none'}
                                            strokeWidth={isActive ? 2 : 0}
                                        />
                                    );
                                })}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Agency Leaderboard */}
                <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                    <h3 className="text-lg font-semibold text-gray-200 mb-6">Top Agencies (Activity)</h3>
                    <ResponsiveContainer width="100%" height="85%">
                        <BarChart data={data.agencies.slice(0, 5)} layout="vertical">
                            <XAxis type="number" hide />
                            <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#9ca3af' }} />
                            <Tooltip
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }}
                            />
                            <Bar dataKey="value" fill="#8b5cf6" radius={[0, 4, 4, 0]} barSize={20} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}

function StatCard({ title, value, color = "text-white" }) {
    return (
        <div className="bg-gray-900/50 border border-gray-800 p-6 rounded-2xl">
            <h4 className="text-sm text-gray-500 uppercase tracking-widest font-mono mb-2">{title}</h4>
            <div className={`text-3xl font-bold ${color}`}>{value}</div>
        </div>
    );
}
