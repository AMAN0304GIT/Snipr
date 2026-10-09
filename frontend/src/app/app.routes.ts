import { Routes } from '@angular/router';
import { AnalyticsComponent } from './pages/analytics/analytics.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { HomeComponent } from './pages/home/home.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'analytics/:code', component: AnalyticsComponent },
  { path: '**', redirectTo: '' },
];