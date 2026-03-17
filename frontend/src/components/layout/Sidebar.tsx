interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
}

const menuItems = [
  { id: 'sessions', label: 'Sessions', icon: '📁' },
  { id: 'templates', label: 'Templates', icon: '📝' },
  { id: 'analytics', label: 'Analytics', icon: '📊' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export function Sidebar({ isOpen, onToggle, onClose }: SidebarProps) {
  return (
    <>
      {isOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="fixed inset-0 z-30 bg-slate-950/40 backdrop-blur-[1px] lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        id="dashboard-sidebar"
        className={`
          fixed inset-y-0 left-0 z-40
          w-72 max-w-[85vw] border-r border-gray-200 bg-white shadow-xl
          transform transition-transform duration-300 ease-out
          lg:sticky lg:top-0 lg:z-10 lg:h-[calc(100vh-73px)] lg:max-w-none lg:translate-x-0 lg:shadow-none
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex items-center justify-between border-b border-gray-100 px-4 py-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-slate-500">
              Navigation
            </p>
            <p className="mt-1 text-base font-semibold text-slate-900">Dashboard Menu</p>
          </div>
          <button
            type="button"
            onClick={onToggle}
            className="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-xl text-slate-600 transition hover:bg-gray-100 lg:hidden"
            aria-label="Close menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <nav className="space-y-1 p-3">
          {menuItems.map((item) => (
            <button
              type="button"
              key={item.id}
              onClick={onClose}
              className="flex min-h-[48px] w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 active:bg-gray-200 sm:text-[15px]"
            >
              <span className="text-xl">{item.icon}</span>
              <span className="text-gray-700 font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>
    </>
  );
}
