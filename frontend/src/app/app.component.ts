import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <header class="nav">
      <div class="container nav-inner">
        <a routerLink="/" class="brand">⚡ Snipr</a>
        <nav>
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Home</a>
          <a routerLink="/dashboard" routerLinkActive="active">Dashboard</a>
          <button class="icon-btn" (click)="toggleTheme()" aria-label="Toggle theme">
            {{ dark ? '☀️' : '🌙' }}
          </button>
        </nav>
      </div>
    </header>

    <main class="container">
      <router-outlet />
    </main>

    <footer class="container muted small">Snipr · built with FastAPI + Angular</footer>
  `,
})
export class AppComponent {
  dark = localStorage.getItem('snipr_theme') === 'dark';

  constructor() {
    this.apply();
  }

  toggleTheme() {
    this.dark = !this.dark;
    localStorage.setItem('snipr_theme', this.dark ? 'dark' : 'light');
    this.apply();
  }

  private apply() {
    document.documentElement.setAttribute('data-theme', this.dark ? 'dark' : 'light');
  }
}