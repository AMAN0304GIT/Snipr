import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ShortLink } from '../../models/link.model';
import { LinkService } from '../../services/link.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="page-head">
      <h2>Your links</h2>
      <a class="btn primary" routerLink="/">+ New link</a>
    </div>

    <input
      class="input search"
      placeholder="Search links…"
      [ngModel]="query"
      (ngModelChange)="onSearch($event)"
    />

    <p class="error" *ngIf="error">{{ error }}</p>
    <p class="muted" *ngIf="loading">
      Loading…
      <span *ngIf="slow">(waking up the server, this can take up to a minute)</span>
    </p>

    <div class="card table-wrap" *ngIf="!loading && !error">
      <table *ngIf="filtered.length; else empty">
        <thead>
          <tr>
            <th>Short link</th>
            <th>Original URL</th>
            <th>Clicks</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let l of filtered">
            <td>
              <a [href]="l.short_url" target="_blank" rel="noopener">/{{ l.code }}</a>
              <span class="badge" *ngIf="isExpired(l)">Expired</span>
            </td>
            <td class="url-cell" [title]="l.original_url">{{ l.original_url }}</td>
            <td>{{ l.click_count }}</td>
            <td>{{ l.created_at | date: 'mediumDate' }}</td>
            <td class="actions">
              <button class="btn sm" (click)="copy(l)">{{ copiedCode === l.code ? 'Copied ✓' : 'Copy' }}</button>
              <a class="btn sm" [routerLink]="['/analytics', l.code]">Stats</a>
              <button class="btn sm danger" (click)="remove(l)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <ng-template #empty>
        <p class="muted pad">No links found. Create your first one!</p>
      </ng-template>
    </div>
  `,
})
export class DashboardComponent implements OnInit {
  links: ShortLink[] = [];
  filtered: ShortLink[] = [];
  query = '';
  loading = true;
  slow = false;
  error = '';
  copiedCode = '';

  constructor(private service: LinkService) {}

  ngOnInit() {
    const timer = setTimeout(() => (this.slow = this.loading), 4000);
    this.service.list().subscribe({
      next: (data) => {
        clearTimeout(timer);
        this.links = data;
        this.applyFilter();
        this.loading = false;
      },
      error: () => {
        clearTimeout(timer);
        this.loading = false;
        this.error = 'Could not load your links. The server may be waking up, please refresh in a minute.';
      },
    });
  }

  onSearch(value: string) {
    this.query = value;
    this.applyFilter();
  }

  private applyFilter() {
    const q = this.query.trim().toLowerCase();
    this.filtered = this.links.filter(
      (l) => l.code.toLowerCase().includes(q) || l.original_url.toLowerCase().includes(q)
    );
  }

  isExpired(l: ShortLink): boolean {
    return !!l.expires_at && new Date(l.expires_at) < new Date();
  }

  copy(l: ShortLink) {
    navigator.clipboard.writeText(l.short_url).then(() => {
      this.copiedCode = l.code;
      setTimeout(() => (this.copiedCode = ''), 1500);
    });
  }

  remove(l: ShortLink) {
    if (!confirm(`Delete ${l.short_url}?`)) return;
    this.service.remove(l.code).subscribe(() => {
      this.links = this.links.filter((x) => x.code !== l.code);
      this.applyFilter();
    });
  }
}