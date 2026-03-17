import { useState } from 'react';
import { Header } from '../components/layout/Header';
import { Sidebar } from '../components/layout/Sidebar';
import { useDashboardStore } from '../store';

export function Dashboard() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { currentSession, qualityScore, optimizationInProgress } = useDashboardStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <div className="flex">
        <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />

        <main className="flex-1 p-6">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden mb-4 p-2 bg-white rounded-md border border-gray-200"
          >
            ☰ Menu
          </button>

          {/* Session info */}
          {currentSession && (
            <div className="mb-6 p-4 bg-white rounded-lg border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">{currentSession.name}</h2>
              <p className="text-sm text-gray-500">Tokens: {currentSession.total_tokens}</p>
            </div>
          )}

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Panel */}
            <div className="p-6 bg-white rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Input Panel</h3>
              <p className="text-gray-500">Context input will be displayed here</p>
            </div>

            {/* Metrics Panel */}
            <div className="p-6 bg-white rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Metrics</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Quality Score</span>
                  <span className="font-semibold">{qualityScore}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Optimization</span>
                  <span className={optimizationInProgress ? 'text-yellow-600' : 'text-green-600'}>
                    {optimizationInProgress ? 'In Progress' : 'Idle'}
                  </span>
                </div>
              </div>
            </div>

            {/* Optimization Progress */}
            <div className="lg:col-span-2 p-6 bg-white rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Optimization Progress</h3>
              <p className="text-gray-500">Real-time optimization progress will be displayed here</p>
            </div>

            {/* Output Panel */}
            <div className="p-6 bg-white rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Output Panel</h3>
              <p className="text-gray-500">Optimized context will be displayed here</p>
            </div>

            {/* Savings Summary */}
            <div className="p-6 bg-white rounded-lg border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Savings Summary</h3>
              <p className="text-gray-500">Cost savings will be displayed here</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
