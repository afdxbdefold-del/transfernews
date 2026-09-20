import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import AdminLayout from '@/components/AdminLayout';
import { changePassword } from '@/api';
import { passwordError } from '@/lib/passwordValidation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function AdminPassword() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const secure = window.location.protocol === 'https:' || ['localhost', '127.0.0.1'].includes(window.location.hostname);
  if (!localStorage.getItem('adminToken')) return <Navigate to="/admin/login" replace />;

  const submit = async event => {
    event.preventDefault();
    const validation = passwordError(currentPassword, newPassword, confirmation);
    if (validation) { setError(validation); return; }
    if (!secure) { setError('Öffne diese Seite über HTTPS, bevor du dein Passwort änderst.'); return; }
    setPending(true); setError(''); setSuccess(false);
    try {
      const { data } = await changePassword(currentPassword, newPassword);
      localStorage.removeItem('adminToken');
      if (data.access_token) localStorage.setItem('adminToken', data.access_token);
      setCurrentPassword(''); setNewPassword(''); setConfirmation(''); setSuccess(true);
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === 'string' ? requestError.response.data.detail : 'Das Passwort konnte nicht geändert werden. Bitte versuche es erneut.');
    } finally { setPending(false); }
  };

  return <AdminLayout title="Passwort ändern">
    <div className="max-w-xl bg-white border border-gray-200 rounded p-6">
      <p className="text-gray-600 mb-6">Wähle ein neues Passwort mit mindestens 16 Zeichen. Nach der Änderung werden alle anderen Sitzungen abgemeldet.</p>
      {!secure && <p role="alert" className="text-red-700 mb-4">Für den Passwortwechsel ist eine HTTPS-Verbindung erforderlich.</p>}
      {success && <p role="status" className="text-green-800 bg-green-50 p-3 mb-4">Dein Passwort wurde geändert. Andere Sitzungen sind jetzt abgemeldet.</p>}
      {error && <p role="alert" className="text-red-700 bg-red-50 p-3 mb-4">{error}</p>}
      <form onSubmit={submit} className="space-y-5">
        <div><label htmlFor="current-password" className="block text-sm font-medium mb-1">Aktuelles Passwort</label><Input id="current-password" type="password" autoComplete="current-password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required disabled={pending || !secure} /></div>
        <div><label htmlFor="new-password" className="block text-sm font-medium mb-1">Neues Passwort</label><Input id="new-password" type="password" autoComplete="new-password" minLength={16} maxLength={72} value={newPassword} onChange={e => setNewPassword(e.target.value)} required disabled={pending || !secure} /></div>
        <div><label htmlFor="confirm-password" className="block text-sm font-medium mb-1">Neues Passwort bestätigen</label><Input id="confirm-password" type="password" autoComplete="new-password" minLength={16} maxLength={72} value={confirmation} onChange={e => setConfirmation(e.target.value)} required disabled={pending || !secure} /></div>
        <Button type="submit" disabled={pending || !secure}>{pending ? 'Wird gespeichert …' : 'Passwort ändern'}</Button>
      </form>
    </div>
  </AdminLayout>;
}
