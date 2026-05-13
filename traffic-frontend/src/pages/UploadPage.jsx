import React, { useEffect, useMemo, useState } from "react";
import CreateGroupForm from "../components/CreateGroupForm";
import { useAuth } from "../auth/AuthContext";

async function fetchJson(url, options = {}) {
  const resp = await fetch(url, options);

  if (!resp.ok) {
    let message = "Ошибка запроса";
    try {
      const data = await resp.json();
      message = data?.detail || JSON.stringify(data);
    } catch {
      message = await resp.text();
    }
    throw new Error(message || "Ошибка запроса");
  }

  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return await resp.json();
  }

  return null;
}

export default function UploadPage() {
  const { token } = useAuth();

  const [activeTab, setActiveTab] = useState("raw");

  const [createdGroup, setCreatedGroup] = useState(null);
  const [currentGroup, setCurrentGroup] = useState(null);
  const [groupNameInput, setGroupNameInput] = useState("");

  const [descriptionFile, setDescriptionFile] = useState(null);
  const [schemaFile, setSchemaFile] = useState(null);

  const [rawPoint, setRawPoint] = useState("Single");
  const [rawFiles, setRawFiles] = useState([]);

  const [rawTraces, setRawTraces] = useState([]);
  const [loadingRawTraces, setLoadingRawTraces] = useState(false);

  const [labeledKind, setLabeledKind] = useState("qos");
  const [labeledSoftwareDesc, setLabeledSoftwareDesc] = useState("");
  const [labeledFile, setLabeledFile] = useState(null);
  const [selectedDonors, setSelectedDonors] = useState([]);

  const [busy, setBusy] = useState(false);
  const [resolvingGroup, setResolvingGroup] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const effectiveGroupName = useMemo(() => {
    if (groupNameInput.trim()) return groupNameInput.trim();
    if (createdGroup?.name) return createdGroup.name;
    return "";
  }, [groupNameInput, createdGroup]);

  function buildHeaders(extra = {}) {
    return {
      Authorization: `Bearer ${token}`,
      ...extra,
    };
  }

  useEffect(() => {
    if (createdGroup?.name) {
      setGroupNameInput(createdGroup.name);
      setCurrentGroup(createdGroup);
    }
  }, [createdGroup]);

  async function resolveGroupByName(groupName, options = {}) {
    const { silent = false } = options;
    const trimmed = (groupName || "").trim();

    if (!trimmed) {
      if (!silent) {
        throw new Error("Введите название группы.");
      }
      return null;
    }

    setResolvingGroup(true);

    try {
      const groups = await fetchJson(
        `/raw-groups/search?name=${encodeURIComponent(trimmed)}&limit=50`,
        {
          headers: buildHeaders(),
        }
      );

      const exact = (groups || []).find(
        (group) => (group.name || "").trim().toLowerCase() === trimmed.toLowerCase()
      );

      if (!exact) {
        if (!silent) {
          throw new Error("Группа с таким названием не найдена.");
        }
        return null;
      }

      setCurrentGroup(exact);
      return exact;
    } finally {
      setResolvingGroup(false);
    }
  }

  async function handleResolveGroup() {
    setError("");
    setMessage("");

    try {
      const group = await resolveGroupByName(effectiveGroupName);
      if (group) {
        setMessage(`Выбрана группа: ${group.name} (ID ${group.id})`);
        await loadRawTracesByGroup(group);
      }
    } catch (e) {
      setError(e.message || "Не удалось найти группу");
    }
  }

  async function loadRawTracesByGroup(group) {
    if (!group?.id) return;

    setLoadingRawTraces(true);
    setError("");

    try {
      const data = await fetchJson(
        `/raw-traces/search?group_id=${encodeURIComponent(group.id)}`,
        {
          headers: buildHeaders(),
        }
      );
      setRawTraces(data || []);
    } catch (e) {
      setError(e.message || "Не удалось загрузить список трасс");
    } finally {
      setLoadingRawTraces(false);
    }
  }

  async function handleUploadDescription(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!descriptionFile) {
      setError("Выберите файл описания.");
      return;
    }

    setBusy(true);
    try {
      const group = await resolveGroupByName(effectiveGroupName);
      if (!group?.id) {
        throw new Error("Группа не найдена.");
      }

      const formData = new FormData();
      formData.append("file", descriptionFile);

      await fetchJson(`/raw-groups/${group.id}/upload-description`, {
        method: "POST",
        headers: buildHeaders(),
        body: formData,
      });

      setMessage(`Описание успешно загружено для группы «${group.name}».`);
      setDescriptionFile(null);
    } catch (e) {
      setError(e.message || "Не удалось загрузить описание");
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadSchema(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!schemaFile) {
      setError("Выберите файл схемы.");
      return;
    }

    setBusy(true);
    try {
      const group = await resolveGroupByName(effectiveGroupName);
      if (!group?.id) {
        throw new Error("Группа не найдена.");
      }

      const formData = new FormData();
      formData.append("file", schemaFile);

      await fetchJson(`/raw-groups/${group.id}/upload-schema`, {
        method: "POST",
        headers: buildHeaders(),
        body: formData,
      });

      setMessage(`Схема успешно загружена для группы «${group.name}».`);
      setSchemaFile(null);
    } catch (e) {
      setError(e.message || "Не удалось загрузить схему");
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadRawTraces(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!effectiveGroupName) {
      setError("Введите название группы.");
      return;
    }

    if (rawFiles.length === 0) {
      setError("Выберите хотя бы один pcap-файл.");
      return;
    }

    setBusy(true);
    try {
      const group = await resolveGroupByName(effectiveGroupName);
      if (!group?.name) {
        throw new Error("Группа не найдена.");
      }

      const formData = new FormData();
      rawFiles.forEach((file) => formData.append("files", file));

      await fetchJson(
        `/raw-traces/group/by-name/${encodeURIComponent(group.name)}/batch?point=${encodeURIComponent(rawPoint)}`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: formData,
        }
      );

      setMessage(`Необработанные трассы успешно загружены в группу «${group.name}».`);
      setRawFiles([]);
      await loadRawTracesByGroup(group);
    } catch (e) {
      setError(e.message || "Не удалось загрузить pcap-файлы");
    } finally {
      setBusy(false);
    }
  }

  async function handleUploadLabeledTrace(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!labeledFile) {
      setError("Выберите csv-файл трассы с разметкой.");
      return;
    }

    if (selectedDonors.length === 0) {
      setError("Выберите хотя бы одну трассу-донор.");
      return;
    }

    const formData = new FormData();
    formData.append("kind", labeledKind);
    formData.append("raw_trace_ids", selectedDonors.join(","));
    formData.append("software_desc", labeledSoftwareDesc);
    formData.append("file", labeledFile);

    setBusy(true);
    try {
      await fetchJson(`/labeled-traces`, {
        method: "POST",
        headers: buildHeaders(),
        body: formData,
      });

      setMessage("Трасса с разметкой успешно загружена.");
      setLabeledFile(null);
      setLabeledSoftwareDesc("");
      setSelectedDonors([]);
    } catch (e) {
      setError(e.message || "Не удалось загрузить размеченную трассу");
    } finally {
      setBusy(false);
    }
  }

  function toggleDonor(id) {
    setSelectedDonors((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  }

  function handleGroupNameChange(value) {
    setGroupNameInput(value);
    setCurrentGroup(null);
    setRawTraces([]);
    setSelectedDonors([]);
  }

  return (
    <div className="upload-page">
      <CreateGroupForm onCreated={setCreatedGroup} />

      <div className="upload-card">
        <div className="section-header">
          <div>
            <h2 className="section-title">Загрузка файлов</h2>
            <p className="section-subtitle">
              {currentGroup
                ? `Текущая группа: ${currentGroup.name} (ID ${currentGroup.id})`
                : "Введите название существующей группы или сначала создайте новую."}
            </p>
          </div>
        </div>

        <div className="upload-tabs">
          <button
            type="button"
            className={`btn ${activeTab === "raw" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveTab("raw")}
          >
            Необработанные трассы
          </button>
          <button
            type="button"
            className={`btn ${activeTab === "labeled" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setActiveTab("labeled")}
          >
            Трассы с разметкой
          </button>
        </div>

        <div className="upload-group-picker" style={{ marginTop: 16 }}>
          <div className="form-field" style={{ flex: 1 }}>
            <span className="form-label">Название группы</span>
            <input
              className="input"
              value={effectiveGroupName}
              onChange={(e) => handleGroupNameChange(e.target.value)}
              placeholder="Введите название группы"
            />
          </div>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleResolveGroup}
            disabled={!effectiveGroupName || resolvingGroup}
          >
            {resolvingGroup ? "Поиск..." : "Найти группу"}
          </button>
        </div>

        {message ? <div className="alert alert-success">{message}</div> : null}
        {error ? <div className="alert alert-error">{error}</div> : null}

        {activeTab === "raw" && (
          <>
            <div className="upload-section">
              <h3 className="subsection-title">Описание группы</h3>
              <form onSubmit={handleUploadDescription} className="upload-form">
                <div className="file-picker">
                  <input
                    id="group-description-file"
                    type="file"
                    accept=".md,.markdown,.txt"
                    onChange={(e) => setDescriptionFile(e.target.files?.[0] || null)}
                    hidden
                  />
                  <label htmlFor="group-description-file" className="btn btn-secondary">
                    Выбрать файл
                  </label>
                  <span className="file-name">
                    {descriptionFile ? descriptionFile.name : "Файл не выбран"}
                  </span>
                </div>

                <button type="submit" className="btn btn-primary" disabled={busy}>
                  Загрузить описание
                </button>
              </form>
            </div>

            <div className="upload-section">
              <h3 className="subsection-title">Схема группы</h3>
              <form onSubmit={handleUploadSchema} className="upload-form">
                <div className="file-picker">
                  <input
                    id="group-schema-file"
                    type="file"
                    accept=".png,.jpg,.jpeg,.pdf,.svg"
                    onChange={(e) => setSchemaFile(e.target.files?.[0] || null)}
                    hidden
                  />
                  <label htmlFor="group-schema-file" className="btn btn-secondary">
                    Выбрать файл
                  </label>
                  <span className="file-name">
                    {schemaFile ? schemaFile.name : "Файл не выбран"}
                  </span>
                </div>

                <button type="submit" className="btn btn-primary" disabled={busy}>
                  Загрузить схему
                </button>
              </form>
            </div>

            <div className="upload-section">
              <h3 className="subsection-title">Файлы трасс</h3>
              <form onSubmit={handleUploadRawTraces} className="upload-form">
                <label className="form-field">
                  <span className="form-label">Точка сбора</span>
                  <select
                    className="input"
                    value={rawPoint}
                    onChange={(e) => setRawPoint(e.target.value)}
                  >
                    <option value="Single">Single</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                  </select>
                </label>

                <div className="file-picker">
                  <input
                    id="raw-traces-files"
                    type="file"
                    accept=".pcap,.pcapng"
                    multiple
                    onChange={(e) => setRawFiles(Array.from(e.target.files || []))}
                    hidden
                  />
                  <label htmlFor="raw-traces-files" className="btn btn-secondary">
                    Выбрать файлы
                  </label>
                  <span className="file-name">
                    {rawFiles.length > 0
                      ? `Выбрано файлов: ${rawFiles.length}`
                      : "Файлы не выбраны"}
                  </span>
                </div>

                {rawFiles.length > 0 && (
                  <div className="selected-files">
                    {rawFiles.map((file) => (
                      <div key={file.name} className="selected-file-item">
                        {file.name}
                      </div>
                    ))}
                  </div>
                )}

                <button type="submit" className="btn btn-primary btn-large" disabled={busy}>
                  Загрузить трассы
                </button>
              </form>
            </div>

            <div className="upload-section">
              <div className="upload-section-header">
                <h3 className="subsection-title">Трассы текущей группы</h3>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleResolveGroup}
                  disabled={!effectiveGroupName || loadingRawTraces || resolvingGroup}
                >
                  {loadingRawTraces || resolvingGroup ? "Загрузка..." : "Обновить список"}
                </button>
              </div>

              {rawTraces.length === 0 ? (
                <div className="muted-text">Пока нет загруженных трасс или список не обновлён.</div>
              ) : (
                <div className="simple-table-wrap">
                  <table className="simple-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Point</th>
                        <th>t_min</th>
                        <th>t_max</th>
                        <th>Packets</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rawTraces.map((trace) => (
                        <tr key={trace.id}>
                          <td>{trace.id}</td>
                          <td>{trace.point}</td>
                          <td>{trace.t_min || "—"}</td>
                          <td>{trace.t_max || "—"}</td>
                          <td>{trace.packets_count ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === "labeled" && (
          <>
            <div className="upload-section">
              <div className="upload-section-header">
                <h3 className="subsection-title">Трассы-доноры</h3>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleResolveGroup}
                  disabled={!effectiveGroupName || loadingRawTraces || resolvingGroup}
                >
                  {loadingRawTraces || resolvingGroup ? "Загрузка..." : "Загрузить трассы группы"}
                </button>
              </div>

              {rawTraces.length === 0 ? (
                <div className="muted-text">
                  Сначала выберите группу и загрузите список её трасс.
                </div>
              ) : (
                <div className="donor-list">
                  {rawTraces.map((trace) => (
                    <label key={trace.id} className="donor-item">
                      <input
                        type="checkbox"
                        checked={selectedDonors.includes(trace.id)}
                        onChange={() => toggleDonor(trace.id)}
                      />
                      <span>
                        ID {trace.id}, point={trace.point}, packets={trace.packets_count ?? "—"}
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="upload-section">
              <h3 className="subsection-title">CSV-файл разметки</h3>
              <form onSubmit={handleUploadLabeledTrace} className="upload-form">
                <label className="form-field">
                  <span className="form-label">Тип разметки</span>
                  <select
                    className="input"
                    value={labeledKind}
                    onChange={(e) => setLabeledKind(e.target.value)}
                  >
                    <option value="qos">QoS</option>
                    <option value="mac_intensity">MAC intensity</option>
                  </select>
                </label>

                <label className="form-field">
                  <span className="form-label">Описание ПО разметки</span>
                  <input
                    className="input"
                    value={labeledSoftwareDesc}
                    onChange={(e) => setLabeledSoftwareDesc(e.target.value)}
                    placeholder="Например: label-tool 1.0"
                  />
                </label>

                <div className="file-picker">
                  <input
                    id="labeled-trace-file"
                    type="file"
                    accept=".csv"
                    onChange={(e) => setLabeledFile(e.target.files?.[0] || null)}
                    hidden
                  />
                  <label htmlFor="labeled-trace-file" className="btn btn-secondary">
                    Выбрать CSV
                  </label>
                  <span className="file-name">
                    {labeledFile ? labeledFile.name : "Файл не выбран"}
                  </span>
                </div>

                <button type="submit" className="btn btn-primary btn-large" disabled={busy}>
                  Загрузить трассу с разметкой
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
}