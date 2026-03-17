import { useAuthStore } from '../../store';

export function Header() {
  const { user, isAuthenticated, logout } = useAuthStore();

  return (
    <header className="bg-white border-b border-gray-200 px-3 sm:px-6 py-3 sm:py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 sm:gap-4">
          <h1 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 truncate">
            Context Schema MCP
          </h1>
        </div>
        <nav className="flex items-center gap-2 sm:gap-4">
          {isAuthenticated ? (
            <div className="flex items-center gap-2 sm:gap-4">
              <span className="hidden sm:inline text-sm text-gray-600 truncate max-w-[120px] md:max-w-none">
                {user?.email || 'User'}
              </span>
              <button
                onClick={logout}
                className="min-h-[44px] px-3 sm:px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          ) : (
            <button className="min-h-[44px] px-4 sm:px-5 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition-colors">
              Login
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
