import React from 'react';
import { Database, MessageSquare } from 'lucide-react';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="layout animate-fade-in">
      <nav className="sidebar glass-panel">
        <div className="logo">
          <Database className="icon-primary" />
          <span>OmniRAG</span>
        </div>
        <ul className="nav-links">
          <li className="active">
            <MessageSquare size={20} />
            <span>Chat</span>
          </li>
        </ul>
      </nav>
      <main className="main-content">
        <header className="header glass-panel">
          <h1>Document Assistant</h1>
          <p>Ask anything about your data using AI.</p>
        </header>
        <div className="content-area">
          {children}
        </div>
      </main>
    </div>
  );
}
