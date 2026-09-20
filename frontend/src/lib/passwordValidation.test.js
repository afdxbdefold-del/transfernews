import { passwordError } from './passwordValidation';
test('requires the current password, sixteen characters and matching confirmation', () => {
  expect(passwordError('', 'a new long password', 'a new long password')).not.toBe('');
  expect(passwordError('previous', 'short', 'short')).not.toBe('');
  expect(passwordError('previous', 'a new long password', 'different')).not.toBe('');
  expect(passwordError('previous', 'a new long password', 'a new long password')).toBe('');
});
test('rejects unchanged passwords and passwords exceeding bcrypt UTF-8 capacity', () => {
  expect(passwordError('a previous password', 'a previous password', 'a previous password')).not.toBe('');
  expect(passwordError('previous', 'ü'.repeat(37), 'ü'.repeat(37))).not.toBe('');
  expect(passwordError('previous', 'ü'.repeat(16), 'ü'.repeat(16))).toBe('');
});
