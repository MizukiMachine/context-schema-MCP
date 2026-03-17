interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

const menuItems = [
  { id: 'sessions', label: 'Sessions', icon: '📁' },
  { id: 'templates', label: 'Templates', icon: '📝' },
  { id: 'analytics', label: 'Analytics', icon: '📊' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export function Sidebar({ isOpen, onToggle }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-64 bg-white border-r border-gray-200
          transform transition-transform duration-200 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="p-4">
          <button
            onClick={onToggle}
            className="lg:hidden p-2 hover:bg-gray-100 rounded-md"
          >
            ✕
          </button>
        </div>

        <nav className="px-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-left hover:bg-gray-100 rounded-lg transition-colors"
            >
              <span>{item.icon}</span>
              <span className="text-gray-700">{item.label}</span>
            </button>
          ))}
        </nav>
      </aside>
    </>
  );
}
