import { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, Search } from 'lucide-react';

export default function SearchableDropdown({ options, value, onChange, placeholder, prefixIcon }) {
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const wrapperRef = useRef(null);

    // Reset search when closing or selecting
    useEffect(() => {
        if (!isOpen) setSearchTerm("");
    }, [isOpen]);

    // Close on click outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [wrapperRef]);

    const filteredOptions = options.filter(opt =>
        opt.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="relative" ref={wrapperRef}>
            {/* Trigger / Input */}
            <div
                className="relative bg-white/5 backdrop-blur-md border border-white/10 hover:bg-white/10 hover:border-white/20 rounded-xl flex items-center transition-all cursor-text group w-full md:min-w-[200px] shadow-sm"
                onClick={() => {
                    setIsOpen(true);
                    // If we want to start searching immediately, maybe clear term?
                    // Or keep showing current value?
                    // User pattern: Click -> see list -> type to filter.
                }}
            >
                {prefixIcon && <div className="pl-3 text-gray-500 group-hover:text-blue-400">{prefixIcon}</div>}

                <input
                    type="text"
                    className="bg-transparent border-none text-gray-200 text-sm w-full py-2 pl-3 pr-8 focus:outline-none placeholder-gray-500 cursor-text"
                    placeholder={value || placeholder} // If value is set, show it as placeholder-ish (but we want to edit it?)
                    // Actually, standard pattern: Input shows current value. If user types, it filters.
                    // But "All Sectors" isn't in the list?
                    value={isOpen ? searchTerm : (value || "")}
                    onChange={(e) => {
                        setSearchTerm(e.target.value);
                        if (!isOpen) setIsOpen(true);
                    }}
                    onFocus={() => setIsOpen(true)}
                />

                <div className="absolute right-2 text-gray-500 pointer-events-none">
                    <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                </div>
            </div>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute top-full mt-2 left-0 w-full max-h-60 overflow-y-auto bg-black/80 backdrop-blur-2xl border border-white/10 rounded-xl shadow-2xl z-50 animate-in fade-in zoom-in-95 duration-200 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
                    <div className="py-1">
                        {/* Option: Clear / All */}
                        <div
                            className="px-4 py-2 text-sm text-gray-400 hover:bg-white/10 cursor-pointer flex items-center justify-between"
                            onClick={() => {
                                onChange("");
                                setIsOpen(false);
                            }}
                        >
                            <span className="italic opacity-80">{placeholder}</span>
                            {value === "" && <Check size={14} className="text-blue-400" />}
                        </div>

                        {filteredOptions.length > 0 ? (
                            filteredOptions.map((opt) => (
                                <div
                                    key={opt}
                                    className={`px-4 py-2 text-sm cursor-pointer flex items-center justify-between transition-colors
                                        ${value === opt ? 'bg-blue-900/30 text-blue-300' : 'text-gray-200 hover:bg-gray-800'}
                                    `}
                                    onClick={() => {
                                        onChange(opt);
                                        setIsOpen(false);
                                    }}
                                >
                                    {opt}
                                    {value === opt && <Check size={14} className="text-blue-400" />}
                                </div>
                            ))
                        ) : (
                            <div className="px-4 py-3 text-sm text-gray-500 text-center">
                                No matches found
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
