import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { Analytics, CreateLinkRequest, ShortLink } from '../models/link.model';

@Injectable({ providedIn: 'root' })
export class LinkService {
  private api = `${environment.apiUrl}/api/links`;

  constructor(private http: HttpClient) {}

  create(body: CreateLinkRequest) {
    return this.http.post<ShortLink>(this.api, body);
  }

  list() {
    return this.http.get<ShortLink[]>(this.api);
  }

  remove(code: string) {
    return this.http.delete<void>(`${this.api}/${code}`);
  }

  analytics(code: string) {
    return this.http.get<Analytics>(`${this.api}/${code}/analytics`);
  }
}