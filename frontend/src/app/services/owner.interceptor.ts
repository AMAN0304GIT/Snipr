import { HttpInterceptorFn } from '@angular/common/http';
import { environment } from '../../environments/environment';

const KEY = 'snipr_owner_id';

function getOwnerId(): string {
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(KEY, id);
  }
  return id;
}

export const ownerInterceptor: HttpInterceptorFn = (req, next) => {
  if (req.url.startsWith(environment.apiUrl)) {
    req = req.clone({ setHeaders: { 'X-Owner-Id': getOwnerId() } });
  }
  return next(req);
};