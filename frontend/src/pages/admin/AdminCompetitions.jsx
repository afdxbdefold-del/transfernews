import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getCompetitions, createCompetition, updateCompetition, deleteCompetition } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, Pencil, Trash } from "@phosphor-icons/react";

export default function AdminCompetitions() {
  const [competitions, setCompetitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({ name: "", slug: "", country: "", type: "league" });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { navigate("/admin/login"); return; }
    fetchData();
  }, [navigate]);

  const fetchData = async () => { try { const res = await getCompetitions({ limit: 100 }); setCompetitions(res.data); } catch (e) { console.error(e); } finally { setLoading(false); } };

  const generateSlug = (name) => name.toLowerCase().replace(/[äÄ]/g, "ae").replace(/[öÖ]/g, "oe").replace(/[üÜ]/g, "ue").replace(/[ß]/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const resetForm = () => { setFormData({ name: "", slug: "", country: "", type: "league" }); setEditing(null); };

  const handleEdit = (item) => { setEditing(item); setFormData({ name: item.name || "", slug: item.slug || "", country: item.country || "", type: item.type || "league" }); setDialogOpen(true); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { ...formData, slug: formData.slug || generateSlug(formData.name) };
    try {
      if (editing) { await updateCompetition(editing.id, data); toast.success("Aktualisiert"); }
      else { await createCompetition(data); toast.success("Erstellt"); }
      setDialogOpen(false); resetForm(); fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Fehler"); }
  };

  const handleDelete = async (id) => { if (!confirm("Wirklich löschen?")) return; try { await deleteCompetition(id); toast.success("Gelöscht"); fetchData(); } catch { toast.error("Fehler"); } };

  return (
    <AdminLayout title="Wettbewerbe">
      <div data-testid="admin-competitions">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{competitions.length} Wettbewerbe</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild><Button onClick={resetForm} className="bg-[#00a651] hover:bg-[#008c45]" data-testid="create-competition-btn"><Plus size={18} className="mr-2" />Neuer Wettbewerb</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle className="font-['Oswald'] uppercase">{editing ? "Bearbeiten" : "Neu"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div><label className="block text-sm font-medium mb-1">Name *</label><Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required data-testid="competition-name-input" /></div>
                <div><label className="block text-sm font-medium mb-1">Slug</label><Input value={formData.slug} onChange={(e) => setFormData({ ...formData, slug: e.target.value })} /></div>
                <div><label className="block text-sm font-medium mb-1">Land</label><Input value={formData.country} onChange={(e) => setFormData({ ...formData, country: e.target.value })} /></div>
                <div><label className="block text-sm font-medium mb-1">Typ</label><Input value={formData.type} onChange={(e) => setFormData({ ...formData, type: e.target.value })} placeholder="league/cup/tournament" /></div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Abbrechen</Button>
                  <Button type="submit" className="bg-[#00a651] hover:bg-[#008c45]" data-testid="save-competition-btn">{editing ? "Aktualisieren" : "Erstellen"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="bg-white border border-gray-200">
          {loading ? <div className="p-8 text-center">Lädt...</div> : competitions.length === 0 ? <div className="p-8 text-center text-gray-500">Keine Wettbewerbe</div> : (
            <table className="admin-table w-full"><thead><tr><th>Name</th><th>Slug</th><th>Land</th><th>Typ</th><th className="text-right">Aktionen</th></tr></thead>
              <tbody>{competitions.map((c) => (<tr key={c.id}><td className="font-medium">{c.name}</td><td><code className="text-xs bg-gray-100 px-2 py-1 rounded">{c.slug}</code></td><td>{c.country || "-"}</td><td>{c.type}</td><td className="text-right"><Button size="sm" variant="ghost" onClick={() => handleEdit(c)}><Pencil size={16} /></Button><Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(c.id)}><Trash size={16} /></Button></td></tr>))}</tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
