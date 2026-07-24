import { Link, useLocation } from "react-router-dom";
import { MagnifyingGlass, List, X, CaretDown, Moon, Sun } from "@phosphor-icons/react";
import { useState, useEffect, useRef } from "react";
import { autosuggest } from "@/api";

const LEAGUES = [
  { slug: 'bundesliga', name: 'Bundesliga', country: '🇩🇪' },
  { slug: 'premier-league', name: 'Premier League', country: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
  { slug: 'la-liga', name: 'La Liga', country: '🇪🇸' },
  { slug: 'serie-a', name: 'Serie A', country: '🇮🇹' },
  { slug: 'ligue-1', name: 'Ligue 1', country: '🇫🇷' },
];

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [leagueDropdownOpen, setLeagueDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('darkMode') === 'true';
    }
    return false;
  });
  const searchRef = useRef(null);
  const leagueRef = useRef(null);
  const location = useLocation();

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('darkMode', 'true');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('darkMode', 'false');
    }
  }, [darkMode]);

  useEffect(() => { 
    setMenuOpen(false); 
    setLeagueDropdownOpen(false);
  }, [location]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
      if (leagueRef.current && !leagueRef.current.contains(e.target)) {
        setLeagueDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (searchQuery.length >= 2) {
        try {
          const res = await autosuggest(searchQuery, 8);
          setSuggestions(res.data);
          setShowSuggestions(true);
        } catch (e) { console.error(e); }
      } else {
        setSuggestions([]);
        setShowSuggestions(false);
      }
    };
    const debounce = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = "/suche?q=" + encodeURIComponent(searchQuery);
    }
  };

  const navItems = [
    { path: "/", label: "Startseite" },
    { path: "/ticker", label: "News-Ticker" },
    { path: "/geruechte", label: "Gerüchte" },
    { path: "/top-deals", label: "Top-Transfers" },
    { path: "/abloesefrei", label: "Ablösefrei" },
    { path: "/deadline-day", label: "Deadline Day" },
  ];
  
  const isActive = (path) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  return (
    <header data-testid="main-header">
      {/* Top Banner Ad - über Header */}
      <div className="py-2 bg-[#f2f2f2]" data-testid="top-banner-container">
        <div className="flex justify-center">
          <div 
            className="bg-gray-300 border border-gray-400 flex items-center justify-center"
            style={{ width: '728px', height: '90px' }}
            data-testid="top-banner-ad"
          >
            <span className="text-[11px] text-gray-500 uppercase tracking-wider">Anzeige</span>
          </div>
        </div>
      </div>
      
      {/* Top Bar - Green */}
      <div className="bg-[#79B92A]">
        <div className="flex items-center justify-between h-[44px] px-3">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
            <div className="bg-white rounded px-2 py-1">
              <span className="text-[#79B92A] font-bold text-sm">transfer</span>
              <span className="text-gray-800 font-bold text-sm">news</span>
            </div>
          </Link>
          
          {/* Search Bar - Desktop */}
          <div className="hidden md:flex flex-1 max-w-[400px] mx-4" ref={searchRef}>
            <form onSubmit={handleSearch} className="w-full relative">
              <input
                type="text"
                placeholder="Spieler, Verein, Wettbewerb..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-[30px] px-3 pr-8 text-[12px] border-0 rounded-sm focus:outline-none focus:ring-2 focus:ring-[#00a83f]"
                data-testid="search-input"
              />
              <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-[#1d4370]">
                <MagnifyingGlass size={16} />
              </button>
              
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 shadow-lg mt-1 z-50">
                  {suggestions.map((item, idx) => (
                    <Link
                      key={idx}
                      to={item.type === "player" ? "/spieler/" + item.slug : "/verein/" + item.slug}
                      className="flex items-center gap-2 px-3 py-2 hover:bg-[#e8f4e8] text-[12px] border-b border-gray-100 last:border-0"
                      onClick={() => setShowSuggestions(false)}
                    >
                      <span className="font-medium text-gray-900">{item.name}</span>
                      <span className="text-[10px] text-gray-500 bg-gray-100 px-1 rounded">
                        {item.type === "player" ? "Spieler" : "Verein"}
                      </span>
                    </Link>
                  ))}
                </div>
              )}
            </form>
          </div>
          
          {/* Right Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="w-8 h-8 flex items-center justify-center text-white/80 hover:text-white transition-colors"
              data-testid="dark-mode-toggle"
            >
              {darkMode ? <Sun size={18} weight="fill" className="text-yellow-300" /> : <Moon size={18} />}
            </button>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden w-8 h-8 flex items-center justify-center text-white"
              data-testid="burger-menu-button"
            >
              <List size={22} />
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Bar */}
      <nav className="bg-[#5a8a1f] border-b border-[#4a7a15]" data-testid="sports-nav">
        <div className="flex items-center h-[32px] px-3 overflow-x-auto hide-scrollbar">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex-shrink-0 h-full flex items-center px-3 text-[11px] font-semibold transition-colors border-b-2 ${
                isActive(item.path) 
                  ? "text-white border-white bg-[#4a7a15]" 
                  : "text-white/90 border-transparent hover:bg-[#4a7a15]/50"
              }`}
            >
              {item.label}
            </Link>
          ))}
          
          {/* Liga-Dropdown */}
          <div className="relative h-full" ref={leagueRef}>
            <button 
              onClick={() => setLeagueDropdownOpen(!leagueDropdownOpen)}
              className={`flex-shrink-0 h-full flex items-center gap-1 px-3 text-[11px] font-semibold transition-colors border-b-2 ${
                location.pathname.includes('/wettbewerb/') 
                  ? "text-white border-white bg-[#4a7a15]" 
                  : "text-white/90 border-transparent hover:bg-[#4a7a15]/50"
              }`}
              data-testid="league-dropdown-btn"
            >
              Wettbewerbe
              <CaretDown size={10} className={`transition-transform ${leagueDropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {leagueDropdownOpen && (
              <div className="absolute top-full left-0 w-48 bg-white shadow-lg border border-gray-200 z-50">
                {LEAGUES.map((league) => (
                  <Link
                    key={league.slug}
                    to={`/wettbewerb/${league.slug}`}
                    onClick={() => setLeagueDropdownOpen(false)}
                    className="flex items-center gap-2 px-3 py-2 hover:bg-[#e8f4e8] text-[12px] border-b border-gray-100 last:border-0"
                  >
                    <span>{league.country}</span>
                    <span className="font-medium text-gray-900">{league.name}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
          
          <Link
            to="/redaktion"
            className="flex-shrink-0 h-full flex items-center px-3 text-[11px] font-semibold text-white/90 border-b-2 border-transparent hover:bg-[#4a7a15]/50"
          >
            Redaktion
          </Link>
        </div>
      </nav>

      {/* Mobile Menu */}
      {menuOpen && (
        <>
          <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setMenuOpen(false)} />
          <div className="fixed top-0 right-0 w-[280px] h-full bg-white z-50 shadow-2xl overflow-y-auto">
            <div className="flex items-center justify-between h-[44px] px-3 bg-[#79B92A]">
              <span className="font-bold text-white text-sm">Menü</span>
              <button onClick={() => setMenuOpen(false)} className="w-8 h-8 flex items-center justify-center text-white">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-3 bg-gray-50 border-b">
              <form onSubmit={handleSearch}>
                <input
                  type="text"
                  placeholder="Suchen..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full h-[36px] px-3 text-[13px] border border-gray-300 rounded focus:outline-none focus:border-[#00a83f]"
                />
              </form>
            </div>
            
            <nav className="py-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center h-10 px-4 text-[13px] font-medium border-l-[3px] ${
                    isActive(item.path) 
                      ? "text-[#79B92A] bg-[#e8f4e8] border-l-[#79B92A]" 
                      : "text-gray-700 border-l-transparent hover:bg-gray-50"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
              
              <div className="border-t border-gray-200 mt-2 pt-2">
                <div className="px-4 py-2 text-[10px] text-gray-500 uppercase font-bold">Wettbewerbe</div>
                {LEAGUES.map((league) => (
                  <Link
                    key={league.slug}
                    to={`/wettbewerb/${league.slug}`}
                    onClick={() => setMenuOpen(false)}
                    className="flex items-center gap-2 h-10 px-4 text-[13px] text-gray-700 hover:bg-gray-50"
                  >
                    <span>{league.country}</span>
                    <span>{league.name}</span>
                  </Link>
                ))}
              </div>
            </nav>
          </div>
        </>
      )}
      
      {/* Billboard Ad - unter dem Menü */}
      <div className="bg-[#d9d9d9] py-2" data-testid="billboard-container">
        <div className="flex justify-center">
          <div 
            className="bg-gray-300 border border-gray-400 flex items-center justify-center"
            style={{ width: '970px', height: '250px' }}
            data-testid="billboard-ad"
          >
            <span className="text-[11px] text-gray-500 uppercase tracking-wider">Anzeige</span>
          </div>
        </div>
      </div>
    </header>
  );
}
