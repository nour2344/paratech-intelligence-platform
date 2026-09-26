import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import {
  DemandBusinessSummary,
  DemandForecastResponse,
  DemandProduct,
  DemandService,
} from '../../core/services/demand.service';

@Component({
  selector: 'app-demand-forecast',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './demand-forecast.component.html',
  styleUrls: ['./demand-forecast.component.scss'],
})
export class DemandForecastComponent implements OnInit {
  products: DemandProduct[] = [];
  filteredProducts: DemandProduct[] = [];
  categories: string[] = [];

  selectedProductName = '';
  productSearch = '';
  selectedCategory = '';
  horizon = 30;

  result: DemandForecastResponse | null = null;
  summary: DemandBusinessSummary | null = null;

  loadingProducts = false;
  loadingForecast = false;

  errorMessage = '';
  successMessage = '';

  constructor(private demandService: DemandService) {}

  ngOnInit(): void {
    this.loadProducts();
  }

  loadProducts(): void {
    this.loadingProducts = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.demandService
      .getProducts()
      .pipe(finalize(() => (this.loadingProducts = false)))
      .subscribe({
        next: (response) => {
          this.products = response.products ?? [];
          this.categories = this.extractCategories(this.products);
          this.applyFilters();
        },
        error: (error) => {
          console.error('Demand products error:', error);
          this.errorMessage =
            'Erreur lors du chargement des produits. Vérifiez que le backend est lancé.';
        },
      });
  }

  extractCategories(products: DemandProduct[]): string[] {
    const values = products
      .map((product) => product.category || '')
      .filter((category) => category.trim().length > 0);

    return Array.from(new Set(values)).sort();
  }

  applyFilters(): void {
    const query = this.productSearch.trim().toLowerCase();
    const category = this.selectedCategory.trim().toLowerCase();

    this.filteredProducts = this.products
      .filter((product) => {
        const matchesName = !query
          ? true
          : product.product_name.toLowerCase().includes(query);

        const matchesCategory = !category
          ? true
          : (product.category || '').toLowerCase() === category;

        return matchesName && matchesCategory;
      })
      .slice(0, 80);
  }

  filterProducts(): void {
    this.selectedProductName = '';
    this.result = null;
    this.summary = null;
    this.successMessage = '';
    this.errorMessage = '';

    this.applyFilters();
  }

  onCategoryChange(): void {
    this.selectedProductName = '';
    this.productSearch = '';
    this.result = null;
    this.summary = null;
    this.successMessage = '';
    this.errorMessage = '';

    this.applyFilters();
  }

  selectProduct(product: DemandProduct): void {
    this.selectedProductName = product.product_name;
    this.productSearch = product.product_name;

    this.result = null;
    this.summary = null;
    this.successMessage = '';
    this.errorMessage = '';

    this.applyFilters();
  }

  generateForecast(): void {
    const productName = this.selectedProductName || this.productSearch.trim();

    this.errorMessage = '';
    this.successMessage = '';
    this.result = null;
    this.summary = null;

    if (!productName) {
      this.errorMessage = 'Veuillez choisir un produit.';
      return;
    }

    if (!this.horizon || Number(this.horizon) < 1) {
      this.errorMessage = 'Veuillez saisir une période valide.';
      return;
    }

    if (Number(this.horizon) > 365) {
      this.errorMessage =
        'Veuillez choisir une période inférieure ou égale à 365 jours.';
      return;
    }

    this.loadingForecast = true;

    this.demandService
      .forecastByName(productName, Number(this.horizon))
      .pipe(finalize(() => (this.loadingForecast = false)))
      .subscribe({
        next: (response) => {
          this.result = response;
          this.summary = this.demandService.buildBusinessSummary(response);
          this.successMessage = 'Prévision générée avec succès.';
        },
        error: (error) => {
          console.error('Demand forecast error:', error);

          this.errorMessage =
            'Ce produit ne dispose pas encore d’un historique de ventes suffisant pour générer une prévision fiable. Veuillez choisir un autre produit.';
        },
      });
  }

  getStatusClass(status: string | undefined): string {
    switch ((status || '').toLowerCase()) {
      case 'high':
        return 'high';
      case 'medium':
        return 'medium';
      case 'low':
        return 'low';
      default:
        return '';
    }
  }

  formatNumber(value: number | undefined | null): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '—';
    }

    return value.toFixed(2);
  }

  formatQuantity(value: number | undefined | null): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '—';
    }

    return Math.round(value).toString();
  }
}