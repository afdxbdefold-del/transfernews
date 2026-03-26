import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AdminLayout from "@/components/AdminLayout";
import { getAdSlots, createAdSlot, updateAdSlot, deleteAdSlot } from "@/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Plus, Pencil, Trash, Eye, EyeSlash } from "@phosphor-icons/react";

const PAGE_TYPES = [
  { value: "all", label: "Alle Seiten" },
  { value: "homepage", label: "Startseite" },
  { value: "news_list", label: "News-Liste" },
  { value: "news_detail", label: "News-Detail" },
  { value: "player", label: "Spielerseite" },
  { value: "club", label: "Vereinsseite" },
  { value: "competition", label: "Wettbewerbsseite" },
  { value: "rumours", label: "Gerüchte" },
  { value: "transfers", label: "Transfers" },
  { value: "search", label: "Suche" },
  { value: "topic", label: "Themenseite" },
];

const DEVICE_TYPES = [
  { value: "all", label: "Alle Geräte" },
  { value: "desktop", label: "Desktop" },
  { value: "tablet", label: "Tablet" },
  { value: "mobile", label: "Mobile" },
];

export default function AdminAdSlots() {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSlot, setEditingSlot] = useState(null);
  const [formData, setFormData] = useState({
    name: "",
    slot_key: "",
    page_type: "all",
    position: "",
    device_type: "all",
    html_code: "",
    js_code: "",
    embed_code: "",
    is_active: true,
    priority: 0,
    feed_interval: null,
    notes: "",
  });
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    if (!token) {
      navigate("/admin/login");
      return;
    }
    fetchSlots();
  }, [navigate]);

  const fetchSlots = async () => {
    try {
      const res = await getAdSlots({ limit: 200 });
      setSlots(res.data);
    } catch (e) {
      console.error("Ad slots error:", e);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      slot_key: "",
      page_type: "all",
      position: "",
      device_type: "all",
      html_code: "",
      js_code: "",
      embed_code: "",
      is_active: true,
      priority: 0,
      feed_interval: null,
      notes: "",
    });
    setEditingSlot(null);
  };

  const handleEdit = (slot) => {
    setEditingSlot(slot);
    setFormData({
      name: slot.name || "",
      slot_key: slot.slot_key || "",
      page_type: slot.page_type || "all",
      position: slot.position || "",
      device_type: slot.device_type || "all",
      html_code: slot.html_code || "",
      js_code: slot.js_code || "",
      embed_code: slot.embed_code || "",
      is_active: slot.is_active ?? true,
      priority: slot.priority || 0,
      feed_interval: slot.feed_interval || null,
      notes: slot.notes || "",
    });
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingSlot) {
        await updateAdSlot(editingSlot.id, formData);
        toast.success("Ad-Slot aktualisiert");
      } else {
        await createAdSlot(formData);
        toast.success("Ad-Slot erstellt");
      }
      setDialogOpen(false);
      resetForm();
      fetchSlots();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Fehler beim Speichern");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Ad-Slot wirklich löschen?")) return;
    try {
      await deleteAdSlot(id);
      toast.success("Ad-Slot gelöscht");
      fetchSlots();
    } catch (error) {
      toast.error("Fehler beim Löschen");
    }
  };

  const toggleActive = async (slot) => {
    try {
      await updateAdSlot(slot.id, { is_active: !slot.is_active });
      fetchSlots();
      toast.success(slot.is_active ? "Ad-Slot deaktiviert" : "Ad-Slot aktiviert");
    } catch (error) {
      toast.error("Fehler beim Aktualisieren");
    }
  };

  // Group slots by page type
  const groupedSlots = slots.reduce((acc, slot) => {
    const key = slot.page_type || "all";
    if (!acc[key]) acc[key] = [];
    acc[key].push(slot);
    return acc;
  }, {});

  return (
    <AdminLayout title="Ad-Management">
      <div data-testid="admin-ad-slots">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-gray-500">
              {slots.length} Werbeslots • {slots.filter((s) => s.is_active).length} aktiv
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button
                onClick={resetForm}
                className="bg-[#00a651] hover:bg-[#008c45]"
                data-testid="create-slot-btn"
              >
                <Plus size={18} className="mr-2" />
                Neuer Ad-Slot
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="font-['Oswald'] text-xl uppercase">
                  {editingSlot ? "Ad-Slot bearbeiten" : "Neuer Ad-Slot"}
                </DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Name *</label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="z.B. Homepage Hero Banner"
                      required
                      data-testid="slot-name-input"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Slot-Key *</label>
                    <Input
                      value={formData.slot_key}
                      onChange={(e) => setFormData({ ...formData, slot_key: e.target.value })}
                      placeholder="z.B. homepage_hero_banner"
                      required
                      data-testid="slot-key-input"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Seitentyp</label>
                    <Select
                      value={formData.page_type}
                      onValueChange={(v) => setFormData({ ...formData, page_type: v })}
                    >
                      <SelectTrigger data-testid="page-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PAGE_TYPES.map((pt) => (
                          <SelectItem key={pt.value} value={pt.value}>
                            {pt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Gerätetyp</label>
                    <Select
                      value={formData.device_type}
                      onValueChange={(v) => setFormData({ ...formData, device_type: v })}
                    >
                      <SelectTrigger data-testid="device-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {DEVICE_TYPES.map((dt) => (
                          <SelectItem key={dt.value} value={dt.value}>
                            {dt.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Position</label>
                    <Input
                      value={formData.position}
                      onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                      placeholder="z.B. header_below"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Priorität</label>
                    <Input
                      type="number"
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Feed-Intervall</label>
                    <Input
                      type="number"
                      value={formData.feed_interval || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, feed_interval: e.target.value ? parseInt(e.target.value) : null })
                      }
                      placeholder="z.B. 4 (nach jedem 4. Item)"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">HTML-Code</label>
                  <Textarea
                    value={formData.html_code}
                    onChange={(e) => setFormData({ ...formData, html_code: e.target.value })}
                    placeholder="<div>Ihr Werbe-HTML...</div>"
                    rows={4}
                    className="font-mono text-sm"
                    data-testid="html-code-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">JavaScript-Code</label>
                  <Textarea
                    value={formData.js_code}
                    onChange={(e) => setFormData({ ...formData, js_code: e.target.value })}
                    placeholder="// Ihr JavaScript..."
                    rows={3}
                    className="font-mono text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Embed-Code (alternativ)</label>
                  <Textarea
                    value={formData.embed_code}
                    onChange={(e) => setFormData({ ...formData, embed_code: e.target.value })}
                    placeholder="<script>...</script> oder <iframe>...</iframe>"
                    rows={3}
                    className="font-mono text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Notizen</label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Interne Notizen..."
                    rows={2}
                  />
                </div>

                <div className="flex items-center gap-2">
                  <Switch
                    checked={formData.is_active}
                    onCheckedChange={(v) => setFormData({ ...formData, is_active: v })}
                    data-testid="is-active-switch"
                  />
                  <span className="text-sm">Aktiv</span>
                </div>

                <div className="flex justify-end gap-2 pt-4">
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                    Abbrechen
                  </Button>
                  <Button type="submit" className="bg-[#00a651] hover:bg-[#008c45]" data-testid="save-slot-btn">
                    {editingSlot ? "Aktualisieren" : "Erstellen"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Slots Table */}
        {loading ? (
          <div className="bg-white border p-8 text-center">Lädt...</div>
        ) : slots.length === 0 ? (
          <div className="bg-white border p-8 text-center text-gray-500">
            Keine Ad-Slots vorhanden. Klicke auf "Ad-Slots initialisieren" im Dashboard.
          </div>
        ) : (
          <div className="space-y-8">
            {Object.entries(groupedSlots).map(([pageType, pageSlots]) => {
              const pageLabel = PAGE_TYPES.find((pt) => pt.value === pageType)?.label || pageType;
              return (
                <div key={pageType} className="bg-white border border-gray-200">
                  <div className="bg-gray-50 px-4 py-3 border-b">
                    <h3 className="font-['Oswald'] text-lg font-bold uppercase">{pageLabel}</h3>
                    <p className="text-sm text-gray-500">{pageSlots.length} Slots</p>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="admin-table w-full">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Slot-Key</th>
                          <th>Geräte</th>
                          <th>Position</th>
                          <th>Status</th>
                          <th>Code</th>
                          <th className="text-right">Aktionen</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pageSlots.map((slot) => (
                          <tr key={slot.id}>
                            <td className="font-medium">{slot.name}</td>
                            <td>
                              <code className="text-xs bg-gray-100 px-2 py-1 rounded">{slot.slot_key}</code>
                            </td>
                            <td>
                              <Badge variant="outline" className="text-xs">
                                {DEVICE_TYPES.find((dt) => dt.value === slot.device_type)?.label || slot.device_type}
                              </Badge>
                            </td>
                            <td className="text-sm text-gray-500">{slot.position || "-"}</td>
                            <td>
                              <button
                                onClick={() => toggleActive(slot)}
                                className="flex items-center gap-1"
                                data-testid={`toggle-${slot.slot_key}`}
                              >
                                {slot.is_active ? (
                                  <Badge className="bg-green-100 text-green-800 hover:bg-green-200">
                                    <Eye size={12} className="mr-1" />
                                    Aktiv
                                  </Badge>
                                ) : (
                                  <Badge className="bg-gray-100 text-gray-600 hover:bg-gray-200">
                                    <EyeSlash size={12} className="mr-1" />
                                    Inaktiv
                                  </Badge>
                                )}
                              </button>
                            </td>
                            <td>
                              {(slot.html_code || slot.js_code || slot.embed_code) ? (
                                <Badge className="bg-blue-100 text-blue-800">Code hinterlegt</Badge>
                              ) : (
                                <Badge variant="outline" className="text-gray-400">Leer</Badge>
                              )}
                            </td>
                            <td className="text-right">
                              <div className="flex items-center justify-end gap-2">
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleEdit(slot)}
                                  data-testid={`edit-${slot.slot_key}`}
                                >
                                  <Pencil size={16} />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-red-500 hover:text-red-700"
                                  onClick={() => handleDelete(slot.id)}
                                  data-testid={`delete-${slot.slot_key}`}
                                >
                                  <Trash size={16} />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AdminLayout>
  );
}
