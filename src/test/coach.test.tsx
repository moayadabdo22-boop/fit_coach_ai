import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { CoachPage } from '@/pages/Coach';

vi.mock('@/contexts/LanguageContext', () => ({
  useLanguage: () => ({
    language: 'en',
    t: (key: string) => key,
    dir: 'ltr',
    setLanguage: vi.fn(),
  }),
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'user-1' },
  }),
}));

vi.mock('@/contexts/UserContext', () => ({
  useUser: () => ({
    profile: {
      name: 'Test User',
      age: 25,
      gender: 'male',
      weight: 70,
      height: 175,
      goal: 'fitness',
      location: 'home',
      fitnessLevel: 'beginner',
      trainingDaysPerWeek: 3,
      equipment: '',
      injuries: '',
      activityLevel: 'moderate',
      dietaryPreferences: '',
      chronicConditions: '',
      allergies: '',
    },
  }),
}));

vi.mock('@/hooks/useVoiceChat', () => ({
  useVoiceChat: () => ({
    isListening: false,
    isProcessing: false,
    isSupported: false,
    error: null,
    clearError: vi.fn(),
    startListening: vi.fn(),
    stopListening: vi.fn(),
    cancelVoiceRequest: vi.fn(),
  }),
}));

vi.mock('@/components/layout/Navbar', () => ({
  Navbar: () => <div data-testid="navbar" />,
}));

vi.mock('@/components/ai/PlanApprovalUI', () => ({
  PlanApprovalUI: () => <div data-testid="plan-approval" />,
}));

const makeQuery = () => {
  const query: any = {};
  query.select = () => query;
  query.eq = () => query;
  query.order = () => query;
  query.maybeSingle = () => Promise.resolve({ data: null });
  query.insert = () => query;
  query.update = () => query;
  query.delete = () => query;
  query.not = () => query;
  query.like = () => query;
  query.single = () => Promise.resolve({ data: null });
  query.then = (resolve: (value: any) => any) => Promise.resolve({ data: [] }).then(resolve);
  return query;
};

vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    from: () => makeQuery(),
  },
}));

describe('CoachPage', () => {
  it('renders chat input', () => {
    render(
      <MemoryRouter>
        <CoachPage />
      </MemoryRouter>
    );

    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();
  });
});
