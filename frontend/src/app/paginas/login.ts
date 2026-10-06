import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { Router } from '@angular/router';

import { AuthService } from '../core/auth';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatInputModule],
  template: `
    <main>
      <mat-card appearance="outlined">
        <mat-card-header>
          <mat-card-title>Bodeguita</mat-card-title>
          <mat-card-subtitle>Entra a tu colmado</mat-card-subtitle>
        </mat-card-header>
        <form [formGroup]="form" (ngSubmit)="entrar()">
          <mat-card-content>
            <mat-form-field appearance="outline">
              <mat-label>Correo</mat-label>
              <input matInput type="email" formControlName="email" autocomplete="email" />
            </mat-form-field>
            <mat-form-field appearance="outline">
              <mat-label>Contraseña</mat-label>
              <input
                matInput
                type="password"
                formControlName="password"
                autocomplete="current-password"
              />
            </mat-form-field>
            @if (error()) {
              <p class="error" role="alert">{{ error() }}</p>
            }
          </mat-card-content>
          <mat-card-actions>
            <button mat-flat-button type="submit" [disabled]="cargando()">
              {{ cargando() ? 'Entrando…' : 'Entrar' }}
            </button>
          </mat-card-actions>
        </form>
      </mat-card>
    </main>
  `,
  styles: `
    main {
      min-height: 100dvh;
      display: grid;
      place-items: center;
      padding: 16px;
      box-sizing: border-box;
    }
    mat-card {
      width: 100%;
      max-width: 380px;
    }
    mat-form-field,
    button {
      width: 100%;
    }
    mat-card-content {
      padding-top: 16px;
    }
    .error {
      color: var(--mat-sys-error);
      margin: 0 0 8px;
    }
  `,
})
export class Login {
  private auth = inject(AuthService);
  private router = inject(Router);

  protected form = inject(NonNullableFormBuilder).group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });
  protected cargando = signal(false);
  protected error = signal('');

  async entrar() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.cargando.set(true);
    this.error.set('');
    try {
      const { email, password } = this.form.getRawValue();
      await this.auth.login(email, password);
      await this.router.navigate(['/']);
    } catch (e) {
      this.error.set(
        e instanceof HttpErrorResponse && e.status === 401
          ? 'Correo o contraseña incorrectos.'
          : 'No se pudo conectar. Revisa tu internet e intenta de nuevo.',
      );
    } finally {
      this.cargando.set(false);
    }
  }
}
