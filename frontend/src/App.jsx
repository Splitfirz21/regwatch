import { useState, useEffect } from 'react';
import axios from 'axios';
import NewsCard from './components/NewsCard';
import SearchableDropdown from './components/SearchableDropdown';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import { RefreshCw, Search as SearchIcon, X, LayoutGrid, Filter, Download, BarChart2, List, Loader, Sparkles } from 'lucide-react';

import { SECTORS, AGENCIES } from './constants';

const API_Base = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8005`;

function App() {
  const [viewMode, setViewMode] = useState('news');
  const [news, setNews] = useState([]);
  const [originalNews, setOriginalNews] = useState([]); // Backup for clearing search
  const [selectedSector, setSelectedSector] = useState("");
  const [selectedAgency, setSelectedAgency] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [trigger, setTrigger] = useState(0);

  // Initial Fetch & Reactive Updates
  useEffect(() => {
    if (!isSearchActive) {
      fetchNews();
    }
  }, [selectedSector, selectedAgency, trigger]);

  // Auto-Refresh
  useEffect(() => {
    const interval = setInterval(() => {
      console.log("Hourly auto-refresh...");
      if (!isSearchActive) fetchNews();
    }, 60 * 60 * 1000);
    return () => clearInterval(interval);
  }, [isSearchActive]);

  const fetchNews = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedSector) params.sector = selectedSector;
      if (selectedAgency) params.agency = selectedAgency;

      const res = await axios.get(`${API_Base}/news`, { params });
      let data = res.data;
      if (Array.isArray(data)) {
        if (selectedAgency) {
          data = data.filter(item => item.agency === selectedAgency);
        }
        setNews(data);
        setOriginalNews(data); // Sync backup
      } else {
        setNews([]);
      }
    } catch (err) {
      console.error("Failed to fetch news", err);
    } finally {
      setLoading(false);
    }
  };

  // Watch for empty search query to auto-restore
  useEffect(() => {
    if ((!searchQuery || searchQuery.trim() === "") && isSearchActive) {
      restoreFeed();
    }
  }, [searchQuery, isSearchActive]);

  const handleSmartSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    setIsSearchActive(true);
    setNews([]); // Clear current view to show loading state effectively

    try {
      const res = await axios.post(`${API_Base}/search`, { query: searchQuery });
      const data = res.data; // { summary, items }

      if (data.items && Array.isArray(data.items)) {
        setNews(data.items);
      } else {
        setNews([]);
      }
    } catch (err) {
      console.error("Search failed", err);
      // Revert? Or show error?
    } finally {
      setSearchLoading(false);
    }
  };

  const restoreFeed = () => {
    setIsSearchActive(false);
    setSearchQuery(""); // Ensure query is cleared in state
    setNews(originalNews.length > 0 ? originalNews : []); // Immediate visual reset
    fetchNews(); // Refresh in background
  };

  const clearSearch = () => {
    setSearchQuery("");
    restoreFeed();
  };

  const handleFeedback = async (id, liked) => {
    try {
      await axios.post(`${API_Base}/feedback`, {
        news_item_id: id,
        liked: liked
      });
      if (liked === false) {
        setNews(prev => prev.filter(item => item.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleScan = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_Base}/scan`);
      setTimeout(() => setTrigger(t => t + 1), 1000);
    } catch (err) {
      console.error("Scan failed", err);
      setLoading(false);
    }
  };

  const handleRemove = async (id) => {
    setNews(current => current.filter(item => item.id !== id));
    try {
      await axios.delete(`${API_Base}/items/${id}`);
      await axios.post(`${API_Base}/feedback`, {
        news_item_id: id,
        liked: false
      });
    } catch (err) {
      console.error("Remove feedback failed", err);
    }
  };

  const handleAddToDashboard = async (item) => {
    try {
      // Optimistic update
      setNews(prev => prev.map(n => n.url === item.url ? { ...n, isAdded: true } : n));

      const res = await axios.post(`${API_Base}/items`, item);
      const savedItem = res.data;

      // Update with real ID and consistent state
      setNews(prev => prev.map(n =>
        n.url === item.url ? { ...savedItem, isAdded: true } : n
      ));

      // If we are "adding to dashboard", we might want to ensure it appears in 'originalNews' too?
      // But originalNews is the backup of the main feed. If we add it, it belongs there now.
      setOriginalNews(prev => {
        // Avoid duplicates in backup
        if (prev.find(n => n.url === item.url)) return prev;
        return [savedItem, ...prev];
      });

    } catch (err) {
      console.error("Failed to add item", err);
      alert("Failed to add to dashboard.");
      // Revert optimistic
      setNews(prev => prev.map(n => n.url === item.url ? { ...n, isAdded: false } : n));
    }
  };

  const handleUpdateItem = (id, updatedFields) => {
    setNews(prev => prev.map(item =>
      item.id === id ? { ...item, ...updatedFields } : item
    ));
  };

  // Local Filter logic (Only applies if NOT in Smart Search mode, or applies on top?)
  const displayNews = isSearchActive ? news : news.filter(item => {
    // Standard Filtering
    if (selectedSector && item.sector !== selectedSector) return false;
    if (selectedAgency && item.agency && !item.agency.includes(selectedAgency)) return false;
    return true;
  });

  const handleViewChange = (mode) => {
    setViewMode(mode);
    if (isSearchActive || searchQuery) {
      clearSearch();
    }
  };

  return (
    <div className="bg-transparent min-h-screen font-sans text-gray-100 flex flex-col">
      {/* Top Navigation Bar */}
      <nav className="sticky top-0 z-[100] bg-black/10 backdrop-blur-md border-b border-white/5 px-4 md:px-6 py-4 flex flex-col xl:flex-row flex-wrap gap-4 items-center justify-between w-full shadow-2xl pointer-events-auto transition-all">
        <div className="flex flex-col md:flex-row items-center gap-4 md:gap-6 flex-1 w-full md:w-auto">
          <div className="flex items-center justify-between w-full md:w-auto">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-400 bg-clip-text text-transparent mr-4 tracking-tight drop-shadow-sm flex items-center gap-2 cursor-pointer whitespace-nowrap" onClick={() => handleViewChange('news')}>
              RegWatch SG
            </h1>

            {/* Mobile Toggles */}
            <div className="flex md:hidden bg-white/5 rounded-lg p-1 border border-white/10">
              <button onClick={() => handleViewChange('news')} className={`p-1.5 rounded-md ${viewMode === 'news' ? 'bg-gray-700 text-white' : 'text-gray-400'}`}><List size={16} /></button>
              <button onClick={() => handleViewChange('analytics')} className={`p-1.5 rounded-md ${viewMode === 'analytics' ? 'bg-indigo-600 text-white' : 'text-gray-400'}`}><BarChart2 size={16} /></button>
            </div>
          </div>

          <div className="hidden md:flex bg-white/5 rounded-lg p-1 border border-white/10">
            <button onClick={() => handleViewChange('news')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'news' ? 'bg-gray-700 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}><List size={16} /> News</button>
            <button onClick={() => handleViewChange('analytics')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${viewMode === 'analytics' ? 'bg-indigo-600 text-white shadow-md' : 'text-gray-400 hover:text-white'}`}><BarChart2 size={16} /> Analytics</button>
          </div>

          {(viewMode === 'news') && (
            <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto">
              <div className="w-full md:w-[240px]"><SearchableDropdown options={SECTORS} value={selectedSector} onChange={setSelectedSector} placeholder="All Sectors" prefixIcon={<LayoutGrid size={16} />} /></div>
              <div className="w-full md:w-[240px]"><SearchableDropdown options={AGENCIES} value={selectedAgency} onChange={setSelectedAgency} placeholder="All Agencies" prefixIcon={<Filter size={16} />} /></div>
            </div>
          )}
        </div>

        <div className="flex flex-row items-center gap-2 md:gap-3 w-full xl:w-auto justify-between md:justify-end flex-1">
          {/* INLINE SMART SEARCH */}
          <form onSubmit={handleSmartSearch} className="relative flex-1 md:flex-none md:w-96 group">
            <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
              {searchLoading ? <Loader size={16} className="text-blue-400 animate-spin" /> : <SearchIcon size={16} className="text-gray-400 group-focus-within:text-blue-400 transition-colors" />}
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Don't see the news you need? Search here"
              className="w-full bg-white/5 border border-white/10 text-gray-200 text-sm rounded-xl pl-10 pr-10 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all placeholder:text-gray-500"
            />
            {searchQuery && (
              <button type="button" onClick={clearSearch} className="absolute inset-y-0 right-3 flex items-center text-gray-400 hover:text-white">
                <X size={14} />
              </button>
            )}
          </form>

          <button onClick={async () => {
            try {
              setLoading(true);
              const response = await axios.get(`${API_Base}/export`, { responseType: 'blob' });
              const url = window.URL.createObjectURL(new Blob([response.data]));
              const link = document.createElement('a');
              link.href = url;
              const contentDisposition = response.headers['content-disposition'];
              let fileName = 'regwatch_export.xlsx';
              if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^"]+)"?/);
                if (match && match[1]) fileName = match[1];
              }
              link.setAttribute('download', fileName);
              document.body.appendChild(link);
              link.click();
              link.remove();
            } catch (err) { console.error("Export failed", err); alert("Failed to export."); } finally { setLoading(false); }
          }} className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-gray-300 px-3 md:px-4 py-2 rounded-xl border border-white/10 font-medium text-sm transition-all shadow-sm whitespace-nowrap">
            <Download size={16} /> <span className="hidden md:inline">Export</span>
          </button>

          <button onClick={handleScan} disabled={loading} className="flex items-center gap-2 bg-blue-600/80 hover:bg-blue-500/80 text-white px-3 md:px-4 py-2 rounded-xl font-medium text-sm transition-all disabled:opacity-50 backdrop-blur-md shadow-lg shadow-blue-500/20 whitespace-nowrap">
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            <span className="hidden md:inline">{loading ? "Scanning..." : "Scan"}</span>
            <span className="md:hidden">Scan</span>
          </button>
        </div>
      </nav>

      <main className="flex-1 px-6 py-8 w-full">
        {viewMode === 'analytics' ? (
          <AnalyticsDashboard />
        ) : (
          <>
            <header className="mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h2 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                {isSearchActive ? (
                  <>
                    <Sparkles className="text-amber-300" />
                    Search Results: "{searchQuery}"
                  </>
                ) : (
                  selectedSector ? selectedSector : "Latest Regulatory News"
                )}
              </h2>
              <p className="text-gray-400">
                {searchLoading ? "AI Scout is searching historical archives..." :
                  loading ? "Scanning sources..." :
                    isSearchActive && displayNews.length === 0 ? "No results found." :
                      `${displayNews.length} updates found`}
              </p>
            </header>

            {displayNews.length === 0 && !loading && !searchLoading ? (
              <div className="flex flex-col items-center justify-center py-20 text-gray-500 animate-in fade-in zoom-in duration-300">
                <SearchIcon size={48} className="mb-4 opacity-20" />
                <p>No news found.</p>
                {!isSearchActive && <button onClick={handleScan} className="text-blue-400 hover:underline mt-2">Trigger a scan</button>}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6 pb-10">
                {displayNews.map(item => (
                  <NewsCard
                    key={item.id || item.url}
                    item={item}
                    onFeedback={handleFeedback}
                    onRemove={handleRemove}
                    onUpdate={handleUpdateItem}
                    onAdd={isSearchActive ? handleAddToDashboard : null}
                    isSaved={item.isSaved}
                  />
                ))}
              </div>
            )}

            {searchLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm z-50">
                <div className="bg-gray-900 border border-white/10 p-6 rounded-2xl flex flex-col items-center shadow-2xl">
                  <Loader size={40} className="text-blue-400 animate-spin mb-4" />
                  <h3 className="text-white font-bold text-lg mb-1">Searching Archives</h3>
                  <p className="text-gray-400 text-sm">Hunting for "{searchQuery}"...</p>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
