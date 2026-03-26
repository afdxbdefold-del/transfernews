import { Link } from "react-router-dom";
import { MagnifyingGlass, List, X, User } from "@phosphor-icons/react";
import { useState, useEffect, useRef } from "react";
import { autosuggest } from "@/api";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
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

  return (
    <header className="bg-[#053f2c] text-white border-b-4 border-[#00a651] sticky top-0 z-50" data-testid="main-header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2" data-testid="logo-link">
            <span className="text-2xl font-bold font-['Oswald'] uppercase tracking-tight">
              Transfer<span className="text-[#00c853]">News</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center space-x-1">
            <Link to="/news" className="px-3 py-2 text-sm font-medium hover:bg-white/10 transition-colors" data-testid="nav-news">
              NEWS
            </Link>
            <Link to="/geruechte" className="px-3 py-2 text-sm font-medium hover:bg-white/10 transition-colors" data-testid="nav-geruechte">
              GERÜCHTE
            </Link>
            <Link to="/transfers" className="px-3 py-2 text-sm font-medium hover:bg-white/10 transition-colors" data-testid="nav-transfers">
              TRANSFERS
            </Link>
          </nav>

          {/* Search */}
          <div className="hidden md:block relative" ref={searchRef}>
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                placeholder="Spieler, Verein..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64 bg-white/10 border border-white/20 rounded px-4 py-2 text-sm placeholder-white/50 focus:outline-none focus:border-[#00c853]"
                data-testid="search-input"
              />
              <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2" data-testid="search-button">
                <MagnifyingGlass size={18} className="text-white/70" />
              </button>
            </form>
            
            {/* Autosuggest Dropdown */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white text-gray-900 rounded shadow-lg border border-gray-200 z-50" data-testid="search-suggestions">
                {suggestions.map((item, idx) => (
                  <Link
                    key={idx}
                    to={item.type === "player" ? `/spieler/${item.slug}` : `/verein/${item.slug}`}
                    className="block px-4 py-2 hover:bg-gray-100 text-sm"
                    onClick={() => setShowSuggestions(false)}
                  >
                    <span className="text-xs uppercase text-gray-500 mr-2">
                      {item.type === "player" ? "Spieler" : "Verein"}
                    </span>
                    {item.name}
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Admin Link */}
          <Link to="/admin" className="hidden md:flex items-center px-3 py-2 text-sm hover:bg-white/10 transition-colors" data-testid="nav-admin">
            <User size={18} className="mr-1" />
            Admin
          </Link>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2"
            data-testid="mobile-menu-button"
          >
            {menuOpen ? <X size={24} /> : <List size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {menuOpen && (
          <div className="md:hidden py-4 border-t border-white/10" data-testid="mobile-menu">
            <form onSubmit={handleSearch} className="mb-4">
              <input
                type="text"
                placeholder="Suche..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded px-4 py-2 text-sm placeholder-white/50"
              />
            </form>
            <nav className="flex flex-col space-y-1">
              <Link to="/news" className="px-3 py-2 hover:bg-white/10">NEWS</Link>
              <Link to="/geruechte" className="px-3 py-2 hover:bg-white/10">GERÜCHTE</Link>
              <Link to="/transfers" className="px-3 py-2 hover:bg-white/10">TRANSFERS</Link>
              <Link to="/admin" className="px-3 py-2 hover:bg-white/10">ADMIN</Link>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
