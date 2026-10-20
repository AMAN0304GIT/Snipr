import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ShortLink } from '../../models/link.model';
import { LinkService } from '../../services/link.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <section class="hero">
      <h1>Shorten links. <span class="grad">Track everything.</span></h1>
      <p class="muted">Paste a long URL, get a short one, and see who clicks it.</p>
    </section>

    <form class="card shorten" (ngSubmit)="submit()">
      <div class="row">
        <input
          class="input"
          type="url"
          name="url"
          [(ngModel)]="url"
          placeholder="https://example.com/a/very/long/link"
          required
        />
        <button class="btn primary" type="submit" [disabled]="loading || !url">
          {{ loading ? 'Shortening…' : 'Shorten' }}
        </button>
      </div>
      <div class="row">
        <input
          class="input"
          name="alias"
          [(ngModel)]="alias"
          placeholder="Custom alias (optional)"
          maxlength="32"
        />
        <select class="input" name="expiry" [(ngModel)]="expiresInDays">
          <option [ngValue]="null">Never expires</option>
          <option [ngValue]="1">Expires in 1 day</option>
          <option [ngValue]="7">Expires in 7 days</option>
          <option [ngValue]="30">Expires in 30 days</option>
        </select>
      </div>
      <p class="error" *ngIf="error">{{ error }}</p>
      <p class="muted small" *ngIf="slow">
        Waking up the server (free hosting). This can take up to a minute…
      </p>
    </form>

    <div class="card result" *ngIf="result">
      <div class="result-text">
        <p class="muted small">Your short link</p>
        <a class="short" [href]="result.short_url" target="_blank" rel="noopener">{{ result.short_url }}</a>
        <p class="muted small truncate">{{ result.original_url }}</p>
      </div>
      <div class="actions">
        <button class="btn" (click)="copy()">{{ copied ? 'Copied ✓' : 'Copy' }}</button>
        <a class="btn" [routerLink]="['/analytics', result.code]">Analytics</a>
      </div>
    </div>

    <section class="features">
      <div class="card">
        <h3>⚡ Fast redirects</h3>
        <p class="muted small">Short codes are looked up by index and redirected instantly.</p>
      </div>
      <div class="card">
        <h3>📊 Click analytics</h3>
        <p class="muted small">See clicks per day, devices, browsers and referrers.</p>
      </div>
      <div class="card">
        <h3>✏️ Custom aliases</h3>
        <p class="muted small">Pick your own memorable link and set an expiry date.</p>
      </div>
    </section>
  `,
})
export class HomeComponent {
  url = '';
  alias = '';
  expiresInDays: number | null = null;
  loading = false;
  slow = false;
  error = '';
  result: ShortLink | null = null;
  copied = false;

  constructor(private links: LinkService) {}

  submit() {
    this.error = '';
    this.result = null;
    this.loading = true;
    this.slow = false;
    const timer = setTimeout(() => (this.slow = this.loading), 4000);

    this.links
      .create({
        url: this.url.trim(),
        custom_alias: this.alias.trim() || null,
        expires_in_days: this.expiresInDays,
      })
      .subscribe({
        next: (link) => {
          clearTimeout(timer);
          this.result = link;
          this.loading = false;
          this.slow = false;
          this.url = '';
          this.alias = '';
        },
        error: (err) => {
          clearTimeout(timer);
          this.loading = false;
          this.slow = false;
          this.error = this.readError(err);
        },
      });
  }

  copy() {
    if (!this.result) return;
    navigator.clipboard.writeText(this.result.short_url).then(() => {
      this.copied = true;
      setTimeout(() => (this.copied = false), 1500);
    });
  }

  private readError(err: any): string {
    const detail = err?.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return 'Please check the URL (must start with http:// or https://) and the alias (letters, numbers, - and _ only).';
    }
    if (err?.status === 429) {
      return 'Too many requests. Please wait a minute and try again.';
    }
    if (err?.status === 0) {
      return 'Cannot reach the server. If it is on a free plan it may be waking up, try again in a minute.';
    }
    return 'Something went wrong. Please try again.';
  }
}