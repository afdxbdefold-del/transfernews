import { Link, useLocation } from "react-router-dom";
import { MagnifyingGlass, List, X, User, House, Newspaper, Trophy, ArrowsLeftRight, ChatDots } from "@phosphor-icons/react";
import { useState, useEffect, useRef } from "react";
import { autosuggest } from "@/api";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const searchRef = useRef(null);
  const location = useLocation();

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
        setSearchOpen(false);
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
        } catch (e) {
          console.error(e);
        }
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
      window.location.href = `/suche?q=${encodeURIComponent(searchQuery)}`;
    }
  };

  const navItems = [
    { path: "/", label: "TRANSFERS", icon: ArrowsLeftRight },
    { path: "/news", label: "NEWS", icon: Newspaper },
    { path: "/geruechte", label: "GERÜCHTE", icon: ChatDots },
    { path: "/wettbewerb/bundesliga", label: "BUNDESLIGA", icon: Trophy },
    { path: "/wettbewerb/premier-league", label: "PREMIER LEAGUE", icon: Trophy },
    { path: "/wettbewerb/la-liga", label: "LA LIGA", icon: Trophy },
  ];

  const isActive = (path) => {
    if (path === "/") return location.pathname === "/";
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-50" data-testid="main-header">
      {/* Top Bar - White with Logo */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1200px] mx-auto px-3">
          <div className="flex items-center justify-between h-14">
            {/* Left: Burger Menu + Logo */}
            <div className="flex items-center gap-3">
              {/* Burger Menu Button */}
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="p-2 hover:bg-gray-100 rounded transition-colors"
                data-testid="burger-menu-button"
              >
                {menuOpen ? <X size={24} weight="bold" /> : <List size={24} weight="bold" />}
              </button>

              {/* Logo */}
              <Link to="/" className="flex items-center" data-testid="logo-link">
                <span className="text-2xl font-black tracking-tight uppercase" style={{ fontFamily: "'Oswald', sans-serif" }}>
                  <span className="text-gray-900">TRANSFER</span>
                  <span className="text-[#79B92A]">NEWS</span>
                </span>
              </Link>
            </div>

            {/* Center: Quick Nav Icons (Desktop) */}
            <div className="hidden lg:flex items-center gap-6">
              <Link to="/news" className="flex flex-col items-center text-gray-600 hover:text-[#79B92A] transition-colors">
                <Newspaper size={20} />
                <span className="text-[10px] font-bold mt-0.5">Newsticker</span>
              </Link>
              <Link to="/transfers" className="flex flex-col items-center text-gray-600 hover:text-[#79B92A] transition-colors">
                <ArrowsLeftRight size={20} />
                <span className="text-[10px] font-bold mt-0.5">Transfers</span>
              </Link>
              <Link to="/geruechte" className="flex flex-col items-center text-gray-600 hover:text-[#79B92A] transition-colors">
                <ChatDots size={20} />
                <span className="text-[10px] font-bold mt-0.5">Gerüchte</span>
              </Link>
            </div>

            {/* Right: Search + Admin */}
            <div className="flex items-center gap-2">
              {/* Search (Desktop) */}
              <div className="hidden md:block relative" ref={searchRef}>
                <form onSubmit={handleSearch} className="relative">
                  <input
                    type="text"
                    placeholder="Spieler, Verein suchen..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-56 bg-gray-100 border-0 rounded-none px-4 py-2 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#79B92A]"
                    data-testid="search-input"
                  />
                  <button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2" data-testid="search-button">
                    <MagnifyingGlass size={18} className="text-gray-500" />
                  </button>
                </form>
                
                {/* Autosuggest Dropdown */}
                {showSuggestions && suggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white text-gray-900 shadow-lg border border-gray-200 z-50" data-testid="search-suggestions">
                    {suggestions.map((item, idx) => (
                      <Link
                        key={idx}
                        to={item.type === "player" ? `/spieler/${item.slug}` : `/verein/${item.slug}`}
                        className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-0"
                        onClick={() => setShowSuggestions(false)}
                      >
                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                          <span className="text-xs font-bold text-gray-500">
                            {item.type === "player" ? "S" : "V"}
                          </span>
                        </div>
                        <div>
                          <span className="text-sm font-medium block">{item.name}</span>
                          <span className="text-xs text-gray-500 uppercase">
                            {item.type === "player" ? "Spieler" : "Verein"}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>

              {/* Search Icon (Mobile) */}
              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="md:hidden p-2 hover:bg-gray-100 rounded transition-colors"
                data-testid="mobile-search-button"
              >
                <MagnifyingGlass size={22} />
              </button>

              {/* Admin Link */}
              <Link 
                to="/admin" 
                className="hidden sm:flex items-center gap-1 px-3 py-2 text-sm font-bold text-gray-700 hover:text-[#79B92A] transition-colors"
                data-testid="nav-admin"
              >
                <User size={18} weight="bold" />
                <span className="hidden lg:inline">Admin</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Sports Navigation Bar - Green */}
      <nav className="bg-[#79B92A]" data-testid="sports-nav">
        <div className="max-w-[1200px] mx-auto px-3">
          <div className="flex items-center h-11 overflow-x-auto hide-scrollbar">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex-shrink-0 px-4 h-full flex items-center text-sm font-black uppercase tracking-wide transition-colors ${
                  isActive(item.path)
                    ? "bg-[#5a8a1f] text-white"
                    : "text-white hover:bg-[#6aa325]"
                }`}
                style={{ fontFamily: "'Oswald', sans-serif" }}
                data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
              >
                {item.label}
              </Link>
            ))}
            
            {/* More Button */}
            <button 
              className="flex-shrink-0 px-4 h-full flex items-center text-sm font-black uppercase tracking-wide text-white hover:bg-[#6aa325] transition-colors"
              style={{ fontFamily: "'Oswald', sans-serif" }}
            >
              MEHR
              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Search Bar */}
      {searchOpen && (
        <div className="md:hidden bg-white border-b border-gray-200 p-3" data-testid="mobile-search-bar">
          <form onSubmit={handleSearch} className="relative">
            <input
              type="text"
              placeholder="Spieler, Verein suchen..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-100 border-0 rounded-none px-4 py-3 text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#79B92A]"
              autoFocus
            />
            <button type="submit" className="absolute right-3 top-1/2 -translate-y-1/2">
              <MagnifyingGlass size={20} className="text-gray-500" />
            </button>
          </form>
        </div>
      )}

      {/* Burger Menu Overlay */}
      {menuOpen && (
        <>
          <div 
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setMenuOpen(false)}
          />
          <div 
            className="fixed top-0 left-0 w-[320px] h-full bg-white z-50 shadow-xl overflow-y-auto"
            data-testid="burger-menu"
          >
            {/* Menu Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <Link to="/" onClick={() => setMenuOpen(false)}>
                <span className="text-xl font-black tracking-tight uppercase" style={{ fontFamily: "'Oswald', sans-serif" }}>
                  <span className="text-gray-900">TRANSFER</span>
                  <span className="text-[#79B92A]">NEWS</span>
                </span>
              </Link>
              <button onClick={() => setMenuOpen(false)} className="p-2">
                <X size={24} weight="bold" />
              </button>
            </div>

            {/* Menu Items */}
            <nav className="p-2">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 font-bold uppercase transition-colors ${
                    isActive(item.path)
                      ? "bg-[#79B92A] text-white"
                      : "text-gray-800 hover:bg-gray-100"
                  }`}
                  style={{ fontFamily: "'Oswald', sans-serif" }}
                >
                  <item.icon size={20} />
                  {item.label}
                </Link>
              ))}
              
              <div className="border-t border-gray-200 my-4" />
              
              <Link
                to="/admin"
                onClick={() => setMenuOpen(false)}
                className="flex items-center gap-3 px-4 py-3 font-bold text-gray-600 hover:bg-gray-100 transition-colors"
              >
                <User size={20} />
                Admin-Bereich
              </Link>
            </nav>
          </div>
        </>
      )}
    </header>
  );
}
