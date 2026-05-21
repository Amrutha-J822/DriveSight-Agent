import { useEffect, useState } from "react";
import { Pencil, Plus, Trash2 } from "lucide-react";

import { createDriver, deleteDriver, listDrivers, updateDriver } from "../api";
import type { Driver } from "../types";

type Form = { name: string; employee_id: string; vehicle_id: string };
const EMPTY: Form = { name: "", employee_id: "", vehicle_id: "" };

export function DriversAdminPage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<Form>(EMPTY);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setDrivers(await listDrivers());
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Failed to load drivers");
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function startEdit(driver: Driver) {
    setEditing(driver.id);
    setShowCreate(false);
    setForm({
      name: driver.name,
      employee_id: driver.employee_id,
      vehicle_id: driver.vehicle_id ?? "",
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
        employee_id: form.employee_id.trim(),
        vehicle_id: form.vehicle_id.trim() || undefined,
      };
      if (editing) {
        await updateDriver(editing, payload);
      } else {
        await createDriver(payload);
      }
      cancel();
      await refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Save failed");
    }
  }

  async function remove(driverId: string) {
    if (!window.confirm("Delete this driver? Cases linked to them will block deletion.")) return;
    try {
      await deleteDriver(driverId);
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
          <p className="eyebrow">Manager · drivers</p>
          <h1>Driver management</h1>
          <p className="muted">Create real driver profiles for your fleet.</p>
        </div>
        {!showForm && (
          <button className="primary-button" onClick={startCreate}>
            <Plus size={16} /> Add driver
          </button>
        )}
      </header>

      {error && <div className="error-banner">{error}</div>}

      {showForm && (
        <section className="admin-form">
          <h3>{editing ? "Edit driver" : "New driver"}</h3>
          <label>
            <span>Name</span>
            <input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="e.g. John Smith"
            />
          </label>
          <label>
            <span>Employee ID</span>
            <input
              value={form.employee_id}
              onChange={(event) => setForm({ ...form, employee_id: event.target.value })}
              placeholder="e.g. EMP-1042"
            />
          </label>
          <label>
            <span>Vehicle ID</span>
            <input
              value={form.vehicle_id}
              onChange={(event) => setForm({ ...form, vehicle_id: event.target.value })}
              placeholder="e.g. VAN-102 (optional)"
            />
          </label>
          <div className="form-actions">
            <button className="ghost-button" onClick={cancel}>
              Cancel
            </button>
            <button
              className="primary-button"
              onClick={save}
              disabled={!form.name.trim() || !form.employee_id.trim()}
            >
              {editing ? "Save changes" : "Create driver"}
            </button>
          </div>
        </section>
      )}

      <section>
        <table className="data-table">
          <thead>
            <tr>
              <th>Driver</th>
              <th>Employee</th>
              <th>Vehicle</th>
              <th>Risk</th>
              <th>Cases</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((driver) => (
              <tr key={driver.id}>
                <td>{driver.name}</td>
                <td>{driver.employee_id}</td>
                <td>{driver.vehicle_id ?? "—"}</td>
                <td>{driver.risk_score}</td>
                <td>
                  {driver.approved_events}A · {driver.dismissed_events}D · {driver.escalated_events}E
                </td>
                <td className="row-actions">
                  <button className="ghost-button" onClick={() => startEdit(driver)}>
                    <Pencil size={14} />
                  </button>
                  <button className="ghost-button danger" onClick={() => remove(driver.id)}>
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
            {drivers.length === 0 && (
              <tr>
                <td colSpan={6} className="muted" style={{ textAlign: "center" }}>
                  No drivers yet. Click "Add driver" to create one.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
