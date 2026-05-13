import React from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import logo from "../assets/logo.png";

function PageHeaderTitle(pathname) {
  if (pathname.startsWith("/users")) return "Управление пользователями";
  if (pathname.startsWith("/upload")) return "Загрузка трасс";
  if (pathname.startsWith("/groups/")) return "Детали группы";
  if (pathname.startsWith("/groups")) return "Репозиторий трасс";
  return "Панель управления";
}

export default function Layout({ children }) {
  const { user, isAdmin, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <img src={logo} alt="Логотип" className="sidebar-logo" />
          <div className="sidebar-brand-text">
            <div className="sidebar-brand-title">Trace Repo</div>
            <div className="sidebar-brand-subtitle">network traffic</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink
            to="/groups"
            className={({ isActive }) => (isActive ? "sidebar-link active" : "sidebar-link")}
          >
            Группы трасс
          </NavLink>

          <NavLink
            to="/upload"
            className={({ isActive }) => (isActive ? "sidebar-link active" : "sidebar-link")}
          >
            Загрузка трасс
          </NavLink>

          {isAdmin && (
            <NavLink
              to="/users"
              className={({ isActive }) => (isActive ? "sidebar-link active" : "sidebar-link")}
            >
              Пользователи
            </NavLink>
          )}
        </nav>

        <div className="sidebar-footer">
          <button className="btn btn-secondary sidebar-logout" onClick={handleLogout}>
            Выйти
          </button>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div>
            <div className="topbar-title">{PageHeaderTitle(location.pathname)}</div>
            <div className="topbar-subtitle">
              Репозиторий трасс сетевого трафика
            </div>
          </div>

          <div className="topbar-user">
            <div className="topbar-user-name">
              {user?.first_name} {user?.last_name}
            </div>
            <div className="topbar-user-org">{user?.organization}</div>
          </div>
        </header>

        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}