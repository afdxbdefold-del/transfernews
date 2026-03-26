import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { login, initAdmin } from "@/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Lock, User } from "@phosphor-icons/react";

export default function AdminLogin() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if already logged in
    const token = localStorage.getItem("adminToken");
    if (token) {
      navigate("/admin");
    }
    
    // Initialize admin user on first load
    initAdmin().catch(() => {});
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const res = await login(email, password);
      localStorage.setItem("adminToken", res.data.access_token);
      toast.success("Erfolgreich angemeldet");
      navigate("/admin");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Anmeldung fehlgeschlagen");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100" data-testid="admin-login">
      <div className="bg-white p-8 border border-gray-200 w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-3xl font-extrabold tracking-tight" style={{fontFamily: 'Inter, sans-serif'}}>
            <span className="text-gray-900">transfer</span>
            <span className="text-[#79B92A]">news</span>
          </span>
          <p className="text-gray-500 mt-2">Admin-Bereich</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">E-Mail</label>
            <div className="relative">
              <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@transfernews.de"
                className="pl-10"
                required
                data-testid="email-input"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Passwort</label>
            <div className="relative">
              <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="pl-10"
                required
                data-testid="password-input"
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#79B92A] hover:bg-[#6aa325]"
            data-testid="login-button"
          >
            {loading ? "Wird angemeldet..." : "Anmelden"}
          </Button>
        </form>

        <div className="mt-6 p-4 bg-gray-50 border text-sm">
          <p className="font-medium mb-1">Demo-Zugangsdaten:</p>
          <p className="text-gray-600">E-Mail: admin@transfernews.de</p>
          <p className="text-gray-600">Passwort: admin123</p>
        </div>
      </div>
    </div>
  );
}
