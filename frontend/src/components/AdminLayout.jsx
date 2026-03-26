import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  House,
  Newspaper,
  User,
  Buildings,
  Trophy,
  Link as LinkIcon,
  Lightning,
  Handshake,
  TrendUp,
  Megaphone,
  Gear,
  SignOut,
} from "@phosphor-icons/react";

export default function AdminLayout({ children, title }) {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("adminToken");
    navigate("/admin/login");
  };

  const navItems = [
    { path: "/admin", icon: House, label: "Dashboard" },
    { path: "/admin/articles", icon: Newspaper, label: "Artikel" },
    { path: "/admin/events", icon: Lightning, label: "Events" },
    { path: "/admin/players", icon: User, label: "Spieler" },
    { path: "/admin/clubs", icon: Buildings, label: "Vereine" },
    { path: "/admin/competitions", icon: Trophy, label: "Wettbewerbe" },
    { path: "/admin/transfers", icon: Handshake, label: "Transfers" },
    { path: "/admin/rumours", icon: TrendUp, label: "Gerüchte" },
    { path: "/admin/sources", icon: LinkIcon, label: "Quellen" },
    { path: "/admin/ad-slots", icon: Megaphone, label: "Ad-Slots" },
  ];

  return (
    <div className="min-h-screen flex bg-gray-100" data-testid="admin-layout">
      {/* Sidebar */}
      <aside className="admin-sidebar w-64 flex-shrink-0">
        <div className="p-4 border-b border-white/10">
          <Link to="/admin" className="block">
            <h1 className="font-['Oswald'] text-xl font-bold text-white uppercase">
              Transfer<span className="text-[#8FCC3D]">News</span>
            </h1>
            <p className="text-xs text-white/50 mt-1">Admin-Dashboard</p>
          </Link>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2 text-sm rounded transition-colors ${
                  isActive ? "bg-white/10 text-white" : "text-white/70 hover:text-white hover:bg-white/5"
                }`}
                data-testid={`nav-${item.label.toLowerCase()}`}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 w-64 p-4 border-t border-white/10">
          <Link
            to="/"
            className="flex items-center gap-3 px-3 py-2 text-sm text-white/70 hover:text-white transition-colors"
          >
            <House size={18} />
            Zur Website
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 text-sm text-white/70 hover:text-white transition-colors w-full"
            data-testid="logout-button"
          >
            <SignOut size={18} />
            Abmelden
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        {title && (
          <div className="mb-8">
            <h1 className="font-['Oswald'] text-3xl font-bold uppercase">{title}</h1>
          </div>
        )}
        {children}
      </main>
    </div>
  );
}
