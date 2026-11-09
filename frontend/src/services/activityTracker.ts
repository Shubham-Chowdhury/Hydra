/**
 * User Activity and Exploration Tracker for Hydra.
 *
 * Silently logs student navigational choices, simulation runs, parameter adjustments,
 * and conversational inquiries into an auditable event stream.
 * This event stream feeds into Hydra's Deep Trajectory Sequence Model for
 * career readiness scoring and personalized pathway synthesis.
 */

import type { UserInteractionEventDto } from '../api/types';

class ActivityTracker {
  private events: UserInteractionEventDto[] = [];
  private maxEvents = 100;

  constructor() {
    this.initFromStorage();
  }

  private initFromStorage() {
    try {
      const stored = sessionStorage.getItem('hydra_interaction_history');
      if (stored) {
        this.events = JSON.parse(stored);
      }
    } catch {
      this.events = [];
    }
  }

  private saveToStorage() {
    try {
      sessionStorage.setItem('hydra_interaction_history', JSON.stringify(this.events.slice(-this.maxEvents)));
    } catch {}
  }

  public trackEvent(
    eventType: string,
    targetId?: string,
    domain?: string,
    metadata?: Record<string, any>
  ): UserInteractionEventDto {
    const event: UserInteractionEventDto = {
      event_id: `evt_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      event_type: eventType,
      timestamp: new Date().toISOString(),
      target_id: targetId,
      domain: domain,
      metadata: metadata || {},
    };

    this.events.push(event);
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }
    this.saveToStorage();
    return event;
  }

  public getHistory(): UserInteractionEventDto[] {
    return [...this.events];
  }

  public clearHistory(): void {
    this.events = [];
    try {
      sessionStorage.removeItem('hydra_interaction_history');
    } catch {}
  }
}

export const activityTracker = new ActivityTracker();

