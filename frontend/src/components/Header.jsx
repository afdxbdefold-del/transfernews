import { Link, useLocation } from "react-router-dom";
import { MagnifyingGlass, List, X, CaretDown, Trophy, Moon, Sun } from "@phosphor-icons/react";
import { useState, useEffect, useRef } from "react";
import { autosuggest } from "@/api";

// Liga-Konfiguration mit Logos
const LEAGUES = [
  { slug: 'bundesliga', name: 'Bundesliga', country: '🇩🇪', color: 'bg-red-600' },
  { slug: 'premier-league', name: 'Premier League', country: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', color: 'bg-purple-700' },
  { slug: 'la-liga', name: 'La Liga', country: '🇪🇸', color: 'bg-orange-500' },
  { slug: 'serie-a', name: 'Serie A', country: '🇮🇹', color: 'bg-blue-600' },
  { slug: 'ligue-1', name: 'Ligue 1', country: '🇫🇷', color: 'bg-blue-800' },
];

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [leagueDropdownOpen, setLeagueDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('darkMode') === 'true';
    }
    return false;
  });
  const searchRef = useRef(null);
  const leagueRef = useRef(null);
  const location = useLocation();

  // Dark Mode Effect
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
        setSearchOpen(false);
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
    { path: "/", label: "TRANSFERS" },
    { path: "/geruechte", label: "GERÜCHTE" },
  ];
  
  const isActive = (path) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };
  
  const isLeagueActive = () => {
    return location.pathname.includes('/wettbewerb/') || location.pathname.includes('/liga/');
  };

  return (
    <header className="sticky top-0 z-50" data-testid="main-header">
      {/* Top Bar - White with Logo */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800">
        <div className="max-w-[1280px] mx-auto px-4">
          <div className="flex items-center justify-between h-[50px]">
            {/* Logo Left */}
            <Link to="/" className="flex items-center" data-testid="logo-link">
              <img src="/logo.svg" alt="TransferNews" className="h-5 dark:invert" />
            </Link>
            
            {/* Right Icons */}
            <div className="flex items-center gap-1">
              {/* Dark Mode Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="w-10 h-10 flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-full transition-colors"
                data-testid="dark-mode-toggle"
                title={darkMode ? "Light Mode" : "Dark Mode"}
              >
                {darkMode ? <Sun size={22} weight="fill" className="text-yellow-400" /> : <Moon size={22} />}
              </button>
              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="w-10 h-10 flex items-center justify-center text-gray-600 dark:text-gray-300"
                data-testid="search-button"
              >
                <MagnifyingGlass size={22} />
              </button>
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="w-10 h-10 flex items-center justify-center text-gray-600 dark:text-gray-300"
                data-testid="burger-menu-button"
              >
                <List size={24} />
              </button>
            </div>
          </div>
        </div>
        
        {/* Search Dropdown */}
        {searchOpen && (
          <div className="border-t border-gray-100 px-4 py-3" ref={searchRef}>
            <form onSubmit={handleSearch}>
              <input
                type="text"
                placeholder="Spieler, Verein suchen..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:border-[#79B92A]"
                autoFocus
                data-testid="search-input"
              />
            </form>
            {showSuggestions && suggestions.length > 0 && (
              <div className="mt-2 bg-white border border-gray-200">
                {suggestions.map((item, idx) => (
                  <Link
                    key={idx}
                    to={item.type === "player" ? "/spieler/" + item.slug : "/verein/" + item.slug}
                    className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-0"
                    onClick={() => { setShowSuggestions(false); setSearchOpen(false); }}
                  >
                    <span className="text-sm font-medium">{item.name}</span>
                    <span className="text-xs text-gray-400">{item.type === "player" ? "Spieler" : "Verein"}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation Bar - BLACK */}
      <nav className="bg-black" data-testid="sports-nav">
        <div className="max-w-[1280px] mx-auto px-4">
          <div className="flex items-center justify-between h-[40px]">
            <div className="flex items-center h-full overflow-x-auto hide-scrollbar">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={"flex-shrink-0 h-full flex items-center px-3 text-[12px] font-bold uppercase tracking-wide transition-colors " + (isActive(item.path) ? "text-[#79B92A]" : "text-white")}
                  style={{ fontFamily: "'Oswald', sans-serif" }}
                >
                  {item.label}
                </Link>
              ))}
              
              {/* Liga-Dropdown */}
              <div className="relative h-full" ref={leagueRef}>
                <button 
                  onClick={() => setLeagueDropdownOpen(!leagueDropdownOpen)}
                  className={"flex-shrink-0 h-full flex items-center gap-1 px-3 text-[12px] font-bold uppercase tracking-wide transition-colors " + (isLeagueActive() ? "text-[#79B92A]" : "text-white")}
                  style={{ fontFamily: "'Oswald', sans-serif" }}
                  data-testid="league-dropdown-btn"
                >
                  <Trophy size={14} weight="fill" />
                  LIGEN
                  <CaretDown size={12} className={`transition-transform ${leagueDropdownOpen ? 'rotate-180' : ''}`} />
                </button>
                
                {/* Dropdown Menu - Rendered outside the nav flow */}
                {leagueDropdownOpen && (
                  <div 
                    className="fixed w-56 bg-white shadow-xl rounded-lg overflow-hidden border border-gray-100"
                    style={{ 
                      top: '90px',
                      left: leagueRef.current?.getBoundingClientRect().left + 'px',
                      zIndex: 9999
                    }}
                    data-testid="league-dropdown"
                  >
                    <div className="p-2">
                      <span className="text-[10px] text-gray-400 uppercase font-bold px-2">Wettbewerbe</span>
                    </div>
                    {LEAGUES.map((league) => (
                      <Link
                        key={league.slug}
                        to={`/wettbewerb/${league.slug}`}
                        onClick={() => setLeagueDropdownOpen(false)}
                        className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                        data-testid={`league-${league.slug}`}
                      >
                        <span className="text-lg">{league.country}</span>
                        <div className="flex-1">
                          <span className="text-sm font-bold text-gray-900">{league.name}</span>
                        </div>
                        <div className={`w-2 h-2 rounded-full ${league.color}`}></div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <button className="text-white hidden">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Burger Menu */}
      {menuOpen && (
        <>
          <div className="fixed inset-0 bg-black/50 z-40" onClick={() => setMenuOpen(false)} />
          <div className="fixed top-0 right-0 w-[280px] h-full bg-white z-50 shadow-2xl overflow-y-auto" data-testid="burger-menu">
            <div className="flex items-center justify-between h-[50px] px-4 border-b border-gray-100">
              <span className="font-bold">Menu</span>
              <button onClick={() => setMenuOpen(false)} className="w-10 h-10 flex items-center justify-center">
                <X size={24} />
              </button>
            </div>
            <nav className="py-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMenuOpen(false)}
                  className={"flex items-center h-12 px-4 text-[14px] font-bold uppercase " + (isActive(item.path) ? "text-[#79B92A]" : "text-gray-900")}
                  style={{ fontFamily: "'Oswald', sans-serif" }}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </>
      )}
    </header>
  );
}
