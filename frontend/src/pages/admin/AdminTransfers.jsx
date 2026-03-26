import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getTransfers, createTransfer, updateTransfer, deleteTransfer, getPlayers, getClubs, getSources } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Pencil, Trash } from "@phosphor-icons/react";

const TRANSFER_TYPES = ["permanent", "loan", "free", "loan_with_option", "youth"];
const TRANSFER_STATUSES = ["rumour", "advanced", "confirmed", "official"];

export default function AdminTransfers() {
  const [transfers, setTransfers] = useState([]);
  const [players, setPlayers] = useState([]);
  const [clubs, setClubs] = useState([]);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [formData, setFormData] = useState({ player_id: "", from_club_id: "", to_club_id: "", transfer_type: "permanent", fee_amount: "", fee_currency: "EUR", season: "", status: "rumour", source_id: "", source_url: "" });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) { navigate("/admin/login"); return; }
    fetchData();
  }, [navigate]);

  const fetchData = async () => {
    try {
      const [transfersRes, playersRes, clubsRes, sourcesRes] = await Promise.all([
        getTransfers({ limit: 100 }), getPlayers({ limit: 200 }), getClubs({ limit: 200 }), getSources({ limit: 100 })
      ]);
      setTransfers(transfersRes.data); setPlayers(playersRes.data); setClubs(clubsRes.data); setSources(sourcesRes.data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  const resetForm = () => { setFormData({ player_id: "", from_club_id: "", to_club_id: "", transfer_type: "permanent", fee_amount: "", fee_currency: "EUR", season: "", status: "rumour", source_id: "", source_url: "" }); setEditing(null); };

  const handleEdit = (item) => {
    setEditing(item);
    setFormData({
      player_id: item.player_id || "", from_club_id: item.from_club_id || "", to_club_id: item.to_club_id || "",
      transfer_type: item.transfer_type || "permanent", fee_amount: item.fee_amount || "", fee_currency: item.fee_currency || "EUR",
      season: item.season || "", status: item.status || "rumour", source_id: item.source_id || "", source_url: item.source_url || ""
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = { ...formData, fee_amount: formData.fee_amount ? parseFloat(formData.fee_amount) : null, player_id: formData.player_id || null, from_club_id: formData.from_club_id || null, to_club_id: formData.to_club_id || null, source_id: formData.source_id || null };
    try {
      if (editing) { await updateTransfer(editing.id, data); toast.success("Aktualisiert"); }
      else { await createTransfer(data); toast.success("Erstellt"); }
      setDialogOpen(false); resetForm(); fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || "Fehler"); }
  };

  const handleDelete = async (id) => { if (!confirm("Wirklich löschen?")) return; try { await deleteTransfer(id); toast.success("Gelöscht"); fetchData(); } catch { toast.error("Fehler"); } };

  const getStatusBadge = (status) => {
    const colors = { rumour: "badge-rumour", advanced: "bg-orange-100 text-orange-800", confirmed: "badge-confirmed", official: "badge-official" };
    return colors[status] || colors.rumour;
  };

  const getPlayerName = (id) => players.find(p => p.id === id)?.name || "-";
  const getClubName = (id) => clubs.find(c => c.id === id)?.name || "-";

  return (
    <AdminLayout title="Transfers">
      <div data-testid="admin-transfers">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{transfers.length} Transfers</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild><Button onClick={resetForm} className="bg-[#79B92A] hover:bg-[#6aa325]" data-testid="create-transfer-btn"><Plus size={18} className="mr-2" />Neuer Transfer</Button></DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader><DialogTitle className="font-['Oswald'] uppercase">{editing ? "Transfer bearbeiten" : "Neuer Transfer"}</DialogTitle></DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div><label className="block text-sm font-medium mb-1">Spieler *</label>
                  <Select value={formData.player_id} onValueChange={(v) => setFormData({ ...formData, player_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{players.map((p) => (<SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>))}</SelectContent></Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Von Verein</label>
                    <Select value={formData.from_club_id} onValueChange={(v) => setFormData({ ...formData, from_club_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{clubs.map((c) => (<SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Zu Verein</label>
                    <Select value={formData.to_club_id} onValueChange={(v) => setFormData({ ...formData, to_club_id: v })}><SelectTrigger><SelectValue placeholder="Auswählen..." /></SelectTrigger><SelectContent>{clubs.map((c) => (<SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>))}</SelectContent></Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Transfer-Typ</label>
                    <Select value={formData.transfer_type} onValueChange={(v) => setFormData({ ...formData, transfer_type: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{TRANSFER_TYPES.map((t) => (<SelectItem key={t} value={t}>{t}</SelectItem>))}</SelectContent></Select>
                  </div>
                  <div><label className="block text-sm font-medium mb-1">Status</label>
                    <Select value={formData.status} onValueChange={(v) => setFormData({ ...formData, status: v })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{TRANSFER_STATUSES.map((s) => (<SelectItem key={s} value={s}>{s}</SelectItem>))}</SelectContent></Select>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div><label className="block text-sm font-medium mb-1">Ablöse</label><Input type="number" value={formData.fee_amount} onChange={(e) => setFormData({ ...formData, fee_amount: e.target.value })} /></div>
                  <div><label className="block text-sm font-medium mb-1">Währung</label><Input value={formData.fee_currency} onChange={(e) => setFormData({ ...formData, fee_currency: e.target.value })} /></div>
                  <div><label className="block text-sm font-medium mb-1">Saison</label><Input value={formData.season} onChange={(e) => setFormData({ ...formData, season: e.target.value })} placeholder="z.B. 2024/25" /></div>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Abbrechen</Button>
                  <Button type="submit" className="bg-[#79B92A] hover:bg-[#6aa325]">{editing ? "Aktualisieren" : "Erstellen"}</Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
        <div className="bg-white border border-gray-200">
          {loading ? <div className="p-8 text-center">Lädt...</div> : transfers.length === 0 ? <div className="p-8 text-center text-gray-500">Keine Transfers</div> : (
            <table className="admin-table w-full"><thead><tr><th>Spieler</th><th>Von</th><th>Zu</th><th>Typ</th><th>Status</th><th>Ablöse</th><th className="text-right">Aktionen</th></tr></thead>
              <tbody>{transfers.map((t) => (
                <tr key={t.id}>
                  <td className="font-medium">{getPlayerName(t.player_id)}</td>
                  <td>{getClubName(t.from_club_id)}</td>
                  <td>{getClubName(t.to_club_id)}</td>
                  <td><Badge variant="outline">{t.transfer_type}</Badge></td>
                  <td><Badge className={getStatusBadge(t.status)}>{t.status}</Badge></td>
                  <td>{t.fee_amount ? `${t.fee_amount.toLocaleString("de-DE")} ${t.fee_currency}` : "-"}</td>
                  <td className="text-right"><Button size="sm" variant="ghost" onClick={() => handleEdit(t)}><Pencil size={16} /></Button><Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(t.id)}><Trash size={16} /></Button></td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
