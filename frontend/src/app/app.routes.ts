import { Routes } from '@angular/router';

import { authGuard } from './core/auth';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./paginas/login').then((m) => m.Login) },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./paginas/inicio').then((m) => m.Inicio),
  },
  { path: '**', redirectTo: '' },
];
