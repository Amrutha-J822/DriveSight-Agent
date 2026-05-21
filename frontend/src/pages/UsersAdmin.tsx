import { useEffect, useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";

import { createUser, deleteUser, listDrivers, listUsersForLogin, updateUser } from "../api";
import { useAuth } from "../auth";
import type { Driver, Role, User } from "../types";

type Form = { name: string; email: string; role: Role; driver_id: string };
const EMPTY: Form = { name: "", email: "", role: "reviewer", driver_id: "" };

export function UsersAdminPage() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<Form>(EMPTY);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const [u, d] = await Promise.all([listUsersForLogin(), listDrivers()]);
      setUsers(u);
      setDrivers(d);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load users");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function startEdit(user: User) {
    setEditing(user.id);
    setShowCreate(false);
    setForm({
      name: user.name,
      email: user.email,
      role: user.role,
      driver_id: user.driver_id ?? "",
    });
  }

  function startCreate() {
    setEditing(null);
    setShowCreate(true);
    setForm(EMPTY);
  }

  function cancel() {
    setEditing(null);
    setShowCreate(false);
    setForm(EMPTY);
  }

  async function save() {
    try {
      const payload = {
        name: form.name.trim(),
        email: form.email.trim(),
        role: form.role,
        driver_id: form.role === "driver" ? form.driver_id || null : null,
      };
      if (form.role === "driver" && !payload.driver_id) {
        setError("Driver accounts must be linked to an existing driver profile.");
        return;
      }
      if (editing) {
        await updateUser(editing, payload);
      } else {
        await createUser(payload);
      }
      cancel();
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed");
    }
  }

  async function remove(userId: string) {
    if (!window.confirm("Delete this user account?")) return;
    try {
      await deleteUser(userId);
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Delete failed");
    }
  }

  const showForm = editing !== null || showCreate;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Manager · users</p>
          <h1>User accounts &amp; roles</h1>
          <p className="muted">
            Create reviewer, manager, and driver accounts. Driver accounts must be linked to a driver
            profile so the person sees their own data.
          </p>
        </div>
        {!showForm && (
          <button className="primary-button" onClick={startCreate}>
            <Plus size={16} /> Add user
          </button>
        )}
      </header>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <section className="admin-form">
          <h3>{editing ? "Edit user" : "New user"}</h3>
          <label>
            <span>Name</span>
            <input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="e.g. Sarah Chen"
            />
          </label>
          <label>
            <span>Email</span>
            <input
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
              placeholder="e.g. sarah@yourfleet.com"
            />
          </label>
          <label>
            <span>Role</span>
            <select
              value={form.role}
              onChange={(event) => setForm({ ...form, role: event.target.value as Role })}
            >
              <option value="reviewer">Reviewer — approves AI findings</option>
              <option value="manager">Manager — full access</option>
              <option value="driver">Driver — sees only own data</option>
            </select>
          </label>
          {form.role === "driver" && (
            <label>
              <span>Linked driver profile</span>
              <select
                value={form.driver_id}
                onChange={(event) => setForm({ ...form, driver_id: event.target.value })}
              >
                <option value="">— pick a driver —</option>
                {drivers.map((driver) => (
                  <option key={driver.id} value={driver.id}>
                    {driver.name} ({driver.employee_id})
                  </option>
                ))}
              </select>
            </label>
          )}
          <div className="form-actions">
            <button className="ghost-button" onClick={cancel}>
              Cancel
            </button>
            <button
              className="primary-button"
              onClick={save}
              disabled={!form.name.trim() || !form.email.trim()}
            >
              {editing ? "Save changes" : "Create user"}
            </button>
          </div>
        </section>
      )}

      <section>
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Linked driver</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const linkedDriver = drivers.find((d) => d.id === user.driver_id);
              const isMe = me?.id === user.id;
              const isDemoSeed = user.email.endsWith("@fleet.demo");
              return (
                <tr key={user.id}>
                  <td>
                    {user.name}
                    {isMe && <span className="muted"> (you)</span>}
                    {isDemoSeed && <span className="pill" style={{ marginLeft: 8 }}>DEMO</span>}
                  </td>
                  <td>{user.email}</td>
                  <td style={{ textTransform: "capitalize" }}>{user.role}</td>
                  <td>{linkedDriver?.name ?? "—"}</td>
                  <td className="row-actions">
                    <button className="ghost-button" onClick={() => startEdit(user)}>
                      <Pencil size={14} />
                    </button>
                    <button
                      className="ghost-button danger"
                      onClick={() => remove(user.id)}
                      disabled={isMe}
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
