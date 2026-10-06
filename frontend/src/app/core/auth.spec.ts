import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { authInterceptor } from './auth';

describe('authInterceptor', () => {
  let http: HttpClient;
  let backend: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideRouter([{ path: 'login', children: [] }]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
  });

  it('adjunta el token guardado', () => {
    localStorage.setItem('bodeguita_token', 'abc');
    http.get('/api/auth/me').subscribe();
    expect(backend.expectOne('/api/auth/me').request.headers.get('Authorization')).toBe(
      'Bearer abc',
    );
  });

  it('cierra la sesión si el backend responde 401', () => {
    localStorage.setItem('bodeguita_token', 'vencido');
    http.get('/api/auth/me').subscribe({ error: () => {} });
    backend.expectOne('/api/auth/me').flush(null, { status: 401, statusText: 'Unauthorized' });
    expect(localStorage.getItem('bodeguita_token')).toBeNull();
  });
});
