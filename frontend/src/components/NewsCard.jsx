import { useState, useEffect } from 'react';
import { ExternalLink, Calendar, Plus, X, ThumbsUp, ThumbsDown } from 'lucide-react';
import clsx from 'clsx';
import { SECTORS, AGENCIES } from '../constants';
import API_BASE_URL from '../config';

const Highlight = ({ text, highlight }) => {
    if (!highlight || !text) return text;
    // Escape special regex chars
    const safeHighlight = highlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const parts = text.split(new RegExp(`(${safeHighlight})`, 'gi'));
    return (
        <span>
            {parts.map((part, i) =>
                part.toLowerCase() === highlight.toLowerCase() ? (
                    <span key={i} className="bg-yellow-300/60 dark:bg-yellow-500/40 text-black dark:text-white rounded px-0.5 font-bold shadow-sm ring-1 ring-yellow-500/20">
                        {part}
                    </span>
                ) : (
                    part
                )
            )}
        </span>
    );
};

// onToggleSave and isSaved added
export default function NewsCard({ item, onRemove, onAdd, onUpdate, highlight, isSaved, onToggleSave }) {
    const [vote, setVote] = useState(null); // 'like' | 'dislike' | null
    const [isAdded, setIsAdded] = useState(false);
    const [adding, setAdding] = useState(false);

    // Edit Mode State
    const [editing, setEditing] = useState(null); // 'sector' or 'agency'
    const [localSector, setLocalSector] = useState(item.sector);
    const [localAgency, setLocalAgency] = useState(item.agency);

    // Sync with props if they change externally (e.g. refresh from scan)
    useEffect(() => {
        setLocalSector(item.sector);
        setLocalAgency(item.agency);
    }, [item.sector, item.agency]);

    useEffect(() => {
        setIsAdded(item.isAdded || false);
    }, [item.isAdded]);

    const handleVote = (type) => {
        if (vote) return; // Prevent multiple votes
        setVote(type);
        onFeedback(item.id, type === 'like');
    };

    const handleAddClick = async () => {
        if (adding || isAdded) return;
        setAdding(true);
        try {
            await onAdd(item);
            setIsAdded(true);
        } catch (e) {
            console.error(e);
        } finally {
            setAdding(false);
        }
    };

    const handleUpdate = async (field, value) => {
        if (!value) return; // ignore empty
        const originalValue = field === 'sector' ? localSector : localAgency;

        // Optimistic Update
        if (field === 'sector') setLocalSector(value);
        else setLocalAgency(value);
        setEditing(null);

        try {
            const API_Base = API_BASE_URL;
            const res = await fetch(`${API_Base}/items/${item.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: value })
            });

            if (!res.ok) {
                // Revert on failure
                if (field === 'sector') setLocalSector(originalValue);
                else setLocalAgency(originalValue);
                console.error("Update failed");
            } else {
                // Success - Call Parent Update for Immediate UI Feedback
                if (onUpdate) {
                    onUpdate(item.id, { [field]: value });
                }
                if (onFeedback) onFeedback();
            }
        } catch (err) {
            console.error(err);
            if (field === 'sector') setLocalSector(originalValue);
            else setLocalAgency(originalValue);
        }
    };



    return (
        <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-all duration-300 shadow-xl shadow-black/20 group hover:scale-[1.01] h-full flex flex-col">

            {/* Remove Button */}
            {!onAdd && (
                <button
                    onClick={() => onRemove(item.id)}
                    className="absolute -top-2 -right-2 bg-gray-700 text-gray-400 hover:bg-red-500 hover:text-white p-1 rounded-full shadow-md opacity-0 group-hover:opacity-100 transition-all z-10"
                    title="Remove and see less like this"
                >
                    <X size={14} />
                </button>
            )}

            <div className="flex justify-between items-start mb-4 flex-1">
                <div className="flex-1">
                    {/* Tags - Editable */}
                    <div className="flex gap-2 mb-3 flex-wrap items-center">
                        {/* SECTOR */}
                        {editing === 'sector' ? (
                            <select
                                className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-900/80 text-blue-200 border border-blue-500/30 outline-none focus:ring-2 focus:ring-blue-500 max-w-[150px]"
                                value={localSector}
                                onChange={(e) => handleUpdate('sector', e.target.value)}
                                onBlur={() => setEditing(null)}
                                autoFocus
                            >
                                {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                        ) : (
                            <div
                                onClick={() => setEditing('sector')}
                                className={clsx(
                                    "px-2 py-0.5 rounded-full text-[10px] font-medium border cursor-pointer hover:bg-opacity-80 transition-colors uppercase tracking-wider select-none",
                                    localSector === 'General'
                                        ? "bg-gray-700 text-gray-300 border-gray-600 hover:bg-gray-600"
                                        : "bg-blue-500/10 text-blue-300 border-blue-500/20 hover:bg-blue-500/20"
                                )}
                                title="Click to edit Sector"
                            >
                                {localSector}
                            </div>
                        )}

                        {/* AGENCY */}
                        {editing === 'agency' ? (
                            <input
                                className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-purple-900/80 text-purple-200 border border-purple-500/30 outline-none focus:ring-2 focus:ring-purple-500 min-w-[100px]"
                                value={localAgency}
                                onChange={(e) => setLocalAgency(e.target.value)}
                                onBlur={(e) => handleUpdate('agency', e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleUpdate('agency', e.target.value);
                                }}
                                autoFocus
                                placeholder="Agency1, Agency2..."
                            />
                        ) : (
                            localAgency && localAgency !== "Unknown" && (
                                <>
                                    {localAgency.split(',').map((ag, idx) => (
                                        <div
                                            key={idx}
                                            onClick={() => setEditing('agency')}
                                            className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20 uppercase tracking-wider cursor-pointer hover:bg-purple-500/20 transition-colors select-none"
                                            title="Click to edit Agencies"
                                        >
                                            {ag.trim()}
                                        </div>
                                    ))}
                                </>
                            )
                        )}

                        {(!localAgency || localAgency === "Unknown") && (
                            <div
                                onClick={() => setEditing('agency')}
                                className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-800 text-gray-500 border border-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-700 transition-colors select-none"
                                title="Click to set Agency"
                            >
                                + Agency
                            </div>
                        )}

                        {item.is_circular && (
                            <span className="inline-block px-3 py-1 text-xs font-bold text-yellow-400 bg-yellow-900/30 rounded-full border border-yellow-500/20 shadow-glow-gold">
                                CIRCULAR
                            </span>
                        )}

                        {/* Impact Badge - Editable */}
                        {item.impact_rating && (
                            <button
                                onClick={() => {
                                    const levels = ['High', 'Medium', 'Low'];
                                    const next = levels[(levels.indexOf(item.impact_rating) + 1) % levels.length];
                                    handleUpdate('impact_rating', next);
                                }}
                                className={clsx(
                                    "inline-block px-2 py-0.5 text-[10px] font-bold rounded-full border uppercase tracking-wider shadow-sm transition-all hover:scale-105 active:scale-95 cursor-pointer select-none",
                                    item.impact_rating === 'High' && "bg-red-500/20 text-red-300 border-red-500/30 animate-pulse shadow-red-900/40 hover:bg-red-500/30",
                                    item.impact_rating === 'Medium' && "bg-amber-500/20 text-amber-300 border-amber-500/30 hover:bg-amber-500/30",
                                    item.impact_rating === 'Low' && "bg-slate-500/20 text-slate-300 border-slate-500/30 hover:bg-slate-500/30",
                                )}
                                title="Click to change Impact"
                            >
                                {item.impact_rating} Impact
                            </button>
                        )}
                    </div>

                    {/* Header / Title */}
                    <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group-hover:underline block mb-3"
                    >
                        <h3 className="text-lg font-bold text-white group-hover:text-blue-300 transition-colors leading-tight line-clamp-2">
                            <Highlight text={item.title} highlight={highlight} />
                        </h3>
                    </a>

                    {/* Summary */}
                    <div className="text-gray-400 text-sm leading-relaxed border-l-2 border-gray-700 pl-4 line-clamp-3 overflow-hidden text-ellipsis">
                        <Highlight text={(item.summary || "").replace(/<[^>]+>/g, '')} highlight={highlight} />
                    </div>
                    {/* Related Sources */}
                    {item.related_sources && item.related_sources.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-gray-700/50">
                            <span className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider mr-2">Also seen on:</span>
                            <div className="flex flex-wrap gap-2 mt-1">
                                {item.related_sources.map((src, idx) => (
                                    <a
                                        key={idx}
                                        href={src.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[10px] text-blue-400 hover:text-blue-300 hover:underline bg-blue-900/20 px-1.5 py-0.5 rounded border border-blue-500/20"
                                        title={`View on ${src.source}`}
                                    >
                                        {src.source}
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
                <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-500 hover:text-white transition-colors self-start mt-1"
                >
                    <ExternalLink size={20} />
                </a>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-gray-700/50 mt-auto gap-4">
                <div className="flex items-center text-xs text-gray-500 min-w-0">
                    <span className="font-semibold text-gray-300 mr-2 truncate">{item.source}</span>
                    <Calendar size={12} className="mr-1 flex-shrink-0" />
                    <span className="whitespace-nowrap">{new Date(item.published_at).toLocaleDateString()}</span>
                </div>

                <div className="flex gap-2 items-center flex-shrink-0">
                    {onAdd ? (
                        <button
                            onClick={handleAddClick}
                            disabled={isAdded || adding}
                            className={clsx(
                                "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shadow-lg whitespace-nowrap",
                                isAdded
                                    ? "bg-gray-700 text-gray-400 cursor-default"
                                    : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/20"
                            )}
                        >
                            {isAdded ? (
                                <><span>Added</span></>
                            ) : (
                                <><Plus size={14} />{adding ? "Adding..." : "Add"}</>
                            )}
                        </button>
                    ) : (
                        <>
                            {onToggleSave && (
                                <button
                                    onClick={() => onToggleSave(item.id)}
                                    className={clsx(
                                        "p-2 rounded-full transition-all duration-200 mr-1",
                                        isSaved
                                            ? "bg-blue-500/20 text-blue-400"
                                            : "hover:bg-gray-700 text-gray-500 hover:text-blue-400"
                                    )}
                                    title={isSaved ? "Unsave" : "Save for later"}
                                >
                                    {/* Import Bookmark from lucide-react first! Need to check imports */}
                                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" /></svg>
                                </button>
                            )}
                            <button
                                onClick={() => handleVote('like')}
                                disabled={!!vote}
                                className={clsx(
                                    "p-2 rounded-full transition-all duration-200",
                                    vote === 'like'
                                        ? "bg-green-500/20 text-green-400"
                                        : "hover:bg-gray-700 text-gray-500 hover:text-green-400"
                                )}
                            >
                                <ThumbsUp size={18} className={clsx(vote === 'like' && "fill-current")} />
                            </button>
                            <button
                                onClick={() => handleVote('dislike')}
                                disabled={!!vote}
                                className={clsx(
                                    "p-2 rounded-full transition-all duration-200",
                                    vote === 'dislike'
                                        ? "bg-red-500/20 text-red-400"
                                        : "hover:bg-gray-700 text-gray-500 hover:text-red-400"
                                )}
                            >
                                <ThumbsDown size={18} className={clsx(vote === 'dislike' && "fill-current")} />
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div >
    );
}
