import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';

import { AuthService } from '../core/auth';

@Component({
  selector: 'app-inicio',
  imports: [MatButtonModule, MatToolbarModule],
  template: `
    <mat-toolbar>
      <span>Bodeguita</span>
      <span class="espacio"></span>
      <button mat-button (click)="auth.cerrarSesion()">Salir</button>
    </mat-toolbar>
    <main>
      <h1>Hola, {{ auth.usuario()?.nombre }}</h1>
      <p>Entraste como {{ auth.usuario()?.rol }}.</p>
    </main>
  `,
  styles: `
    .espacio {
      flex: 1;
    }
    main {
      padding: 16px;
    }
  `,
})
export class Inicio {
  protected auth = inject(AuthService);
}
