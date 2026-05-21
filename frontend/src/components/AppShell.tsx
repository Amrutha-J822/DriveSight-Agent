import { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";
import { LogOut, Shield } from "lucide-react";

import { useAuth } from "../auth";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <div className="app-shell">
      <header className="app-topbar">
        <Link to="/" className="brand">
          <Shield size={20} />
          <span>
            DriveSight <em>Fleet Safety</em>
          </span>
        </Link>

        <nav className="app-nav">
          {user.role === "driver" && (
            <NavLink to="/" end>
              My dashboard
            </NavLink>
          )}
          {user.role === "reviewer" && (
            <>
              <NavLink to="/" end>
                Case queue
              </NavLink>
              <NavLink to="/upload">Upload</NavLink>
            </>
          )}
          {user.role === "manager" && (
            <>
              <NavLink to="/" end>
                Analytics
              </NavLink>
              <NavLink to="/queue">Cases</NavLink>
              <NavLink to="/escalations">Escalations</NavLink>
              <NavLink to="/drivers">Drivers</NavLink>
              <NavLink to="/users">Users</NavLink>
              <NavLink to="/upload">Upload</NavLink>
            </>
          )}
        </nav>

        <div className="user-chip">
          <div>
            <strong>{user.name}</strong>
            <small>{user.role}</small>
          </div>
          <button className="ghost-button" onClick={logout} title="Sign out">
            <LogOut size={16} />
          </button>
        </div>
      </header>

      <main className="app-main">{children}</main>
    </div>
  );
}
