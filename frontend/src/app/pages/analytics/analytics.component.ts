import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Analytics, CountItem } from '../../models/link.model';
import { LinkService } from '../../services/link.service';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <a routerLink="/dashboard" class="muted small">← Back to dashboard</a>
    <p class="error" *ngIf="error">{{ error }}</p>

    <ng-container *ngIf="data">
      <h2 class="title">{{ data.short_url }}</h2>
      <p class="muted truncate">{{ data.original_url }}</p>

      <div class="stats">
        <div class="card stat">
          <span class="muted small">Total clicks</span>
          <strong>{{ data.total_clicks }}</strong>
        </div>
        <div class="card stat">
          <span class="muted small">Top device</span>
          <strong>{{ topLabel(data.devices) }}</strong>
        </div>
        <div class="card stat">
          <span class="muted small">Top browser</span>
          <strong>{{ topLabel(data.browsers) }}</strong>
        </div>
      </div>

      <div class="card">
        <h3>Clicks, last 14 days</h3>
        <div class="chart">
          <div class="col" *ngFor="let d of data.clicks_by_day">
            <span class="val">{{ d.count || '' }}</span>
            <div class="bar-area">
              <div class="bar" [style.height.%]="pct(d.count, data.clicks_by_day)"></div>
            </div>
            <span class="lbl">{{ d.label }}</span>
          </div>
        </div>
      </div>

      <div class="grid3">
        <div class="card" *ngFor="let s of sections">
          <h3>{{ s.title }}</h3>
          <p class="muted small" *ngIf="!s.items.length">No clicks yet</p>
          <div class="hbar" *ngFor="let i of s.items">
            <div class="hbar-top">
              <span class="truncate">{{ i.label }}</span>
              <span>{{ i.count }}</span>
            </div>
            <div class="track"><div class="fill" [style.width.%]="pct(i.count, s.items)"></div></div>
          </div>
        </div>
      </div>
    </ng-container>
  `,
})
export class AnalyticsComponent implements OnInit {
  data: Analytics | null = null;
  sections: { title: string; items: CountItem[] }[] = [];
  error = '';

  constructor(private route: ActivatedRoute, private links: LinkService) {}

  ngOnInit() {
    const code = this.route.snapshot.paramMap.get('code')!;
    this.links.analytics(code).subscribe({
      next: (d) => {
        this.data = d;
        this.sections = [
          { title: 'Devices', items: d.devices },
          { title: 'Browsers', items: d.browsers },
          { title: 'Referrers', items: d.referrers },
        ];
      },
      error: () => (this.error = 'Could not load analytics for this link.'),
    });
  }

  pct(count: number, items: CountItem[]): number {
    const max = Math.max(1, ...items.map((i) => i.count));
    return (count / max) * 100;
  }

  topLabel(items: CountItem[]): string {
    return items.length ? items[0].label : '-';
  }
}