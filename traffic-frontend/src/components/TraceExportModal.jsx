import React, { useEffect, useMemo, useState } from "react";

function pad(value) {
  return String(value).padStart(2, "0");
}

function parseDateTime(sourceValue) {
  if (!sourceValue) {
    const now = new Date();
    return {
      date: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`,
      time: "00:00:00",
    };
  }

  const clean = String(sourceValue).replace("Z", "");
  const [datePart, timePart = "00:00:00"] = clean.split("T");

  return {
    date: datePart,
    time: timePart.slice(0, 8),
  };
}

function toIso(date, time) {
  const normalizedTime = time.length === 5 ? `${time}:00` : time;
  return `${date}T${normalizedTime}`;
}

export default function TraceExportModal({
  open,
  title,
  fromValue,
  toValue,
  busy = false,
  onClose,
  onSubmit,
}) {
  const initialFrom = useMemo(() => parseDateTime(fromValue), [fromValue]);
  const initialTo = useMemo(() => parseDateTime(toValue), [toValue]);

  const [fromDate, setFromDate] = useState(initialFrom.date);
  const [fromTime, setFromTime] = useState(initialFrom.time);
  const [toDate, setToDate] = useState(initialTo.date);
  const [toTime, setToTime] = useState(initialTo.time);
  const [showDateFields, setShowDateFields] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setFromDate(initialFrom.date);
    setFromTime(initialFrom.time);
    setToDate(initialTo.date);
    setToTime(initialTo.time);
    setShowDateFields(false);
    setError("");
  }, [initialFrom, initialTo, open]);

  if (!open) return null;

  function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const t_from = toIso(fromDate, fromTime);
    const t_to = toIso(toDate, toTime);

    if (t_from > t_to) {
      setError("Начало интервала должно быть не позже конца.");
      return;
    }

    onSubmit({ t_from, t_to });
  }

  return (
    <div className="modal-overlay" onClick={busy ? undefined : onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            disabled={busy}
          >
            ✕
          </button>
        </div>

        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="modal-grid-2">
            <label className="form-label">
              Время начала
              <input
                className="input"
                type="time"
                step="1"
                value={fromTime}
                onChange={(e) => setFromTime(e.target.value)}
                required
              />
            </label>

            <label className="form-label">
              Время конца
              <input
                className="input"
                type="time"
                step="1"
                value={toTime}
                onChange={(e) => setToTime(e.target.value)}
                required
              />
            </label>
          </div>

          <button
            type="button"
            className="modal-link-btn"
            onClick={() => setShowDateFields((prev) => !prev)}
          >
            {showDateFields ? "Скрыть дату" : "Показать и изменить дату"}
          </button>

          {showDateFields && (
            <div className="modal-grid-2">
              <label className="form-label">
                Дата начала
                <input
                  className="input"
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  required
                />
              </label>

              <label className="form-label">
                Дата конца
                <input
                  className="input"
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  required
                />
              </label>
            </div>
          )}

          {error ? <div className="alert alert-error">{error}</div> : null}

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={busy}
            >
              Отмена
            </button>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? "Подготовка..." : "Скачать"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}