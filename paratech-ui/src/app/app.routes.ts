import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/landing/landing.component').then(
        (m) => m.LandingComponent
      ),
  },

  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login.component').then(
        (m) => m.LoginComponent
      ),
  },

  {
    path: 'register',
    loadComponent: () =>
      import('./pages/register/register.component').then(
        (m) => m.RegisterComponent
      ),
  },

  {
  path: 'client',
  canActivate: [authGuard, roleGuard],
  data: { role: 'CLIENT' },
  children: [
    {
      path: '',
      redirectTo: 'recommendations',
      pathMatch: 'full',
    },
    {
      path: 'dashboard',
      redirectTo: 'recommendations',
      pathMatch: 'full',
    },
    {
      path: 'history',
      redirectTo: 'recommendations',
      pathMatch: 'full',
    },
    {
      path: 'recommendations',
      loadComponent: () =>
        import('./pages/recommendation/recommendation.component').then(
          (m) => m.RecommendationComponent
        ),
    },
  ],
},

  {
    path: 'owner',
    canActivate: [authGuard, roleGuard],
    data: { role: 'OWNER' },
    loadComponent: () =>
      import('./layouts/owner-layout/owner-layout.component').then(
        (m) => m.OwnerLayoutComponent
      ),
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./pages/owner-dashboard/owner-dashboard.component').then(
            (m) => m.OwnerDashboardComponent
          ),
      },
      {
        path: 'powerbi',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
      {
        path: 'stock-ml',
        loadComponent: () =>
          import('./pages/stock-ml-risk/stock-ml-risk.component').then(
            (m) => m.StockMlRiskComponent
          ),
      },
      {
        path: 'stock',
        redirectTo: 'stock-ml',
        pathMatch: 'full',
      },
      {
        path: 'demand',
        loadComponent: () =>
          import('./pages/demand-forecast/demand-forecast.component').then(
            (m) => m.DemandForecastComponent
          ),
      },
      {
        path: 'alerts',
        loadComponent: () =>
          import('./pages/alerts/alerts.component').then(
            (m) => m.AlertsComponent
          ),
      },
      {
        path: 'client-history',
        loadComponent: () =>
          import('./pages/client-history/client-history.component').then(
            (m) => m.ClientHistoryComponent
          ),
      },
    ],
  },

  {
  path: 'pharmacist',
  canActivate: [authGuard, roleGuard],
  data: { role: 'PHARMACIST' },
  loadComponent: () =>
    import('./layouts/pharmacist-layout/pharmacist-layout.component').then(
      (m) => m.PharmacistLayoutComponent
    ),
  children: [
    {
      path: '',
      redirectTo: 'dashboard',
      pathMatch: 'full',
    },
    {
      path: 'dashboard',
      loadComponent: () =>
        import(
          './pages/pharmacist-dashboard/pharmacist-dashboard.component'
        ).then((m) => m.PharmacistDashboardComponent),
    },
    {
      path: 'powerbi',
      redirectTo: 'dashboard',
      pathMatch: 'full',
    },
    {
      path: 'barcode',
      loadComponent: () =>
        import('./pages/barcode/barcode.component').then(
          (m) => m.BarcodeComponent
        ),
    },
    {
      path: 'recommendations',
      loadComponent: () =>
        import('./pages/recommendation/recommendation.component').then(
          (m) => m.RecommendationComponent
        ),
    },
    {
      path: 'stock-ml',
      loadComponent: () =>
        import('./pages/stock-ml-risk/stock-ml-risk.component').then(
          (m) => m.StockMlRiskComponent
        ),
    },
    {
      path: 'stock',
      redirectTo: 'stock-ml',
      pathMatch: 'full',
    },
  ],
},

  {
  path: 'cashier',
  canActivate: [authGuard, roleGuard],
  data: { role: 'CASHIER' },
  loadComponent: () =>
    import('./layouts/cashier-layout/cashier-layout.component').then(
      (m) => m.CashierLayoutComponent
    ),
  children: [
    {
      path: '',
      redirectTo: 'dashboard',
      pathMatch: 'full',
    },
    {
      path: 'dashboard',
      loadComponent: () =>
        import('./pages/cashier-dashboard/cashier-dashboard.component').then(
          (m) => m.CashierDashboardComponent
        ),
    },
    {
      path: 'powerbi',
      redirectTo: 'dashboard',
      pathMatch: 'full',
    },
    {
      path: 'barcode',
      loadComponent: () =>
        import('./pages/barcode/barcode.component').then(
          (m) => m.BarcodeComponent
        ),
    },
    {
      path: 'stock-ml',
      loadComponent: () =>
        import('./pages/stock-ml-risk/stock-ml-risk.component').then(
          (m) => m.StockMlRiskComponent
        ),
    },
    {
      path: 'stock',
      redirectTo: 'stock-ml',
      pathMatch: 'full',
    },
  ],
},
  {
    path: '**',
    redirectTo: '',
  },
];