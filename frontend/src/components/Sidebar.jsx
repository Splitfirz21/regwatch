import clsx from 'clsx';
import { Layers } from 'lucide-react';

const SECTORS = [
    "Energy & Chemicals", "Precision Engineering", "Electronics", "Aerospace", "Marine & Offshore",
    "Logistics", "Air Transport", "Land Transport", "Sea Transport",
    "ICT", "Media",
    "Food Services", "Retail", "Hotels",
    "Real Estate", "Security", "Environmental Services", "Wholesale Trade",
    "Healthcare", "Education", "Professional Services",
    "Financial Services", "Construction"
];

export default function Sidebar({ selected, onSelect }) {
    return (
        <div className="w-64 bg-gray-900 border-r border-gray-800 h-screen overflow-y-auto flex-shrink-0 sticky top-0 custom-scrollbar">
            <div className="p-6 border-b border-gray-800">
                <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent flex items-center gap-2">
                    <Layers className="text-blue-400" />
                    RegWatch SG
                </h1>
                <p className="text-xs text-gray-500 mt-2">Intelligent Regulatory Monitoring</p>
            </div>

            <div className="p-4 space-y-1">
                <button
                    onClick={() => onSelect(null)}
                    className={clsx(
                        "w-full text-left px-4 py-3 rounded-lg text-sm transition-all",
                        selected === null
                            ? "bg-blue-600 text-white font-medium shadow-lg shadow-blue-500/20"
                            : "text-gray-400 hover:bg-gray-800 hover:text-white"
                    )}
                >
                    All Sectors
                </button>

                <div className="h-px bg-gray-800 my-2 mx-4" />

                {SECTORS.map(sector => (
                    <button
                        key={sector}
                        onClick={() => onSelect(sector)}
                        className={clsx(
                            "w-full text-left px-4 py-2.5 rounded-lg text-sm transition-all",
                            selected === sector
                                ? "bg-gray-800 text-blue-400 border-l-2 border-blue-400 font-medium"
                                : "text-gray-400 hover:bg-gray-800 hover:text-white border-l-2 border-transparent"
                        )}
                    >
                        {sector}
                    </button>
                ))}
            </div>
        </div>
    );
}
