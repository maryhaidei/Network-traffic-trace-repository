import React, { useState } from "react";
import CreateGroupForm from "../components/CreateGroupForm";
import {
  getRawTracesByGroup,
  searchGroups,
  uploadGroupDescription,
  uploadGroupSchema,
  uploadLabeledTrace,
  uploadPcapBatchToGroup,
} from "../api/client";

export default function UploadPage() {
  const [activeTab, setActiveTab] = useState("raw");

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

  const effectiveGroupName = groupNameInput.trim();

  const groupPickerStyle = {
    display: "grid",
    gridTemplateColumns: "minmax(0, 1fr) auto",
    gap: 16,
    alignItems: "end",
    marginTop: 16,
  };

  const groupPickerButtonStyle = {
    minHeight: 52,
    whiteSpace: "nowrap",
    alignSelf: "end",
  };

  const statusAreaStyle = {
    display: "grid",
    gap: 10,
    marginTop: 16,
  };

  function selectGroup(group) {
    if (!group) return;

    setCurrentGroup(group);
    setGroupNameInput(group.name || "");
    setRawTraces([]);
    setSelectedDonors([]);
    setMessage("");
    setError("");
  }

  async function handleGroupCreated(group) {
    selectGroup(group);

    try {
      await loadRawTracesByGroup(group);
    } catch {
      // Ошибка уже будет записана внутри loadRawTracesByGroup.
    }
  }

  function isCurrentGroupMatchedToInput() {
    const inputName = groupNameInput.trim().toLowerCase();
    const selectedName = (currentGroup?.name || "").trim().toLowerCase();

    return Boolean(currentGroup?.id && inputName && inputName === selectedName);
  }

  async function resolveGroupByName(groupName, options = {}) {
    const { silent = false } = options;
    const trimmed = (groupName || "").trim();

    if (!trimmed) {
      if (!silent) {
        throw new Error("Введите название группы.");
      }
      return null;
    }

    if (isCurrentGroupMatchedToInput()) {
      return currentGroup;
    }

    setResolvingGroup(true);

    try {
      const groups = await searchGroups({ name: trimmed, limit: 50 });
      const exact = (groups || []).find(
        (group) => (group.name || "").trim().toLowerCase() === trimmed.toLowerCase()
      );

      if (!exact) {
        if (!silent) {
          throw new Error("Группа с таким названием не найдена.");
        }
        return null;
      }

      selectGroup(exact);
      return exact;
    } finally {
      setResolvingGroup(false);
    }
  }

  async function getGroupForOperation() {
    const group = await resolveGroupByName(effectiveGroupName);
    if (!group?.id) {
      throw new Error("Группа не найдена.");
    }

    return group;
  }

function formatRawTraceName(trace) {
  if (trace.original_filename) {
    return trace.original_filename;
  }

  if (
    trace.capture_series &&
    trace.part_index !== null &&
    trace.part_index !== undefined
  ) {
    return `${trace.capture_series}${String(trace.part_index).padStart(3, "0")}`;
  }

  if (trace.capture_series) {
    return trace.capture_series;
  }

  return `PCAP-файл #${trace.id}`;
}

  async function handleResolveGroup() {
    setError("");
    setMessage("");

    try {
      const group = await resolveGroupByName(effectiveGroupName);
      if (group) {
        await loadRawTracesByGroup(group);
      }
    } catch (e) {
      setCurrentGroup(null);
      setRawTraces([]);
      setSelectedDonors([]);
      setError(e.message || "Не удалось найти группу");
    }
  }

  async function loadRawTracesByGroup(group) {
    if (!group?.id) return;

    setLoadingRawTraces(true);
    setError("");

    try {
      const data = await getRawTracesByGroup(group.id);
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
      const group = await getGroupForOperation();

      await uploadGroupDescription(group.id, descriptionFile);

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
      const group = await getGroupForOperation();

      await uploadGroupSchema(group.id, schemaFile);

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
      const group = await getGroupForOperation();

      await uploadPcapBatchToGroup(group.id, rawFiles, rawPoint);

      setMessage(`Сетевые трассы успешно загружены в группу «${group.name}».`);
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
      setError("Выберите csv-файл трассы показателей сети.");
      return;
    }

    if (selectedDonors.length === 0) {
      setError("Выберите хотя бы одну трассу-донор.");
      return;
    }

    setBusy(true);

    try {
      await uploadLabeledTrace(
        selectedDonors,
        labeledFile,
        labeledKind,
        labeledSoftwareDesc
      );

      setMessage("Трасса показателей сети успешно загружена.");
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

    const inputName = value.trim().toLowerCase();
    const selectedName = (currentGroup?.name || "").trim().toLowerCase();

    if (inputName !== selectedName) {
      setCurrentGroup(null);
      setRawTraces([]);
      setSelectedDonors([]);
    }

    setMessage("");
    setError("");
  }

  return (
    <div className="upload-page">
      <CreateGroupForm onCreated={handleGroupCreated} />

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
            onClick={async () => {
              setActiveTab("labeled");

              if (currentGroup?.id && rawTraces.length === 0) {
                await loadRawTracesByGroup(currentGroup);
              }
            }}
          >
            Трассы с разметкой
          </button>
        </div>

        <div className="upload-group-picker" style={groupPickerStyle}>
          <label className="form-field" style={{ minWidth: 0 }}>
            <span className="form-label">Название группы</span>
            <input
              className="input"
              value={groupNameInput}
              onChange={(e) => handleGroupNameChange(e.target.value)}
              placeholder="Введите название группы"
            />
          </label>

          <button
            type="button"
            className="btn btn-secondary"
            style={groupPickerButtonStyle}
            onClick={handleResolveGroup}
            disabled={!effectiveGroupName || resolvingGroup}
          >
            {resolvingGroup ? "Поиск..." : "Найти группу"}
          </button>
        </div>

        <div className="upload-status-area" style={statusAreaStyle} aria-live="polite">
          {currentGroup ? (
            <div className="alert alert-success">
              Выбрана группа: {currentGroup.name} (ID {currentGroup.id})
            </div>
          ) : null}

          {message ? <div className="alert alert-success">{message}</div> : null}
          {error ? <div className="alert alert-error">{error}</div> : null}
        </div>

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
                        <th>Трасса</th>
                        <th>Point</th>
                        <th>t_min</th>
                        <th>t_max</th>
                        <th>Packets</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rawTraces.map((trace) => (
                        <tr key={trace.id}>
                          <td>{formatRawTraceName(trace)}</td>
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
                        {formatRawTraceName(trace)}
                        <span className="muted-text">
                          {" "}· ID {trace.id} · point={trace.point} · packets={trace.packets_count ?? "—"}
                        </span>
                      </span>
                    </label>
                  ))}
                </div>
              )}
            </div>

            <div className="upload-section">
              <h3 className="subsection-title">CSV-файл</h3>
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
                  Загрузить трассу покзателей сети
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </div>
  );
}