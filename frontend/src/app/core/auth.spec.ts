import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AuthService, authInterceptor } from './auth';

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

  it('el login manda un formulario, como pide el backend', async () => {
    const login = TestBed.inject(AuthService).login('ana@colmado.do', 'a+b c');
    const req = backend.expectOne('/api/auth/login');
    expect(req.request.headers.get('Content-Type')).toBe('application/x-www-form-urlencoded');
    expect(req.request.body).toBe('username=ana%40colmado.do&password=a%2Bb+c');
    req.flush({ access_token: 'nuevo' });
    await Promise.resolve();
    backend.expectOne('/api/auth/me').flush({ nombre: 'Ana' });
    await login;
    expect(localStorage.getItem('bodeguita_token')).toBe('nuevo');
  });

  it('cierra la sesión si el backend responde 401', () => {
    localStorage.setItem('bodeguita_token', 'vencido');
    http.get('/api/auth/me').subscribe({ error: () => {} });
    backend.expectOne('/api/auth/me').flush(null, { status: 401, statusText: 'Unauthorized' });
    expect(localStorage.getItem('bodeguita_token')).toBeNull();
  });
});
