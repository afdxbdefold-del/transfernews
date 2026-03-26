import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getClubs, createClub, updateClub, deleteClub, getCompetitions } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Pencil, Trash } from "@phosphor-icons/react";

export default function AdminClubs() {
  const [clubs, setClubs] = useState([]);
  const [competitions, setCompetitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingClub, setEditingClub] = useState(null);
  const [formData, setFormData] = useState({ name: "", slug: "", country: "", competition_id: "", aliases: "" });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { navigate("/admin/login"); return; }
    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    try {
      const [clubsRes, compsRes] = await Promise.all([getClubs({ limit: 100 }), getCompetitions({ limit: 100 })]);
      setClubs(clubsRes.data);
      setCompetitions(compsRes.data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const generateSlug = (name) => name.toLowerCase().replace(/[äÄ]/g, "ae").replace(/[öÖ]/g, "oe").replace(/[üÜ]/g, "ue").replace(/[ß]/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const resetForm = () => { setFormData({ name: "", slug: "", country: "", competition_id: "", aliases: "" }); setEditingClub(null); };

  const handleEdit = (club) => {
    setEditingClub(club);
    setFormData({ name: club.name || "", slug: club.slug || "", country: club.country || "", competition_id: club.competition_id || "", aliases: (club.aliases || []).join(", ") });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { ...formData, slug: formData.slug || generateSlug(formData.name), aliases: formData.aliases ? formData.aliases.split(",").map((a) => a.trim()) : [], competition_id: formData.competition_id || null };
    try {
      if (editingClub) { await updateClub(editingClub.id, data); toast.success("Verein aktualisiert"); }
      else { await createClub(data); toast.success("Verein erstellt"); }
      setDialogOpen(false); resetForm(); fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Fehler"); }
  };

  const handleDelete = async (id) => { if (!confirm("Wirklich löschen?")) return; try { await deleteClub(id); toast.success("Gelöscht"); fetchData(); } catch { toast.error("Fehler"); } };

  return (
    <AdminLayout title="Vereine">
      <div data-testid="admin-clubs">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{clubs.length} Vereine</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={resetForm} className="bg-[#00a651] hover:bg-[#008c45]" data-testid="create-club-btn"><Plus size={18} className="mr-2" />Neuer Verein</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle className="font-['Oswald'] uppercase">{editingClub ? "Verein bearbeiten" : "Neuer Verein"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div><label className="block text-sm font-medium mb-1">Name *</label><Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required data-testid="club-name-input" /></div>
                <div><label className="block text-sm font-medium mb-1">Slug</label><Input value={formData.slug} onChange={(e) => setFormData({ ...formData, slug: e.target.value })} placeholder="auto" /></div>
                <div><label className="block text-sm font-medium mb-1">Land</label><Input value={formData.country} onChange={(e) => setFormData({ ...formData, country: e.target.value })} /></div>
                <div><label className="block text-sm font-medium mb-1">Wettbewerb</label>
                  <Select value={formData.competition_id} onValueChange={(v) => setFormData({ ...formData, competition_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger>
                    <SelectContent>{competitions.map((c) => (<SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>))}</SelectContent>
                  </Select>
                </div>
                <div><label className="block text-sm font-medium mb-1">Aliase</label><Input value={formData.aliases} onChange={(e) => setFormData({ ...formData, aliases: e.target.value })} placeholder="kommagetrennt" /></div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Abbrechen</Button>
                  <Button type="submit" className="bg-[#00a651] hover:bg-[#008c45]" data-testid="save-club-btn">{editingClub ? "Aktualisieren" : "Erstellen"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="bg-white border border-gray-200">
          {loading ? <div className="p-8 text-center">Lädt...</div> : clubs.length === 0 ? <div className="p-8 text-center text-gray-500">Keine Vereine</div> : (
            <table className="admin-table w-full"><thead><tr><th>Name</th><th>Slug</th><th>Land</th><th className="text-right">Aktionen</th></tr></thead>
              <tbody>{clubs.map((club) => (<tr key={club.id}><td className="font-medium">{club.name}</td><td><code className="text-xs bg-gray-100 px-2 py-1 rounded">{club.slug}</code></td><td>{club.country || "-"}</td><td className="text-right"><Button size="sm" variant="ghost" onClick={() => handleEdit(club)}><Pencil size={16} /></Button><Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(club.id)}><Trash size={16} /></Button></td></tr>))}</tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
