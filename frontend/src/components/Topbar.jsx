import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Topbar({ title }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="flex items-center justify-between border-b border-border bg-surface/60 backdrop-blur px-6 py-4">
      <div>
        <h1 className="font-display font-semibold text-lg text-ink">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={toggleTheme}
          aria-label="Toggle dark and light mode"
          className="w-9 h-9 rounded-lg border border-border flex items-center justify-center text-ink-muted hover:text-signal hover:border-signal/40 transition-colors"
        >
          {theme === "dark" ? "☀" : "☾"}
        </button>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm text-ink leading-none">{user?.full_name}</p>
            <p className="text-[11px] text-ink-muted font-mono mt-0.5">
              {user?.company_name || "no company set"}
            </p>
          </div>
          <div className="w-9 h-9 rounded-full bg-signal/15 border border-signal/30 flex items-center justify-center text-signal font-display text-sm">
            {user?.full_name?.[0]?.toUpperCase() || "?"}
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="text-sm text-ink-muted hover:text-danger transition-colors"
        >
          Log out
        </button>
      </div>
    </header>
  );
}
