import React, { useState } from "react";
import {
  createUserApi,
  deleteUserByLoginApi,
  getUserByLoginApi,
  resetUserPasswordByLoginApi,
} from "../api/client";

const initialCreateForm = {
  login: "",
  password: "",
  last_name: "",
  first_name: "",
  organization: "",
  email: "",
  role: "user",
};

const initialManageForm = {
  login: "",
  newPassword: "",
};

export default function UsersPage() {
  const [createForm, setCreateForm] = useState(initialCreateForm);
  const [manageForm, setManageForm] = useState(initialManageForm);

  const [saving, setSaving] = useState(false);
  const [managing, setManaging] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [foundUser, setFoundUser] = useState(null);

  function updateCreate(field, value) {
    setCreateForm((prev) => ({ ...prev, [field]: value }));
  }

  function updateManage(field, value) {
    setManageForm((prev) => ({ ...prev, [field]: value }));
  }

  function clearMessages() {
    setError("");
    setSuccess("");
  }

  async function handleCreate(e) {
    e.preventDefault();
    clearMessages();
    setFoundUser(null);
    setSaving(true);

    try {
      const user = await createUserApi({
        login: createForm.login.trim(),
        password: createForm.password,
        last_name: createForm.last_name.trim(),
        first_name: createForm.first_name.trim(),
        organization: createForm.organization.trim(),
        email: createForm.email.trim(),
        role: createForm.role,
      });

      setSuccess(`Пользователь создан: ${user.login} (${user.role})`);
      setCreateForm(initialCreateForm);
    } catch (e) {
      setError(e?.message || "Ошибка создания пользователя");
    } finally {
      setSaving(false);
    }
  }

  async function handleFindByLogin(e) {
    e.preventDefault();
    clearMessages();
    setFoundUser(null);
    setManaging(true);

    try {
      const user = await getUserByLoginApi(manageForm.login.trim());
      setFoundUser(user);
      setSuccess(`Пользователь найден: ${user.login}`);
    } catch (e) {
      setError(e?.message || "Пользователь не найден");
    } finally {
      setManaging(false);
    }
  }

  async function handleDeleteByLogin() {
    const login = manageForm.login.trim();
    if (!login) {
      setError("Введите логин пользователя");
      return;
    }

    const confirmed = window.confirm(`Удалить пользователя ${login}?`);
    if (!confirmed) return;

    clearMessages();
    setManaging(true);

    try {
      await deleteUserByLoginApi(login);
      setSuccess(`Пользователь ${login} удалён`);
      setFoundUser(null);
      setManageForm(initialManageForm);
    } catch (e) {
      setError(e?.message || "Ошибка удаления пользователя");
    } finally {
      setManaging(false);
    }
  }

  async function handleResetPasswordByLogin() {
    const login = manageForm.login.trim();
    const newPassword = manageForm.newPassword;

    if (!login) {
      setError("Введите логин пользователя");
      return;
    }

    if (!newPassword || newPassword.length < 8) {
      setError("Новый пароль должен содержать не менее 8 символов");
      return;
    }

    clearMessages();
    setManaging(true);

    try {
      await resetUserPasswordByLoginApi(login, newPassword);
      setSuccess(`Пароль пользователя ${login} успешно сброшен`);
      setManageForm((prev) => ({ ...prev, newPassword: "" }));
    } catch (e) {
      setError(e?.message || "Ошибка сброса пароля");
    } finally {
      setManaging(false);
    }
  }

  return (
    <div className="page-grid">
      <section className="hero-card">
        <div>
          <div className="hero-badge">Администрирование</div>
          <h2 className="hero-title">Управление пользователями</h2>
          <p className="hero-text">
            Здесь администратор может создавать пользователей, искать их по логину,
            удалять учётные записи и выполнять сброс пароля.
          </p>
        </div>
      </section>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="two-col-grid">
        <section className="card">
          <div className="section-header">
            <div className="section-title">Добавление пользователя</div>
          </div>

          <form className="form-grid" onSubmit={handleCreate}>
            <label className="form-label">
              Логин
              <input
                className="input"
                value={createForm.login}
                onChange={(e) => updateCreate("login", e.target.value)}
                minLength={8}
                maxLength={8}
                placeholder="Ровно 8 символов"
                required
              />
            </label>

            <label className="form-label">
              Пароль
              <input
                className="input"
                type="password"
                value={createForm.password}
                onChange={(e) => updateCreate("password", e.target.value)}
                minLength={8}
                placeholder="Введите пароль"
                required
              />
            </label>

            <label className="form-label">
              Фамилия
              <input
                className="input"
                value={createForm.last_name}
                onChange={(e) => updateCreate("last_name", e.target.value)}
                required
              />
            </label>

            <label className="form-label">
              Имя
              <input
                className="input"
                value={createForm.first_name}
                onChange={(e) => updateCreate("first_name", e.target.value)}
                required
              />
            </label>

            <label className="form-label">
              Организация
              <input
                className="input"
                value={createForm.organization}
                onChange={(e) => updateCreate("organization", e.target.value)}
                required
              />
            </label>

            <label className="form-label">
              E-mail
              <input
                className="input"
                type="email"
                value={createForm.email}
                onChange={(e) => updateCreate("email", e.target.value)}
                required
              />
            </label>

            <label className="form-label">
              Роль
              <select
                className="input"
                value={createForm.role}
                onChange={(e) => updateCreate("role", e.target.value)}
              >
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </label>

            <div className="form-actions">
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? "Создание..." : "Создать пользователя"}
              </button>
            </div>
          </form>
        </section>

        <section className="card">
          <div className="section-header">
            <div className="section-title">Поиск и действия по логину</div>
          </div>

          <form className="form-grid" onSubmit={handleFindByLogin}>
            <label className="form-label">
              Логин пользователя
              <input
                className="input"
                value={manageForm.login}
                onChange={(e) => updateManage("login", e.target.value)}
                minLength={8}
                maxLength={8}
                placeholder="Введите логин"
                required
              />
            </label>

            <div className="form-actions">
              <button className="btn btn-primary" type="submit" disabled={managing}>
                {managing ? "Поиск..." : "Найти пользователя"}
              </button>
            </div>
          </form>

          {foundUser && (
            <div className="sub-card" style={{ marginTop: 16 }}>
              <div className="result-title">{foundUser.login}</div>
              <div className="result-meta">
                {foundUser.last_name} {foundUser.first_name}
              </div>
              <div className="result-meta">Организация: {foundUser.organization}</div>
              <div className="result-meta">E-mail: {foundUser.email}</div>
              <div className="result-meta">
                Роль:{" "}
                <span className="pill pill-accent" style={{ marginLeft: 6 }}>
                  {foundUser.role}
                </span>
              </div>
            </div>
          )}

          <div className="form-grid" style={{ marginTop: 16 }}>
            <label className="form-label">
              Новый пароль для сброса
              <input
                className="input"
                type="password"
                value={manageForm.newPassword}
                onChange={(e) => updateManage("newPassword", e.target.value)}
                minLength={8}
                placeholder="Введите новый пароль"
              />
            </label>
          </div>

          <div className="users-actions-row" style={{ marginTop: 16 }}>
            <button
              className="btn btn-secondary"
              type="button"
              onClick={handleResetPasswordByLogin}
              disabled={managing}
            >
              Сбросить пароль
            </button>

            <button
              className="btn btn-danger"
              type="button"
              onClick={handleDeleteByLogin}
              disabled={managing}
            >
              Удалить пользователя
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}