import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import TraceExportModal from "../components/TraceExportModal";
import {
  downloadRawTrace,
  exportGroupZip,
  exportRawTraceSegment,
  getGroup,
  getRawTracesByGroup,
  patchGroup,
  uploadGroupDescription,
  uploadGroupSchema,
  uploadPcapBatchToGroup,
} from "../api/client";

export default function GroupDetailsPage() {
  const { id } = useParams();
  const groupId = Number(id);

  const [group, setGroup] = useState(null);
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingGroup, setSavingGroup] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("meta");

  const [edit, setEdit] = useState({
    org: "",
    data_character: "",
    hardware_desc: "",
    software_desc: "",
    processing_degree: "",
    capture_points: 1,
    capture_start: "",
    capture_end: "",
  });

  const [descFile, setDescFile] = useState(null);
  const [schemaFile, setSchemaFile] = useState(null);
  const [pcapFiles, setPcapFiles] = useState([]);
  const [pcapPoint, setPcapPoint] = useState("Single");

  const [exportModal, setExportModal] = useState({
  open: false,
  traceId: null,
  fromValue: "",
  toValue: "",
});

  async function reloadGroup() {
    const g = await getGroup(groupId);
    setGroup(g);
    setEdit({
      org: g.org || "",
      data_character: g.data_character || "",
      hardware_desc: g.hardware_desc || "",
      software_desc: g.software_desc || "",
      processing_degree: g.processing_degree || "",
      capture_points: g.capture_points || 1,
      capture_start: g.capture_start ? g.capture_start.slice(0, 16) : "",
      capture_end: g.capture_end ? g.capture_end.slice(0, 16) : "",
    });
    setPcapPoint((g.capture_points || 1) === 2 ? "A" : "Single");
  }

  async function reloadTraces() {
    const data = await getRawTracesByGroup(groupId);
    setTraces(data);
  }

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");

      try {
        await Promise.all([reloadGroup(), reloadTraces()]);
      } catch (e) {
        setError(e?.message || "Ошибка загрузки группы");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [groupId]);

  async function handleSaveGroup(e) {
    e.preventDefault();
    setSavingGroup(true);
    setError("");

    try {
      const payload = {
        org: edit.org || null,
        data_character: edit.data_character || null,
        hardware_desc: edit.hardware_desc || null,
        software_desc: edit.software_desc || null,
        processing_degree: edit.processing_degree || null,
        capture_points: Number(edit.capture_points),
        capture_start: edit.capture_start ? new Date(edit.capture_start).toISOString() : null,
        capture_end: edit.capture_end ? new Date(edit.capture_end).toISOString() : null,
      };

      await patchGroup(groupId, payload);
      await reloadGroup();
    } catch (e) {
      setError(e?.message || "Ошибка сохранения");
    } finally {
      setSavingGroup(false);
    }
  }

  async function handleUploadDescription() {
    if (!descFile) {
      setError("Выберите markdown-файл");
      return;
    }

    try {
      setError("");
      await uploadGroupDescription(groupId, descFile);
      alert("Описание загружено");
      setDescFile(null);
    } catch (e) {
      setError(e?.message || "Ошибка загрузки описания");
    }
  }

  async function handleUploadSchema() {
    if (!schemaFile) {
      setError("Выберите файл схемы");
      return;
    }

    try {
      setError("");
      await uploadGroupSchema(groupId, schemaFile);
      alert("Схема загружена");
      setSchemaFile(null);
    } catch (e) {
      setError(e?.message || "Ошибка загрузки схемы");
    }
  }

  async function handleUploadPcaps() {
    if (!pcapFiles.length) {
      setError("Выберите pcap-файлы");
      return;
    }

    try {
      setError("");
      await uploadPcapBatchToGroup(groupId, pcapFiles, pcapPoint);
      await reloadTraces();
      setPcapFiles([]);
      alert("Файлы загружены");
    } catch (e) {
      setError(e?.message || "Ошибка загрузки трасс");
    }
  }

  async function handleExportGroup() {
    try {
      await exportGroupZip(groupId);
    } catch (e) {
      setError(e?.message || "Ошибка экспорта группы");
    }
  }

  async function handleDownloadTrace(traceId) {
    try {
      await downloadRawTrace(traceId);
    } catch (e) {
      setError(e?.message || "Ошибка скачивания");
    }
  }

function handleExportTraceSegment(trace) {
  setExportModal({
    open: true,
    traceId: trace.id,
    fromValue: trace.t_min || "",
    toValue: trace.t_max || "",
  });
}

function closeExportModal() {
  setExportModal({
    open: false,
    traceId: null,
    fromValue: "",
    toValue: "",
  });
}

async function submitExportTraceSegment({ t_from, t_to }) {
  try {
    await exportRawTraceSegment(exportModal.traceId, t_from, t_to);
    closeExportModal();
  } catch (e) {
    setError(e?.message || "Ошибка экспорта фрагмента");
  }
}

  if (loading) {
    return <div className="card">Загрузка...</div>;
  }

  if (!group) {
    return <div className="card">Группа не найдена</div>;
  }

  return (
    <div className="page-grid">
      <section className="hero-card">
        <div>
          <div className="hero-badge">Группа #{group.id}</div>
          <h2 className="hero-title">{group.org}</h2>
          <p className="hero-text">
            {group.data_character}
          </p>
          <div className="hero-pills">
            <span className="pill">{group.capture_points} точка(и)</span>
            <span className="pill">{group.capture_start ? new Date(group.capture_start).toLocaleString() : "-"}</span>
            <span className="pill">{group.capture_end ? new Date(group.capture_end).toLocaleString() : "-"}</span>
          </div>
        </div>

        <div className="hero-actions">
          <button className="btn btn-primary" onClick={handleExportGroup}>
            Экспорт группы
          </button>
        </div>
      </section>

      <section className="card">
        <div className="tab-switcher">
          <button className={activeTab === "meta" ? "tab-btn active" : "tab-btn"} onClick={() => setActiveTab("meta")}>
            Метаданные
          </button>
          <button className={activeTab === "files" ? "tab-btn active" : "tab-btn"} onClick={() => setActiveTab("files")}>
            Описание и схема
          </button>
          <button className={activeTab === "upload" ? "tab-btn active" : "tab-btn"} onClick={() => setActiveTab("upload")}>
            Загрузка трасс
          </button>
          <button className={activeTab === "traces" ? "tab-btn active" : "tab-btn"} onClick={() => setActiveTab("traces")}>
            Сетевые трассы
          </button>
        </div>

        {error && <div className="alert alert-error" style={{ marginTop: 16 }}>{error}</div>}

        {activeTab === "meta" && (
          <form className="form-grid" onSubmit={handleSaveGroup} style={{ marginTop: 16 }}>
            <label className="form-label">
              Организация
              <input
                className="input"
                value={edit.org}
                onChange={(e) => setEdit({ ...edit, org: e.target.value })}
              />
            </label>

            <label className="form-label">
              Характер данных
              <input
                className="input"
                value={edit.data_character}
                onChange={(e) => setEdit({ ...edit, data_character: e.target.value })}
              />
            </label>

            <label className="form-label">
              Аппаратура
              <textarea
                className="textarea"
                rows={3}
                value={edit.hardware_desc}
                onChange={(e) => setEdit({ ...edit, hardware_desc: e.target.value })}
              />
            </label>

            <label className="form-label">
              ПО сбора
              <textarea
                className="textarea"
                rows={3}
                value={edit.software_desc}
                onChange={(e) => setEdit({ ...edit, software_desc: e.target.value })}
              />
            </label>

            <label className="form-label">
              Степень обработки
              <textarea
                className="textarea"
                rows={3}
                value={edit.processing_degree}
                onChange={(e) => setEdit({ ...edit, processing_degree: e.target.value })}
              />
            </label>

            <label className="form-label">
              Точек сбора
              <select
                className="input"
                value={edit.capture_points}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  setEdit({ ...edit, capture_points: value });
                  setPcapPoint(value === 2 ? "A" : "Single");
                }}
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
              </select>
            </label>

            <label className="form-label">
              Начало
              <input
                className="input"
                type="datetime-local"
                value={edit.capture_start}
                onChange={(e) => setEdit({ ...edit, capture_start: e.target.value })}
              />
            </label>

            <label className="form-label">
              Конец
              <input
                className="input"
                type="datetime-local"
                value={edit.capture_end}
                onChange={(e) => setEdit({ ...edit, capture_end: e.target.value })}
              />
            </label>

            <div className="form-actions">
              <button className="btn btn-primary" type="submit" disabled={savingGroup}>
                {savingGroup ? "Сохранение..." : "Сохранить изменения"}
              </button>
            </div>
          </form>
        )}

        {activeTab === "files" && (
          <div className="two-col-grid" style={{ marginTop: 16 }}>
            <div className="sub-card">
              <div className="section-title">Описание группы</div>
              <input
                className="input"
                type="file"
                accept=".md,text/markdown"
                onChange={(e) => setDescFile(e.target.files?.[0] || null)}
              />
              <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={handleUploadDescription}>
                Загрузить описание
              </button>
            </div>

            <div className="sub-card">
              <div className="section-title">Схема стенда</div>
              <input
                className="input"
                type="file"
                accept="image/*,application/pdf"
                onChange={(e) => setSchemaFile(e.target.files?.[0] || null)}
              />
              <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={handleUploadSchema}>
                Загрузить схему
              </button>
            </div>
          </div>
        )}

        {activeTab === "upload" && (
          <div style={{ marginTop: 16 }}>
            <div className="form-grid">
              <label className="form-label">
                Точка сбора
                <select
                  className="input"
                  value={pcapPoint}
                  onChange={(e) => setPcapPoint(e.target.value)}
                >
                  {Number(edit.capture_points) === 2 ? (
                    <>
                      <option value="A">A</option>
                      <option value="B">B</option>
                    </>
                  ) : (
                    <option value="Single">Single</option>
                  )}
                </select>
              </label>

              <label className="form-label">
                Файлы трасс
                <input
                  className="input"
                  type="file"
                  multiple
                  accept=".pcap,.pcapng,application/vnd.tcpdump.pcap"
                  onChange={(e) => setPcapFiles(Array.from(e.target.files || []))}
                />
              </label>
            </div>

            <div className="form-actions">
              <button className="btn btn-primary" onClick={handleUploadPcaps}>
                Загрузить выбранные файлы
              </button>
            </div>
          </div>
        )}

        {activeTab === "traces" && (
          <div style={{ marginTop: 16 }}>
            {traces.length === 0 ? (
              <div className="empty-state">В этой группе пока нет сетевых трасс</div>
            ) : (
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Точка</th>
                      <th>Серия</th>
                      <th>Часть</th>
                      <th>Начало</th>
                      <th>Конец</th>
                      <th>Пакетов</th>
                      <th>Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {traces.map((t) => (
                      <tr key={t.id}>
                        <td>{t.id}</td>
                        <td>{t.point}</td>
                        <td>{t.capture_series || "-"}</td>
                        <td>{t.part_index ?? "-"}</td>
                        <td>{t.t_min || "-"}</td>
                        <td>{t.t_max || "-"}</td>
                        <td>{t.packets_count ?? "-"}</td>
                        <td>
                          <div className="table-actions">
                            <button className="btn btn-secondary btn-sm" onClick={() => handleDownloadTrace(t.id)}>
                              Скачать
                            </button>
                            <button className="btn btn-secondary btn-sm" onClick={() => handleExportTraceSegment(t)}>
                              Фрагмент
                            </button>
                            <TraceExportModal
                             open={exportModal.open}
                             title={
                              exportModal.traceId
                               ? `Скачать фрагмент сетевой трассы #${exportModal.traceId}`
                               : "Скачать фрагмент сетевой трассы"
                             }
                             fromValue={exportModal.fromValue}
                             toValue={exportModal.toValue}
                             onClose={closeExportModal}
                             onSubmit={submitExportTraceSegment}
                           />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}