import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, Router } from '@angular/router';

function getStoredRole(): string | null {
  const directRole = localStorage.getItem('role');

  if (directRole) {
    return directRole.toUpperCase();
  }

  const userRaw = localStorage.getItem('user');

  if (!userRaw) {
    return null;
  }

  try {
    const user = JSON.parse(userRaw);
    return user?.role ? String(user.role).toUpperCase() : null;
  } catch {
    return null;
  }
}

function redirectByRole(router: Router, role: string | null): void {
  switch (role) {
    case 'OWNER':
      router.navigate(['/owner/dashboard']);
      break;
    case 'PHARMACIST':
      router.navigate(['/pharmacist/dashboard']);
      break;
    case 'CASHIER':
      router.navigate(['/cashier/dashboard']);
      break;
    case 'CLIENT':
      router.navigate(['/client/recommendations']);
      break;
    default:
      router.navigate(['/login']);
  }
}

export const roleGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const router = inject(Router);

  const expectedRole = String(route.data['role'] || '').toUpperCase();
  const currentRole = getStoredRole();
  const token =
    localStorage.getItem('access_token') ||
    localStorage.getItem('token');

  if (!token || !currentRole) {
    router.navigate(['/login']);
    return false;
  }

  if (currentRole !== expectedRole) {
    redirectByRole(router, currentRole);
    return false;
  }

  return true;
};
