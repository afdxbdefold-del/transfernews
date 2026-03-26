import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getArticles, createArticle, updateArticle, deleteArticle, getPlayers, getClubs, getCompetitions } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Pencil, Trash, Eye } from "@phosphor-icons/react";

const ARTICLE_TYPES = ["news", "rumour", "transfer", "analysis", "interview", "special"];
const ARTICLE_STATUSES = ["draft", "review", "scheduled", "published", "archived"];

export default function AdminArticles() {
  const [articles, setArticles] = useState([]);
  const [players, setPlayers] = useState([]);
  const [clubs, setClubs] = useState([]);
  const [competitions, setCompetitions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({
    title: "", slug: "", excerpt: "", body: "", article_type: "news", status: "draft",
    seo_title: "", meta_description: "", feature_image: "", is_breaking: false, is_featured: false,
    linked_player_ids: [], linked_club_ids: [], linked_competition_ids: []
  });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { navigate("/admin/login"); return; }
    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    try {
      const [articlesRes, playersRes, clubsRes, compsRes] = await Promise.all([
        getArticles({ limit: 100 }), getPlayers({ limit: 200 }), getClubs({ limit: 200 }), getCompetitions({ limit: 100 })
      ]);
      setArticles(articlesRes.data); setPlayers(playersRes.data); setClubs(clubsRes.data); setCompetitions(compsRes.data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const generateSlug = (title) => title.toLowerCase().replace(/[äÄ]/g, "ae").replace(/[öÖ]/g, "oe").replace(/[üÜ]/g, "ue").replace(/[ß]/g, "ss").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

  const resetForm = () => {
    setFormData({ title: "", slug: "", excerpt: "", body: "", article_type: "news", status: "draft", seo_title: "", meta_description: "", feature_image: "", is_breaking: false, is_featured: false, linked_player_ids: [], linked_club_ids: [], linked_competition_ids: [] });
    setEditing(null);
  };

  const handleEdit = (item) => {
    setEditing(item);
    setFormData({
      title: item.title || "", slug: item.slug || "", excerpt: item.excerpt || "", body: item.body || "",
      article_type: item.article_type || "news", status: item.status || "draft",
      seo_title: item.seo_title || "", meta_description: item.meta_description || "",
      feature_image: item.feature_image || "", is_breaking: item.is_breaking || false,
      is_featured: item.is_featured || false, linked_player_ids: item.linked_player_ids || [],
      linked_club_ids: item.linked_club_ids || [], linked_competition_ids: item.linked_competition_ids || []
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { ...formData, slug: formData.slug || generateSlug(formData.title) };
    try {
      if (editing) { await updateArticle(editing.id, data); toast.success("Aktualisiert"); }
      else { await createArticle(data); toast.success("Erstellt"); }
      setDialogOpen(false); resetForm(); fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Fehler"); }
  };

  const handleDelete = async (id) => { if (!confirm("Wirklich löschen?")) return; try { await deleteArticle(id); toast.success("Gelöscht"); fetchData(); } catch { toast.error("Fehler"); } };

  const handlePublish = async (article) => {
    try {
      await updateArticle(article.id, { status: "published" });
      toast.success("Veröffentlicht");
      fetchData();
    } catch { toast.error("Fehler"); }
  };

  const getStatusBadge = (status) => {
    const colors = { draft: "bg-gray-100 text-gray-600", review: "bg-yellow-100 text-yellow-800", scheduled: "bg-blue-100 text-blue-800", published: "bg-green-100 text-green-800", archived: "bg-slate-100 text-slate-600" };
    return colors[status] || colors.draft;
  };

  const formatDate = (d) => d ? new Date(d).toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "numeric" }) : "-";

  return (
    <AdminLayout title="Artikel">
      <div data-testid="admin-articles">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{articles.length} Artikel</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild><Button onClick={resetForm} className="bg-[#00a651] hover:bg-[#008c45]" data-testid="create-article-btn"><Plus size={18} className="mr-2" />Neuer Artikel</Button></DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader><DialogTitle className="font-['Oswald'] uppercase">{editing ? "Artikel bearbeiten" : "Neuer Artikel"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div><label className="block text-sm font-medium mb-1">Titel *</label><Input value={formData.title} onChange={(e) => setFormData({ ...formData, title: e.target.value })} required data-testid="article-title-input" /></div>
                <div><label className="block text-sm font-medium mb-1">Slug</label><Input value={formData.slug} onChange={(e) => setFormData({ ...formData, slug: e.target.value })} placeholder="auto" /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Typ</label>
                    <Select value={formData.article_type} onValueChange={(v) => setFormData({ ...formData, article_type: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{ARTICLE_TYPES.map((t) => (<SelectItem key={t} value={t}>{t}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Status</label>
                    <Select value={formData.status} onValueChange={(v) => setFormData({ ...formData, status: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{ARTICLE_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}</SelectContent></Select>
                  </div>
                </div>
                <div><label className="block text-sm font-medium mb-1">Excerpt</label><Textarea value={formData.excerpt} onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })} rows={2} /></div>
                <div><label className="block text-sm font-medium mb-1">Body</label><Textarea value={formData.body} onChange={(e) => setFormData({ ...formData, body: e.target.value })} rows={8} /></div>
                <div><label className="block text-sm font-medium mb-1">Bild-URL</label><Input value={formData.feature_image} onChange={(e) => setFormData({ ...formData, feature_image: e.target.value })} /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">SEO-Titel</label><Input value={formData.seo_title} onChange={(e) => setFormData({ ...formData, seo_title: e.target.value })} /></div>
                  <div><label className="block text-sm font-medium mb-1">Meta-Description</label><Input value={formData.meta_description} onChange={(e) => setFormData({ ...formData, meta_description: e.target.value })} /></div>
                </div>
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2"><Switch checked={formData.is_breaking} onCheckedChange={(v) => setFormData({ ...formData, is_breaking: v })} /><span className="text-sm">Breaking News</span></div>
                  <div className="flex items-center gap-2"><Switch checked={formData.is_featured} onCheckedChange={(v) => setFormData({ ...formData, is_featured: v })} /><span className="text-sm">Featured</span></div>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Abbrechen</Button>
                  <Button type="submit" className="bg-[#00a651] hover:bg-[#008c45]" data-testid="save-article-btn">{editing ? "Aktualisieren" : "Erstellen"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="bg-white border border-gray-200">
          {loading ? <div className="p-8 text-center">Lädt...</div> : articles.length === 0 ? <div className="p-8 text-center text-gray-500">Keine Artikel</div> : (
            <table className="admin-table w-full"><thead><tr><th>Titel</th><th>Typ</th><th>Status</th><th>Datum</th><th className="text-right">Aktionen</th></tr></thead>
              <tbody>{articles.map((a) => (
                <tr key={a.id}>
                  <td className="font-medium">
                    <div className="flex items-center gap-2">
                      {a.is_breaking && <Badge className="badge-breaking text-xs">BREAKING</Badge>}
                      <span className="max-w-xs truncate">{a.title}</span>
                    </div>
                  </td>
                  <td><Badge variant="outline">{a.article_type}</Badge></td>
                  <td><Badge className={getStatusBadge(a.status)}>{a.status}</Badge></td>
                  <td className="text-sm text-gray-500">{formatDate(a.published_at || a.created_at)}</td>
                  <td className="text-right">
                    {a.status === "draft" && <Button size="sm" variant="ghost" onClick={() => handlePublish(a)} title="Veröffentlichen"><Eye size={16} className="text-green-600" /></Button>}
                    <Button size="sm" variant="ghost" onClick={() => handleEdit(a)}><Pencil size={16} /></Button>
                    <Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(a.id)}><Trash size={16} /></Button>
                  </td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
