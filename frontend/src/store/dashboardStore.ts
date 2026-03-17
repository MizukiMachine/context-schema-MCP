import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Session, ContextWindow, Element, OptimizationTask } from '../types';

interface DashboardState {
  currentSession: Session | null;
  currentWindow: ContextWindow | null;
  elements: Element[];
  optimizationInProgress: boolean;
  optimizationTasks: OptimizationTask[];
  qualityScore: number;

  // Actions
  setCurrentSession: (session: Session | null) => void;
  setCurrentWindow: (window: ContextWindow | null) => void;
  setElements: (elements: Element[]) => void;
  addElement: (element: Element) => void;
  setOptimizationInProgress: (inProgress: boolean) => void;
  setOptimizationTasks: (tasks: OptimizationTask[]) => void;
  setQualityScore: (score: number) => void;
}

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set) => ({
      currentSession: null,
      currentWindow: null,
      elements: [],
      optimizationInProgress: false,
      optimizationTasks: [],
      qualityScore: 0,

      setCurrentSession: (session) => set({ currentSession: session }),
      setCurrentWindow: (window) => set({ currentWindow: window }),
      setElements: (elements) => set({ elements }),
      addElement: (element) => set((state) => ({ elements: [...state.elements, element] })),
      setOptimizationInProgress: (inProgress) => set({ optimizationInProgress: inProgress }),
      setOptimizationTasks: (tasks) => set({ optimizationTasks: tasks }),
      setQualityScore: (score) => set({ qualityScore: score }),
    }),
    { name: 'dashboard-store' }
  )
);
