import React, { useState } from "react";
import { createGroup } from "../api/client";

const initialForm = {
  name: "",
  org: "",
  data_character: "",
  hardware_desc: "",
  software_desc: "",
  processing_degree: "",
  capture_points: 1,
  capture_start: "",
  capture_end: "",
};

export default function CreateGroupForm({ onCreated }) {
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");

  async function submit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);

    try {
      const payload = {
        name: form.name.trim(),
        org: form.org.trim(),
        data_character: form.data_character.trim(),
        hardware_desc: form.hardware_desc.trim(),
        software_desc: form.software_desc.trim(),
        processing_degree: form.processing_degree.trim(),
        capture_points: Number(form.capture_points),
        capture_start: form.capture_start
          ? new Date(form.capture_start).toISOString()
          : null,
        capture_end: form.capture_end
          ? new Date(form.capture_end).toISOString()
          : null,
      };

      const group = await createGroup(payload);

      setSuccess(`Группа создана: ${group.name} (ID ${group.id})`);
      setForm(initialForm);
      onCreated?.(group);
    } catch (e) {
      setError(e.message || "Ошибка при создании группы");
    } finally {
      setSaving(false);
    }
  }

  function change(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  return (
    <div className="upload-card">
      <div className="section-header">
        <div>
          <h2 className="section-title">Создание группы трасс</h2>
          <p className="section-subtitle">
            Сначала создайте группу, затем загрузите описание, схему и сами трассы.
          </p>
        </div>
      </div>

      <form onSubmit={submit} className="upload-grid">
        <label className="form-field">
          <span className="form-label">Название группы</span>
          <input
            className="input"
            placeholder="Например: Трассы Wi-Fi кампуса, июль 2025"
            value={form.name}
            onChange={(e) => change("name", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Организация</span>
          <input
            className="input"
            placeholder="Например: МГУ"
            value={form.org}
            onChange={(e) => change("org", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Характер данных</span>
          <input
            className="input"
            placeholder="Например: L2 traffic"
            value={form.data_character}
            onChange={(e) => change("data_character", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Описание аппаратуры</span>
          <textarea
            className="input textarea"
            rows={3}
            value={form.hardware_desc}
            onChange={(e) => change("hardware_desc", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Описание ПО сбора</span>
          <textarea
            className="input textarea"
            rows={3}
            value={form.software_desc}
            onChange={(e) => change("software_desc", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Степень обработки данных</span>
          <textarea
            className="input textarea"
            rows={3}
            value={form.processing_degree}
            onChange={(e) => change("processing_degree", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Начало сбора</span>
          <input
            className="input"
            type="datetime-local"
            value={form.capture_start}
            onChange={(e) => change("capture_start", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Конец сбора</span>
          <input
            className="input"
            type="datetime-local"
            value={form.capture_end}
            onChange={(e) => change("capture_end", e.target.value)}
            required
          />
        </label>

        <label className="form-field">
          <span className="form-label">Число точек сбора</span>
          <select
            className="input"
            value={form.capture_points}
            onChange={(e) => change("capture_points", e.target.value)}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
          </select>
        </label>

        <div className="form-actions form-field-full">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Создание..." : "Создать группу"}
          </button>
        </div>

        {success ? <div className="alert alert-success form-field-full">{success}</div> : null}
        {error ? <div className="alert alert-error form-field-full">{error}</div> : null}
      </form>
    </div>
  );
}