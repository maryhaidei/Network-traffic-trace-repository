import React, { useMemo, useState } from "react";
import {
  downloadLabeledTrace,
  downloadRawTrace,
  exportLabeledTraceSegment,
  exportRawTraceSegment,
  getRawTrace,
  searchLabeledTraces,
  searchRawTraces,
} from "../api/client";
import TraceExportModal from "../components/TraceExportModal";

export default function GroupsPage() {
  const [tab, setTab] = useState("raw");
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);

  const [exportModal, setExportModal] = useState({
    open: false,
    type: null,
    traceId: null,
    title: "",
    fromValue: "",
    toValue: "",
  });

  const rawDefault = useMemo(
    () => ({
      org: "",
      data_character: "",
      hardware_desc: "",
      software_desc: "",
      capture_points: "",
      from_ts: "",
      to_ts: "",
    }),
    []
  );

  const labeledDefault = useMemo(
    () => ({
      kind: "",
      donor_raw_trace_id: "",
      software_desc: "",
      from_ts: "",
      to_ts: "",
    }),
    []
  );

  const [rawFilters, setRawFilters] = useState(rawDefault);
  const [labeledFilters, setLabeledFilters] = useState(labeledDefault);

  const rawDirty = JSON.stringify(rawFilters) !== JSON.stringify(rawDefault);
  const labeledDirty = JSON.stringify(labeledFilters) !== JSON.stringify(labeledDefault);

  async function handleSearch() {
    setError("");
    setLoading(true);

    try {
      const data =
        tab === "raw"
          ? await searchRawTraces({ ...rawFilters, limit: 50 })
          : await searchLabeledTraces({ ...labeledFilters, limit: 50 });

      setItems(Array.isArray(data) ? data : []);
      setHasSearched(true);
    } catch (e) {
      setItems([]);
      setHasSearched(true);
      setError(e?.message || "Ошибка поиска");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    const dirty = tab === "raw" ? rawDirty : labeledDirty;
    if (!dirty && !hasSearched) return;

    if (tab === "raw") {
      setRawFilters(rawDefault);
    } else {
      setLabeledFilters(labeledDefault);
    }

    setItems([]);
    setHasSearched(false);
    setError("");
  }

  function openRawExportModal(item) {
    setExportModal({
      open: true,
      type: "raw",
      traceId: item.id,
      title: `Скачать фрагмент сетевой трассы #${item.id}`,
      fromValue: item.t_min || "",
      toValue: item.t_max || "",
    });
  }

  function openLabeledExportModal(item) {
    setExportModal({
      open: true,
      type: "labeled",
      traceId: item.id,
      title: `Скачать фрагмент трассы показателей сети #${item.id}`,
      fromValue: item.t_from || "",
      toValue: item.t_to || "",
    });
  }

  function closeExportModal() {
    setExportModal({
      open: false,
      type: null,
      traceId: null,
      title: "",
      fromValue: "",
      toValue: "",
    });
  }

  async function handleExportSubmit({ t_from, t_to }) {
    try {
      if (exportModal.type === "raw") {
        await exportRawTraceSegment(exportModal.traceId, t_from, t_to);
      } else {
        await exportLabeledTraceSegment(exportModal.traceId, t_from, t_to);
      }
      closeExportModal();
    } catch (e) {
      setError(e?.message || "Ошибка экспорта фрагмента");
    }
  }

  async function handleFindRawByLabeled(rawTraceId) {
    try {
      const rawTrace = await getRawTrace(rawTraceId);
      setTab("raw");
      setRawFilters(rawDefault);
      setItems([rawTrace]);
      setHasSearched(true);
      setError("");
    } catch (e) {
      setError(e?.message || "Не удалось найти сетевую трассу");
    }
  }

  async function handleFindLabeledByRaw(rawTraceId) {
    setError("");
    setLoading(true);

    const nextFilters = {
      ...labeledDefault,
      donor_raw_trace_id: String(rawTraceId),
    };

    try {
      const data = await searchLabeledTraces({ ...nextFilters, limit: 50 });
      setTab("labeled");
      setLabeledFilters(nextFilters);
      setItems(Array.isArray(data) ? data : []);
      setHasSearched(true);
    } catch (e) {
      setTab("labeled");
      setLabeledFilters(nextFilters);
      setItems([]);
      setHasSearched(true);
      setError(e?.message || "Не удалось найти трассы");
    } finally {
      setLoading(false);
    }
  }

  function switchToRawTab() {
    setTab("raw");
    setItems([]);
    setHasSearched(false);
    setError("");
  }

  function switchToLabeledTab() {
    setTab("labeled");
    setItems([]);
    setHasSearched(false);
    setError("");
  }

  return (
    <div className="page-grid">
      <section className="hero-card">
        <div>
          <h2 className="hero-title">Поиск по репозиторию трасс</h2>
          <p className="hero-text">
            Выполняйте поиск по трассам, переходите между
            связанными объектами и выгружайте полные файлы или временные фрагменты.
          </p>
        </div>
      </section>

      <section className="card">
        <div className="section-header">
          <div className="section-title">Параметры поиска</div>
          <div className="tab-switcher">
            <button
              className={tab === "raw" ? "tab-btn active" : "tab-btn"}
              type="button"
              onClick={switchToRawTab}
            >
              Сетевые трассы
            </button>

            <button
              className={tab === "labeled" ? "tab-btn active" : "tab-btn"}
              type="button"
              onClick={switchToLabeledTab}
            >
               Трассы показателей сети
            </button>
          </div>
        </div>

        {tab === "raw" && (
          <div className="filters-grid">
            <input
              className="input"
              placeholder="Организация"
              value={rawFilters.org}
              onChange={(e) => setRawFilters({ ...rawFilters, org: e.target.value })}
            />
            <input
              className="input"
              placeholder="Характер данных"
              value={rawFilters.data_character}
              onChange={(e) =>
                setRawFilters({ ...rawFilters, data_character: e.target.value })
              }
            />
            <input
              className="input"
              placeholder="Аппаратура"
              value={rawFilters.hardware_desc}
              onChange={(e) =>
                setRawFilters({ ...rawFilters, hardware_desc: e.target.value })
              }
            />
            <input
              className="input"
              placeholder="ПО сбора"
              value={rawFilters.software_desc}
              onChange={(e) =>
                setRawFilters({ ...rawFilters, software_desc: e.target.value })
              }
            />
            <select
              className="input"
              value={rawFilters.capture_points}
              onChange={(e) =>
                setRawFilters({ ...rawFilters, capture_points: e.target.value })
              }
            >
              <option value="">Точки сбора: любые</option>
              <option value="1">1 точка</option>
              <option value="2">2 точки</option>
            </select>
            <input
              className="input"
              type="datetime-local"
              value={rawFilters.from_ts}
              onChange={(e) => setRawFilters({ ...rawFilters, from_ts: e.target.value })}
            />
            <input
              className="input"
              type="datetime-local"
              value={rawFilters.to_ts}
              onChange={(e) => setRawFilters({ ...rawFilters, to_ts: e.target.value })}
            />
          </div>
        )}

        {tab === "labeled" && (
          <div className="filters-grid">
            <select
              className="input"
              value={labeledFilters.kind}
              onChange={(e) =>
                setLabeledFilters({ ...labeledFilters, kind: e.target.value })
              }
            >
              <option value="">Тип разметки: любая</option>
              <option value="qos">QoS ряды</option>
              <option value="mac_intensity">Ряды мак-интенсивности</option>
            </select>

            <input
              className="input"
              placeholder="ID донорской трассы"
              value={labeledFilters.donor_raw_trace_id}
              onChange={(e) =>
                setLabeledFilters({
                  ...labeledFilters,
                  donor_raw_trace_id: e.target.value,
                })
              }
            />

            <input
              className="input"
              placeholder="ПО разметки"
              value={labeledFilters.software_desc}
              onChange={(e) =>
                setLabeledFilters({
                  ...labeledFilters,
                  software_desc: e.target.value,
                })
              }
            />

            <input
              className="input"
              type="datetime-local"
              value={labeledFilters.from_ts}
              onChange={(e) =>
                setLabeledFilters({ ...labeledFilters, from_ts: e.target.value })
              }
            />

            <input
              className="input"
              type="datetime-local"
              value={labeledFilters.to_ts}
              onChange={(e) =>
                setLabeledFilters({ ...labeledFilters, to_ts: e.target.value })
              }
            />
          </div>
        )}

        <div className="toolbar" style={{ marginTop: 16 }}>
          <button className="btn btn-primary" type="button" onClick={handleSearch} disabled={loading}>
            {loading ? "Поиск..." : "Найти"}
          </button>
          <button className="btn btn-secondary" type="button" onClick={handleReset}>
            Сброс
          </button>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginTop: 16 }}>
            {typeof error === "string" ? error : JSON.stringify(error)}
          </div>
        )}
      </section>

      <section className="card">
        <div className="section-header">
          <div className="section-title">Результаты поиска</div>
          {hasSearched && <div className="section-meta">Найдено: {items.length}</div>}
        </div>

        {items.length === 0 ? (
          hasSearched ? (
            <div className="empty-state">Ничего не найдено</div>
          ) : (
            <div className="empty-state">Задайте параметры и выполните поиск</div>
          )
        ) : (
          <div className="results-list">
            {items.map((item) => (
              <div className="result-card" key={item.id}>
                {tab === "raw" ? (
                  <div className="result-card-top">
                    <div>
                      <div className="result-title">Сетевая трасса #{item.id}</div>
                      <div className="result-meta">
                        Группа: {item.group_id} • Организация: {item.org || "-"} •
                        Характер: {item.data_character || "-"}
                      </div>
                      <div className="result-meta">
                        Точка: {item.point || "-"} • Пакетов: {item.packets_count ?? "-"}
                      </div>
                      <div className="result-meta">
                        Серия: {item.capture_series || "-"} • Часть: {item.part_index ?? "-"}
                      </div>
                      <div className="result-meta">
                        Интервал: {item.t_min || "-"} — {item.t_max || "-"}
                      </div>
                    </div>

                    <div className="action-stack">
                      <button className="btn btn-secondary" type="button" onClick={() => downloadRawTrace(item.id)}>
                        Скачать
                      </button>
                      <button
                        className="btn btn-secondary"
                        type="button"
                        onClick={() => openRawExportModal(item)}
                      >
                        Скачать фрагмент
                      </button>
                      <button
                        className="btn btn-primary"
                        type="button"
                        onClick={() => handleFindLabeledByRaw(item.id)}
                      >
                        Найти трассу показателей по данной
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="result-card-top">
                    <div>
                      <div className="result-title">
                        Трасса показателей сети #{item.id}
                        <span className="pill pill-accent" style={{ marginLeft: 10 }}>
                          {item.kind === "qos" ? "QoS" : "MAC intensity"}
                        </span>
                      </div>

                      <div className="result-meta">
                        Тип: {item.kind === "qos" ? "QoS" : "Мак-интенсивность"}
                      </div>
                      <div className="result-meta">
                        Доноры:{" "}
                        {Array.isArray(item.donor_raw_trace_ids) && item.donor_raw_trace_ids.length
                          ? item.donor_raw_trace_ids.join(", ")
                          : "-"}{" "}
                        • ПО: {item.software_desc || "-"}
                      </div>
                      <div className="result-meta">
                        Интервал: {item.t_from || "-"} — {item.t_to || "-"}
                      </div>
                    </div>

                    <div className="action-stack users-action-stack">
                      <button className="btn btn-secondary" type="button" onClick={() => downloadLabeledTrace(item.id)}>
                        Скачать
                      </button>

                      <button
                        className="btn btn-secondary"
                        type="button"
                        onClick={() => openLabeledExportModal(item)}
                      >
                        Скачать фрагмент
                      </button>

                      {Array.isArray(item.donor_raw_trace_ids) &&
                        item.donor_raw_trace_ids.map((rawId) => (
                          <button
                            key={rawId}
                            className="btn btn-primary"
                            type="button"
                            onClick={() => handleFindRawByLabeled(rawId)}
                          >
                            Найти сетевую трассу
                          </button>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <TraceExportModal
        open={exportModal.open}
        title={exportModal.title}
        fromValue={exportModal.fromValue}
        toValue={exportModal.toValue}
        onClose={closeExportModal}
        onSubmit={handleExportSubmit}
      />
    </div>
  );
}