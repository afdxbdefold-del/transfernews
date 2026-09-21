import { act } from 'react';
import { createRoot } from 'react-dom/client';
import DynamicAdSlot, { AdSlotsProvider } from './DynamicAds';
import { getActiveAdSlots } from '../api';

let mockPath = '/';
jest.mock('react-router-dom', () => ({ useLocation: () => ({ pathname: mockPath }) }));
jest.mock('../api', () => ({ getActiveAdSlots: jest.fn() }));

test('resize and equivalent settings refresh keep one auction; navigation and disabling release it', async () => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  jest.useFakeTimers();
  window.innerWidth = 1440;
  const rect = jest.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockImplementation(() => ({ width: 728, height: 90 }));
  let enabled = true;
  getActiveAdSlots.mockImplementation(async () => ({ data: [{ slot_key: 'top_banner_above_header', is_active: enabled, page_type: 'all', device_type: 'all' }] }));
  const host = document.createElement('div');
  document.body.appendChild(host);
  const root = createRoot(host);
  const page = () => <AdSlotsProvider><DynamicAdSlot slotKey="top_banner_above_header" /><DynamicAdSlot slotKey="top_banner_above_header" /></AdSlotsProvider>;
  try {
    await act(async () => { root.render(page()); });
    await act(async () => { jest.advanceTimersByTime(201); });
    const original = host.querySelector('script[src*="requestform"]');
    expect(original).not.toBeNull();
    expect(host.querySelectorAll('[id="141912-1"]')).toHaveLength(1);
    await act(async () => {
      for (const width of [1430, 1360, 1000, 390, 395]) {
        window.innerWidth = width;
        window.dispatchEvent(new Event('resize'));
      }
      window.dispatchEvent(new Event('ad-slots-updated'));
      jest.advanceTimersByTime(400);
    });
    expect(host.querySelector('script[src*="requestform"]')).toBe(original);
    expect(host.querySelectorAll('script[src*="requestform"]')).toHaveLength(1);
    mockPath = '/news/next';
    await act(async () => { root.render(page()); jest.advanceTimersByTime(400); });
    await act(async () => { jest.advanceTimersByTime(201); });
    expect(original.isConnected).toBe(false);
    expect(host.querySelectorAll('script[src*="requestform"]')).toHaveLength(1);
    enabled = false;
    await act(async () => { window.dispatchEvent(new Event('ad-slots-updated')); });
    expect(host.querySelectorAll('script[src*="requestform"]')).toHaveLength(0);
    mockPath = '/datenschutz';
    await act(async () => { root.render(page()); });
    expect(host.querySelector('.managed-ad-slot')).toBeNull();
  } finally {
    await act(async () => { root.unmount(); });
    host.remove();
    rect.mockRestore();
    jest.useRealTimers();
    mockPath = '/';
    delete global.IS_REACT_ACT_ENVIRONMENT;
  }
});
