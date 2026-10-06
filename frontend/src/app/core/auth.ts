import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, firstValueFrom, throwError } from 'rxjs';

export interface Usuario {
  id_usuario: number;
  id_negocio: number;
  nombre: string;
  email: string;
  rol: 'dueno' | 'cajero';
  activo: boolean;
}

// localStorage para que la PWA no pida login cada vez que se abre en el celular.
// Límite conocido: un XSS podría leerlo (ver docs/EVALUACION-TECNOLOGIAS.md §6).
const CLAVE_TOKEN = 'bodeguita_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  readonly usuario = signal<Usuario | null>(null);

  get token(): string | null {
    return localStorage.getItem(CLAVE_TOKEN);
  }

  async login(email: string, password: string): Promise<void> {
    // El login de FastAPI (OAuth2) pide formulario, no JSON. Se manda como texto ya
    // codificado: HttpClient no serializa URLSearchParams y HttpParams deja '+' sin codificar.
    const form = new URLSearchParams({ username: email, password }).toString();
    const { access_token } = await firstValueFrom(
      this.http.post<{ access_token: string }>('/api/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      }),
    );
    localStorage.setItem(CLAVE_TOKEN, access_token);
    await this.cargarUsuario();
  }

  /** Recupera la sesión guardada. Devuelve false si no hay o ya venció. */
  async cargarUsuario(): Promise<boolean> {
    if (!this.token) return false;
    try {
      this.usuario.set(await firstValueFrom(this.http.get<Usuario>('/api/auth/me')));
      return true;
    } catch {
      this.cerrarSesion();
      return false;
    }
  }

  cerrarSesion(): void {
    localStorage.removeItem(CLAVE_TOKEN);
    this.usuario.set(null);
    this.router.navigate(['/login']);
  }
}

/** Adjunta el token a cada petición y cierra la sesión si el backend responde 401. */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.token;
  const conToken = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
  return next(conToken).pipe(
    catchError((err) => {
      if (token && err instanceof HttpErrorResponse && err.status === 401) auth.cerrarSesion();
      return throwError(() => err);
    }),
  );
};

export const authGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router); // inject() no funciona después de un await
  if (auth.usuario() || (await auth.cargarUsuario())) return true;
  return router.createUrlTree(['/login']);
};
