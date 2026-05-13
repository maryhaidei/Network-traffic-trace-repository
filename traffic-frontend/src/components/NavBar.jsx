import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function NavBar() {
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div
      style={{
        display: "flex",
        padding: "8px 16px",
        borderBottom: "1px solid #ddd",
        marginBottom: 16,
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16,
      }}
    >
      <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
        <strong>Traffic Trace Repo</strong>
        {isAuthenticated && (
          <>
            <Link to="/groups">Группы трасс</Link>
            <Link to="/upload">Загрузка трасс</Link>
            {isAdmin && <Link to="/users">Пользователи</Link>}
          </>
        )}
      </div>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        {isAuthenticated ? (
          <>
            <span style={{ fontSize: 14, color: "#555" }}>
              {user?.login} ({user?.role})
            </span>
            <button type="button" onClick={handleLogout}>
              Выйти
            </button>
          </>
        ) : (
          <Link to="/login">Войти</Link>
        )}
      </div>
    </div>
  );
}