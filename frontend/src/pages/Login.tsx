import { useEffect, useState } from "react";
import { Shield } from "lucide-react";

import { listUsersForLogin } from "../api";
import { useAuth } from "../auth";
import type { User } from "../types";

export function LoginPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();

  useEffect(() => {
    listUsersForLogin()
      .then((list) => {
        setUsers(list);
        setSelectedId(list[0]?.id ?? "");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load users"));
  }, []);

  async function handleSubmit() {
    if (!selectedId) return;
    setSubmitting(true);
    setError(null);
    try {
      await login(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <header>
          <Shield size={32} />
          <h1>DriveSight Fleet Safety</h1>
          <p className="muted">
            Demo login — pick a seeded user to enter their portal. (Phase 2 will replace this with
            Firebase Google + Email/Password login.)
          </p>
        </header>

        {error && <div className="error-banner">{error}</div>}

        <div className="user-options">
          {users.map((user) => (
            <label key={user.id} className={selectedId === user.id ? "selected" : ""}>
              <input
                type="radio"
                name="user"
                value={user.id}
                checked={selectedId === user.id}
                onChange={() => setSelectedId(user.id)}
              />
              <div>
                <strong>{user.name}</strong>
                <small>
                  {user.role.toUpperCase()} · {user.email}
                </small>
              </div>
            </label>
          ))}
        </div>

        <button className="primary-button" onClick={handleSubmit} disabled={!selectedId || submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>

        <footer className="muted">
          Roles in this demo: <strong>reviewer</strong> approves/dismisses/escalates AI findings,{" "}
          <strong>manager</strong> sees analytics, <strong>driver</strong> sees their own score and
          coaching.
        </footer>
      </div>
    </div>
  );
}
