import { describe, expect, it } from 'vitest';
import type { TradeState } from '@kairox/shared';

const VALID_TRANSITIONS: Record<TradeState, TradeState[]> = {
  idle: ['pre_started', 'pending_funds'],
  pre_started: ['running', 'cancelled'],
  pending_funds: ['ready', 'cancelled'],
  ready: ['running', 'cancelled'],
  running: ['settling', 'failed'],
  settling: ['completed', 'failed'],
  completed: [],
  failed: [],
  cancelled: [],
};

function canTransition(current: TradeState, target: TradeState): boolean {
  return VALID_TRANSITIONS[current]?.includes(target) ?? false;
}

describe('trade state machine contract (mirrors backend)', () => {
  it('blocks idle to running bypass', () => {
    expect(canTransition('idle', 'running')).toBe(false);
  });

  it('allows pre-start to running', () => {
    expect(canTransition('pre_started', 'running')).toBe(true);
  });

  it('completed is terminal', () => {
    expect(canTransition('completed', 'running')).toBe(false);
  });
});
