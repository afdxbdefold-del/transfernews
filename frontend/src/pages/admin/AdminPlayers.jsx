import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getPlayers, createPlayer, updatePlayer, deletePlayer } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, Pencil, Trash } from "@phosphor-icons/react";

export default function AdminPlayers() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    slug: "",
    country: "",
    position: "",
    birthdate: "",
    aliases: "",
  });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) {
      navigate("/admin/login");
      return;
    }
    fetchPlayers();
  }, [navigate]);

  const fetchPlayers = async () => {
    try {
      const res = await getPlayers({ limit: 100 });
      setPlayers(res.data);
    } catch (e) {
      console.error("Players error:", e);
    } finally {
      setLoading(false);
    }
  };

  const generateSlug = (name) => {
    return name
      .toLowerCase()
      .replace(/[äÄ]/g, "ae")
      .replace(/[öÖ]/g, "oe")
      .replace(/[üÜ]/g, "ue")
      .replace(/[ß]/g, "ss")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  };

  const resetForm = () => {
    setFormData({ name: "", slug: "", country: "", position: "", birthdate: "", aliases: "" });
    setEditingPlayer(null);
  };

  const handleEdit = (player) => {
    setEditingPlayer(player);
    setFormData({
      name: player.name || "",
      slug: player.slug || "",
      country: player.country || "",
      position: player.position || "",
      birthdate: player.birthdate || "",
      aliases: (player.aliases || []).join(", "),
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = {
      ...formData,
      slug: formData.slug || generateSlug(formData.name),
      aliases: formData.aliases ? formData.aliases.split(",").map((a) => a.trim()) : [],
    };

    try {
      if (editingPlayer) {
        await updatePlayer(editingPlayer.id, data);
        toast.success("Spieler aktualisiert");
      } else {
        await createPlayer(data);
        toast.success("Spieler erstellt");
      }
      setDialogOpen(false);
      resetForm();
      fetchPlayers();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Fehler beim Speichern");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Spieler wirklich löschen?")) return;
    try {
      await deletePlayer(id);
      toast.success("Spieler gelöscht");
      fetchPlayers();
    } catch (error) {
      toast.error("Fehler beim Löschen");
    }
  };

  return (
    <AdminLayout title="Spieler">
      <div data-testid="admin-players">
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-500">{players.length} Spieler</p>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={resetForm} className="bg-[#00a651] hover:bg-[#008c45]" data-testid="create-player-btn">
                <Plus size={18} className="mr-2" />
                Neuer Spieler
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="font-['Oswald'] uppercase">
                  {editingPlayer ? "Spieler bearbeiten" : "Neuer Spieler"}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Name *</label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    data-testid="player-name-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Slug</label>
                  <Input
                    value={formData.slug}
                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                    placeholder="auto-generiert wenn leer"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Land</label>
                    <Input
                      value={formData.country}
                      onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Position</label>
                    <Input
                      value={formData.position}
                      onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Geburtsdatum</label>
                  <Input
                    value={formData.birthdate}
                    onChange={(e) => setFormData({ ...formData, birthdate: e.target.value })}
                    placeholder="z.B. 1990-05-15"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Aliase (kommagetrennt)</label>
                  <Input
                    value={formData.aliases}
                    onChange={(e) => setFormData({ ...formData, aliases: e.target.value })}
                    placeholder="z.B. Messi, Leo, Lionel"
                  />
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Abbrechen
                  </Button>
                  <Button type="submit" className="bg-[#00a651] hover:bg-[#008c45]" data-testid="save-player-btn">
                    {editingPlayer ? "Aktualisieren" : "Erstellen"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="bg-white border border-gray-200">
          {loading ? (
            <div className="p-8 text-center">Lädt...</div>
          ) : players.length === 0 ? (
            <div className="p-8 text-center text-gray-500">Keine Spieler vorhanden</div>
          ) : (
            <table className="admin-table w-full">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Slug</th>
                  <th>Land</th>
                  <th>Position</th>
                  <th className="text-right">Aktionen</th>
                </tr>
              </thead>
              <tbody>
                {players.map((player) => (
                  <tr key={player.id}>
                    <td className="font-medium">{player.name}</td>
                    <td><code className="text-xs bg-gray-100 px-2 py-1 rounded">{player.slug}</code></td>
                    <td>{player.country || "-"}</td>
                    <td>{player.position || "-"}</td>
                    <td className="text-right">
                      <Button size="sm" variant="ghost" onClick={() => handleEdit(player)}>
                        <Pencil size={16} />
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDelete(player.id)}>
                        <Trash size={16} />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
