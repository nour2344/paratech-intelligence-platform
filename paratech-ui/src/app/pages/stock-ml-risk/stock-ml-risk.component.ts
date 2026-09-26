import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';

import {
  StockMlAnalysisResponse,
  StockMlProduct,
  StockMlRiskService,
} from '../../core/services/stock-ml-risk.service';

@Component({
  selector: 'app-stock-ml-risk',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stock-ml-risk.component.html',
  styleUrls: ['./stock-ml-risk.component.scss'],
})
export class StockMlRiskComponent {
  productQuery = '';
  products: StockMlProduct[] = [];
  selectedProduct: StockMlProduct | null = null;
  analysis: StockMlAnalysisResponse | null = null;

  loadingSearch = false;
  loadingAnalysis = false;

  searchMessage = '';
  errorMessage = '';
  analysisError = '';

  constructor(private stockMlRiskService: StockMlRiskService) {}

  searchProducts(): void {
    const query = this.productQuery.trim();

    this.errorMessage = '';
    this.searchMessage = '';
    this.products = [];

    if (!query) {
      this.errorMessage = 'Veuillez saisir un nom de produit.';
      return;
    }

    if (query.length < 2) {
      this.errorMessage = 'Veuillez saisir au moins 2 caractères.';
      return;
    }

    this.loadingSearch = true;

    this.stockMlRiskService
      .searchProducts(query)
      .pipe(finalize(() => (this.loadingSearch = false)))
      .subscribe({
        next: (response) => {
          this.products = response.results ?? [];

          if (this.products.length === 0) {
            this.searchMessage = 'Aucun produit trouvé.';
          } else {
            this.searchMessage = `${this.products.length} produit(s) trouvé(s). Cliquez sur un produit pour lancer l’analyse.`;
          }
        },
        error: () => {
          this.errorMessage =
            'Erreur lors de la recherche du produit. Vérifiez que le backend est lancé et que /stock-ml/search fonctionne.';
        },
      });
  }

  analyzeProduct(product: StockMlProduct): void {
    this.selectedProduct = product;
    this.analysis = null;
    this.analysisError = '';
    this.loadingAnalysis = true;

    this.stockMlRiskService
      .analyzeProduct(product.product_name)
      .pipe(finalize(() => (this.loadingAnalysis = false)))
      .subscribe({
        next: (response) => {
          this.analysis = response;
        },
        error: () => {
          this.analysisError =
            'Erreur lors de l’analyse du produit. Vérifiez que /stock-ml/analyze fonctionne.';
        },
      });
  }

  getRiskClass(level: string | undefined): string {
    switch ((level || '').toLowerCase()) {
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

  getAlertClass(severity: string | undefined): string {
    const value = (severity || '').toUpperCase();

    switch (value) {
      case 'CRITIQUE':
      case 'CRITICAL':
        return 'critical';
      case 'WARNING':
      case 'AVERTISSEMENT':
        return 'warning';
      default:
        return 'info';
    }
  }

  formatConfidence(value: number | undefined): string {
    if (value === null || value === undefined) {
      return '—';
    }
    return `${Math.round(value * 100)}%`;
  }

  formatNumber(value: number | undefined): string {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '—';
    }

    if (Number.isInteger(value)) {
      return `${value}`;
    }

    return value.toFixed(2);
  }
}