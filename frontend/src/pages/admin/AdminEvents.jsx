import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getEvents, createEvent, updateEvent, deleteEvent, getPlayers, getClubs, getSources } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Pencil, Trash } from "@phosphor-icons/react";

const EVENT_TYPES = ["rumour", "advanced", "confirmed", "official"];
const EVENT_STATUSES = ["pending", "processed", "rejected", "published"];

export default function AdminEvents() {
  const [events, setEvents] = useState([]);
  const [players, setPlayers] = useState([]);
  const [clubs, setClubs] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({ event_type: "rumour", status: "pending", player_id: "", from_club_id: "", to_club_id: "", headline_raw: "", body_raw: "", source_id: "", source_url: "", confidence_score: 50 });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { navigate("/admin/login"); return; }
    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    try {
      const [eventsRes, playersRes, clubsRes, sourcesRes] = await Promise.all([
        getEvents({ limit: 100 }), getPlayers({ limit: 200 }), getClubs({ limit: 200 }), getSources({ limit: 100 })
      ]);
      setEvents(eventsRes.data); setPlayers(playersRes.data); setClubs(clubsRes.data); setSources(sourcesRes.data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const resetForm = () => { setFormData({ event_type: "rumour", status: "pending", player_id: "", from_club_id: "", to_club_id: "", headline_raw: "", body_raw: "", source_id: "", source_url: "", confidence_score: 50 }); setEditing(null); };

  const handleEdit = (item) => {
    setEditing(item);
    setFormData({
      event_type: item.event_type || "rumour", status: item.status || "pending", player_id: item.player_id || "",
      from_club_id: item.from_club_id || "", to_club_id: item.to_club_id || "", headline_raw: item.headline_raw || "",
      body_raw: item.body_raw || "", source_id: item.source_id || "", source_url: item.source_url || "",
      confidence_score: item.confidence_score || 50
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { ...formData, confidence_score: parseInt(formData.confidence_score) || 50, player_id: formData.player_id || null, from_club_id: formData.from_club_id || null, to_club_id: formData.to_club_id || null, source_id: formData.source_id || null };
    try {
      if (editing) { await updateEvent(editing.id, data); toast.success("Aktualisiert"); }
      else { await createEvent(data); toast.success("Erstellt"); }
      setDialogOpen(false); resetForm(); fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Fehler"); }
  };

  const handleDelete = async (id) => { if (!confirm("Wirklich löschen?")) return; try { await deleteEvent(id); toast.success("Gelöscht"); fetchData(); } catch { toast.error("Fehler"); } };

  const getStatusBadge = (status) => {
    const colors = { pending: "bg-yellow-100 text-yellow-800", processed: "bg-blue-100 text-blue-800", rejected: "bg-red-100 text-red-800", published: "bg-green-100 text-green-800" };
    return colors[status] || colors.pending;
  };

  return (
    <AdminLayout title="Events">
      <div data-testid="admin-events">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{events.length} Events</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild><Button onClick={resetForm} className="bg-[#79B92A] hover:bg-[#6aa325]" data-testid="create-event-btn"><Plus size={18} className="mr-2" />Neues Event</Button></DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader><DialogTitle className="font-['Oswald'] uppercase">{editing ? "Event bearbeiten" : "Neues Event"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Event-Typ</label>
                    <Select value={formData.event_type} onValueChange={(v) => setFormData({ ...formData, event_type: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{EVENT_TYPES.map((t) => (<SelectItem key={t} value={t}>{t}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Status</label>
                    <Select value={formData.status} onValueChange={(v) => setFormData({ ...formData, status: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{EVENT_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}</SelectContent></Select>
                  </div>
                </div>
                <div><label className="block text-sm font-medium mb-1">Headline *</label><Input value={formData.headline_raw} onChange={(e) => setFormData({ ...formData, headline_raw: e.target.value })} required /></div>
                <div><label className="block text-sm font-medium mb-1">Body</label><Textarea value={formData.body_raw} onChange={(e) => setFormData({ ...formData, body_raw: e.target.value })} rows={4} /></div>
                <div className="grid grid-cols-3 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Spieler</label>
                    <Select value={formData.player_id} onValueChange={(v) => setFormData({ ...formData, player_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{players.map((p) => (<SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Von Verein</label>
                    <Select value={formData.from_club_id} onValueChange={(v) => setFormData({ ...formData, from_club_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{clubs.map((c) => (<SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Zu Verein</label>
                    <Select value={formData.to_club_id} onValueChange={(v) => setFormData({ ...formData, to_club_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{clubs.map((c) => (<SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>))}</SelectContent></Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Quelle</label>
                    <Select value={formData.source_id} onValueChange={(v) => setFormData({ ...formData, source_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{sources.map((s) => (<SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Confidence Score</label><Input type="number" min="0" max="100" value={formData.confidence_score} onChange={(e) => setFormData({ ...formData, confidence_score: e.target.value })} /></div>
                </div>
                <div><label className="block text-sm font-medium mb-1">Quellen-URL</label><Input value={formData.source_url} onChange={(e) => setFormData({ ...formData, source_url: e.target.value })} /></div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Abbrechen</Button>
                  <Button type="submit" className="bg-[#79B92A] hover:bg-[#6aa325]">{editing ? "Aktualisieren" : "Erstellen"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="bg-white border border-gray-200">
          {loading ? <div className="p-8 text-center">Lädt...</div> : events.length === 0 ? <div className="p-8 text-center text-gray-500">Keine Events</div> : (
            <table className="admin-table w-full"><thead><tr><th>Headline</th><th>Typ</th><th>Status</th><th>Confidence</th><th className="text-right">Aktionen</th></tr></thead>
              <tbody>{events.map((e) => (<tr key={e.id}><td className="font-medium max-w-xs truncate">{e.headline_raw}</td><td><Badge variant="outline">{e.event_type}</Badge></td><td><Badge className={getStatusBadge(e.status)}>{e.status}</Badge></td><td>{e.confidence_score}%</td><td className="text-right"><Button size="sm" variant="ghost" onClick={() => handleEdit(e)}><Pencil size={16} /></Button><Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(e.id)}><Trash size={16} /></Button></td></tr>))}</tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
