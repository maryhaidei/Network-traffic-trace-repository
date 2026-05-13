import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import logo from "../assets/logo.png";

export default function LoginPage() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    login: "",
    password: "",
  });
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    try {
      await login(form.login, form.password);
      navigate("/groups");
    } catch (e) {
      setError(e?.message || "Ошибка входа");
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <img src={logo} alt="Логотип" className="login-logo" />

        <h1 className="login-title">Репозиторий трасс сетевого трафика</h1>
        <p className="login-subtitle">
          Вход в систему хранения и анализа трасс
        </p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="form-label">
            Логин
            <input
              className="input"
              value={form.login}
              onChange={(e) => setForm({ ...form, login: e.target.value })}
              placeholder="Введите логин"
              required
            />
          </label>

          <label className="form-label">
            Пароль
            <input
              className="input"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="Введите пароль"
              required
            />
          </label>

          {error && <div className="alert alert-error">{error}</div>}

          <button className="btn btn-primary btn-lg" type="submit" disabled={loading}>
            {loading ? "Вход..." : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
}