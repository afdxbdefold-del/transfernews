export function passwordError(currentPassword, newPassword, confirmation) {
  if (!currentPassword) return 'Bitte gib dein aktuelles Passwort ein.';
  if (Array.from(newPassword).length < 16) return 'Das neue Passwort muss mindestens 16 Zeichen haben.';
  if (new Blob([newPassword]).size > 72) return 'Das neue Passwort ist zu lang. Verwende weniger Sonderzeichen oder kürze es auf mindestens 16 Zeichen.';
  if (newPassword === currentPassword) return 'Wähle ein anderes Passwort als dein bisheriges.';
  if (newPassword !== confirmation) return 'Die neuen Passwörter stimmen nicht überein.';
  return '';
}
