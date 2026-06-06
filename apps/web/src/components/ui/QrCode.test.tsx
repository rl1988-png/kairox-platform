import { describe, expect, it } from 'vitest';

describe('QrCode module', () => {
  it('exports QrCode component', async () => {
    const mod = await import('./QrCode');
    expect(typeof mod.QrCode).toBe('function');
  });
});
