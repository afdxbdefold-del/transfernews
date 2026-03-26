import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getRumours, createRumour, updateRumour, deleteRumour, getPlayers, getClubs, getSources } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Pencil, Trash } from "@phosphor-icons/react";

const RUMOUR_STATUSES = ["active", "confirmed", "denied", "expired"];

export default function AdminRumours() {
  const [rumours, setRumours] = useState([]);
  const [players, setPlayers] = useState([]);
  const [clubs, setClubs] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({ player_id: "", target_club_id: "", source_id: "", source_url: "", confidence_score: 50, status: "active" });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { navigate("/admin/login"); return; }
    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    try {
      const [rumoursRes, playersRes, clubsRes, sourcesRes] = await Promise.all([
        getRumours({ limit: 100 }), getPlayers({ limit: 200 }), getClubs({ limit: 200 }), getSources({ limit: 100 })
      ]);
      setRumours(rumoursRes.data); setPlayers(playersRes.data); setClubs(clubsRes.data); setSources(sourcesRes.data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const resetForm = () => { setFormData({ player_id: "", target_club_id: "", source_id: "", source_url: "", confidence_score: 50, status: "active" }); setEditing(null); };

  const handleEdit = (item) => {
    setEditing(item);
    setFormData({
      player_id: item.player_id || "", target_club_id: item.target_club_id || "", source_id: item.source_id || "",
      source_url: item.source_url || "", confidence_score: item.confidence_score || 50, status: item.status || "active"
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { ...formData, confidence_score: parseInt(formData.confidence_score) || 50, player_id: formData.player_id || null, target_club_id: formData.target_club_id || null, source_id: formData.source_id || null };
    try {
      if (editing) { await updateRumour(editing.id, data); toast.success("Aktualisiert"); }
      else { await createRumour(data); toast.success("Erstellt"); }
      setDialogOpen(false); resetForm(); fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Fehler"); }
  };

  const handleDelete = async (id) => { if (!confirm("Wirklich löschen?")) return; try { await deleteRumour(id); toast.success("Gelöscht"); fetchData(); } catch { toast.error("Fehler"); } };

  const getStatusBadge = (status) => {
    const colors = { active: "badge-rumour", confirmed: "badge-confirmed", denied: "bg-red-100 text-red-800", expired: "bg-gray-100 text-gray-600" };
    return colors[status] || colors.active;
  };

  const getPlayerName = (id) => players.find(p => p.id === id)?.name || "-";
  const getClubName = (id) => clubs.find(c => c.id === id)?.name || "-";

  return (
    <AdminLayout title="Gerüchte">
      <div data-testid="admin-rumours">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{rumours.length} Gerüchte</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild><Button onClick={resetForm} className="bg-[#00a651] hover:bg-[#008c45]" data-testid="create-rumour-btn"><Plus size={18} className="mr-2" />Neues Gerücht</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle className="font-['Oswald'] uppercase">{editing ? "Gerücht bearbeiten" : "Neues Gerücht"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div><label className="block text-sm font-medium mb-1">Spieler *</label>
                  <Select value={formData.player_id} onValueChange={(v) => setFormData({ ...formData, player_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{players.map((p) => (<SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>))}</SelectContent></Select>
                </div>
                <div><label className="block text-sm font-medium mb-1">Ziel-Verein</label>
                  <Select value={formData.target_club_id} onValueChange={(v) => setFormData({ ...formData, target_club_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{clubs.map((c) => (<SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>))}</SelectContent></Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Status</label>
                    <Select value={formData.status} onValueChange={(v) => setFormData({ ...formData, status: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{RUMOUR_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Confidence Score</label><Input type="number" min="0" max="100" value={formData.confidence_score} onChange={(e) => setFormData({ ...formData, confidence_score: e.target.value })} /></div>
                </div>
                <div><label className="block text-sm font-medium mb-1">Quelle</label>
                  <Select value={formData.source_id} onValueChange={(v) => setFormData({ ...formData, source_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{sources.map((s) => (<SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>))}</SelectContent></Select>
                </div>
                <div><label className="block text-sm font-medium mb-1">Quellen-URL</label><Input value={formData.source_url} onChange={(e) => setFormData({ ...formData, source_url: e.target.value })} /></div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Abbrechen</Button>
                  <Button type="submit" className="bg-[#00a651] hover:bg-[#008c45]">{editing ? "Aktualisieren" : "Erstellen"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="bg-white border border-gray-200">
          {loading ? <div className="p-8 text-center">Lädt...</div> : rumours.length === 0 ? <div className="p-8 text-center text-gray-500">Keine Gerüchte</div> : (
            <table className="admin-table w-full"><thead><tr><th>Spieler</th><th>Ziel-Verein</th><th>Status</th><th>Confidence</th><th className="text-right">Aktionen</th></tr></thead>
              <tbody>{rumours.map((r) => (
                <tr key={r.id}>
                  <td className="font-medium">{getPlayerName(r.player_id)}</td>
                  <td>{getClubName(r.target_club_id)}</td>
                  <td><Badge className={getStatusBadge(r.status)}>{r.status}</Badge></td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-16 bg-gray-200 rounded"><div className="h-full bg-yellow-500 rounded" style={{ width: `${r.confidence_score}%` }} /></div>
                      <span className="text-sm">{r.confidence_score}%</span>
                    </div>
                  </td>
                  <td className="text-right"><Button size="sm" variant="ghost" onClick={() => handleEdit(r)}><Pencil size={16} /></Button><Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(r.id)}><Trash size={16} /></Button></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
