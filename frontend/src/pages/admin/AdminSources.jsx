import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getSources, createSource, updateSource, deleteSource } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Pencil, Trash } from "@phosphor-icons/react";

const SOURCE_TYPES = ["official", "journalist", "media", "aggregator", "social"];
const SOURCE_CATEGORIES = ["tier_1", "tier_2", "tier_3", "unverified"];

export default function AdminSources() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({ name: "", slug: "", type: "media", source_url: "", source_category: "tier_2", active: true, trust_score: 50 });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { navigate("/admin/login"); return; }
    fetchData();
  }, [navigate]);

  const fetchData = async () => { try { const res = await getSources({ limit: 100 }); setSources(res.data); } catch (e) { console.error(e); } finally { setLoading(false); } };

  const generateSlug = (name) => name.toLowerCase().replace(/[äÄ]/g, "ae").replace(/[öÖ]/g, "oe").replace(/[üÜ]/g, "ue").replace(/[ß]/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const resetForm = () => { setFormData({ name: "", slug: "", type: "media", source_url: "", source_category: "tier_2", active: true, trust_score: 50 }); setEditing(null); };

  const handleEdit = (item) => { setEditing(item); setFormData({ name: item.name || "", slug: item.slug || "", type: item.type || "media", source_url: item.source_url || "", source_category: item.source_category || "tier_2", active: item.active ?? true, trust_score: item.trust_score || 50 }); setDialogOpen(true); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { ...formData, slug: formData.slug || generateSlug(formData.name), trust_score: parseInt(formData.trust_score) || 50 };
    try {
      if (editing) { await updateSource(editing.id, data); toast.success("Aktualisiert"); }
      else { await createSource(data); toast.success("Erstellt"); }
      setDialogOpen(false); resetForm(); fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Fehler"); }
  };

  const handleDelete = async (id) => { if (!confirm("Wirklich löschen?")) return; try { await deleteSource(id); toast.success("Gelöscht"); fetchData(); } catch { toast.error("Fehler"); } };

  const getCategoryBadge = (cat) => {
    const colors = { tier_1: "bg-green-100 text-green-800", tier_2: "bg-blue-100 text-blue-800", tier_3: "bg-yellow-100 text-yellow-800", unverified: "bg-gray-100 text-gray-600" };
    return colors[cat] || colors.unverified;
  };

  return (
    <AdminLayout title="Quellen">
      <div data-testid="admin-sources">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{sources.length} Quellen</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild><Button onClick={resetForm} className="bg-[#00a651] hover:bg-[#008c45]" data-testid="create-source-btn"><Plus size={18} className="mr-2" />Neue Quelle</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle className="font-['Oswald'] uppercase">{editing ? "Bearbeiten" : "Neu"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div><label className="block text-sm font-medium mb-1">Name *</label><Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} required /></div>
                <div><label className="block text-sm font-medium mb-1">Slug</label><Input value={formData.slug} onChange={(e) => setFormData({ ...formData, slug: e.target.value })} /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Typ</label>
                    <Select value={formData.type} onValueChange={(v) => setFormData({ ...formData, type: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{SOURCE_TYPES.map((t) => (<SelectItem key={t} value={t}>{t}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Kategorie</label>
                    <Select value={formData.source_category} onValueChange={(v) => setFormData({ ...formData, source_category: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{SOURCE_CATEGORIES.map((c) => (<SelectItem key={c} value={c}>{c}</SelectItem>))}</SelectContent></Select>
                  </div>
                </div>
                <div><label className="block text-sm font-medium mb-1">URL</label><Input value={formData.source_url} onChange={(e) => setFormData({ ...formData, source_url: e.target.value })} /></div>
                <div><label className="block text-sm font-medium mb-1">Trust Score (0-100)</label><Input type="number" min="0" max="100" value={formData.trust_score} onChange={(e) => setFormData({ ...formData, trust_score: e.target.value })} /></div>
                <div className="flex items-center gap-2"><Switch checked={formData.active} onCheckedChange={(v) => setFormData({ ...formData, active: v })} /><span className="text-sm">Aktiv</span></div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Abbrechen</Button>
                  <Button type="submit" className="bg-[#00a651] hover:bg-[#008c45]">{editing ? "Aktualisieren" : "Erstellen"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="bg-white border border-gray-200">
          {loading ? <div className="p-8 text-center">Lädt...</div> : sources.length === 0 ? <div className="p-8 text-center text-gray-500">Keine Quellen</div> : (
            <table className="admin-table w-full"><thead><tr><th>Name</th><th>Typ</th><th>Kategorie</th><th>Trust</th><th>Status</th><th className="text-right">Aktionen</th></tr></thead>
              <tbody>{sources.map((s) => (<tr key={s.id}><td className="font-medium">{s.name}</td><td>{s.type}</td><td><Badge className={getCategoryBadge(s.source_category)}>{s.source_category}</Badge></td><td>{s.trust_score}%</td><td><Badge className={s.active ? "bg-green-100 text-green-800" : "bg-gray-100"}>{s.active ? "Aktiv" : "Inaktiv"}</Badge></td><td className="text-right"><Button size="sm" variant="ghost" onClick={() => handleEdit(s)}><Pencil size={16} /></Button><Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(s.id)}><Trash size={16} /></Button></td></tr>))}</tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
