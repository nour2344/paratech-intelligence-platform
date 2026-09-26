import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  RecommendationHistory,
  RecommendationService,
  RecommendedProduct,
} from '../../core/services/recommendation.service';

@Component({
  selector: 'app-recommendation',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './recommendation.component.html',
  styleUrl: './recommendation.component.scss',
})
export class RecommendationComponent implements OnInit {
  query = '';

  category = '';
  maxPrice: number | null = null;

  products: RecommendedProduct[] = [];
  history: RecommendationHistory[] = [];

  loading = false;
  loadingHistory = false;

  errorMessage = '';
  successMessage = '';

  isClientPage = false;
  selectedHistoryIndexes = new Set<number>();

  private userId = 1;

  constructor(
    private recommendationService: RecommendationService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.isClientPage = this.router.url.startsWith('/client');
    this.loadHistory();
  }

  generateRecommendation(): void {
    this.errorMessage = '';
    this.successMessage = '';
    this.products = [];

    if (!this.query.trim()) {
      this.errorMessage = 'Veuillez saisir un produit ou un besoin.';
      return;
    }

    this.loading = true;

    this.recommendationService
      .predict({
        user_id: this.userId,
        query: this.query.trim(),
        input_data: {
          mode: 'content_based',
          product_name: this.query.trim(),
        },
      })
      .subscribe({
        next: (response) => {
          this.products = response.recommended_products || [];
          this.successMessage = 'Recommandations générées avec succès.';
          this.loading = false;
          this.loadHistory();
        },
        error: (error) => {
          this.errorMessage = this.extractErrorMessage(
            error,
            'Erreur lors de la recommandation.'
          );
          this.loading = false;
        },
      });
  }

  generatePreferenceRecommendation(): void {
    this.errorMessage = '';
    this.successMessage = '';
    this.products = [];

    this.loading = true;

    const queryParts: string[] = [];

    if (this.category) {
      queryParts.push(`catégorie ${this.category}`);
    }

    if (this.maxPrice !== null && this.maxPrice !== undefined) {
      queryParts.push(`prix maximum ${this.maxPrice}`);
    }

    const generatedQuery =
      queryParts.length > 0
        ? queryParts.join(', ')
        : 'recommandation générale produits parapharmacie';

    this.recommendationService
      .predict({
        user_id: this.userId,
        query: generatedQuery,
        input_data: {
          mode: 'preference_based',
          category: this.category || null,
          max_price: this.maxPrice,
        },
      })
      .subscribe({
        next: (response) => {
          this.products = response.recommended_products || [];
          this.successMessage = 'Recommandations générées avec succès.';
          this.loading = false;
          this.loadHistory();
        },
        error: (error) => {
          this.errorMessage = this.extractErrorMessage(
            error,
            'Erreur lors de la recommandation.'
          );
          this.loading = false;
        },
      });
  }

  loadHistory(): void {
    this.loadingHistory = true;
    this.selectedHistoryIndexes.clear();

    this.recommendationService.getUserHistory(this.userId).subscribe({
      next: (history) => {
        this.history = history || [];
        this.loadingHistory = false;
      },
      error: () => {
        this.history = [];
        this.loadingHistory = false;
      },
    });
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('user');

    this.router.navigate(['/login']);
  }

  isHistorySelected(index: number): boolean {
    return this.selectedHistoryIndexes.has(index);
  }

  toggleHistorySelection(index: number): void {
    if (this.selectedHistoryIndexes.has(index)) {
      this.selectedHistoryIndexes.delete(index);
    } else {
      this.selectedHistoryIndexes.add(index);
    }
  }

  selectAllHistory(): void {
    this.selectedHistoryIndexes.clear();

    this.history.forEach((_, index) => {
      this.selectedHistoryIndexes.add(index);
    });
  }

  clearHistorySelection(): void {
    this.selectedHistoryIndexes.clear();
  }

  deleteSelectedHistory(): void {
    if (this.selectedHistoryIndexes.size === 0) {
      return;
    }

    this.history = this.history.filter(
      (_, index) => !this.selectedHistoryIndexes.has(index)
    );

    this.selectedHistoryIndexes.clear();
    this.successMessage = 'Les recommandations sélectionnées ont été supprimées.';
  }

  deleteOneHistory(index: number): void {
    this.history = this.history.filter((_, itemIndex) => itemIndex !== index);
    this.selectedHistoryIndexes.delete(index);
    this.successMessage = 'La recommandation a été supprimée.';
  }

  getProductName(product: RecommendedProduct): string {
    return product.product_name || product.name || 'Produit recommandé';
  }

  formatScore(score: number | null | undefined): string {
    if (score === null || score === undefined) {
      return '';
    }

    if (score <= 1) {
      return `${Math.round(score * 100)}%`;
    }

    return `${Math.round(score)}%`;
  }

  parseRecommendedProducts(value: string): RecommendedProduct[] {
    try {
      return JSON.parse(value);
    } catch {
      return [];
    }
  }

  getHistoryTitle(item: RecommendationHistory): string {
    const historyItem = item as any;

    return (
      historyItem.query ||
      historyItem.category ||
      historyItem.search_query ||
      'Recherche client'
    );
  }

  getHistoryDate(item: RecommendationHistory): string {
    const historyItem = item as any;

    return (
      historyItem.created_at ||
      historyItem.date ||
      historyItem.createdAt ||
      'Date non disponible'
    );
  }

  getHistoryProducts(item: RecommendationHistory): RecommendedProduct[] {
    const historyItem = item as any;

    if (Array.isArray(historyItem.products)) {
      return historyItem.products;
    }

    if (Array.isArray(historyItem.recommended_products)) {
      return historyItem.recommended_products;
    }

    if (typeof historyItem.recommended_products === 'string') {
      return this.parseRecommendedProducts(historyItem.recommended_products);
    }

    if (typeof historyItem.products === 'string') {
      return this.parseRecommendedProducts(historyItem.products);
    }

    return [];
  }

  private extractErrorMessage(error: any, fallback: string): string {
    const detail = error?.error?.detail || error?.error?.message || error?.message;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => item?.msg || item?.message || JSON.stringify(item))
        .join(' ');
    }

    return fallback;
  }
}