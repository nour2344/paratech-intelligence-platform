import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

function getToken(): string | null {
  return (
    localStorage.getItem('access_token') ||
    localStorage.getItem('token')
  );
}

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const token = getToken();

  if (!token) {
    router.navigate(['/login']);
    return false;
  }

  return true;
};
