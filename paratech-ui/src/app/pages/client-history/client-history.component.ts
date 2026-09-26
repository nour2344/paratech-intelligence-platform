import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { finalize } from 'rxjs/operators';

interface RecommendationProduct {
  name: string;
  score: number | null;
  product_id: number | null;
  category: string | null;
}

interface ClientHistoryItem {
  id?: number;
  user_id?: number;
  client_id?: number;
  client_name?: string;
  user_name?: string;
  full_name?: string;
  name?: string;
  query?: string;
  request_query?: string;
  search_query?: string;
  created_at?: string;
  date?: string;
  data_used?: unknown;
  recommended_products?: unknown;
}

interface CleanHistoryItem {
  id: number | string;
  clientId: number | string;
  clientName: string;
  query: string;
  mode: string;
  category: string;
  date: string;
  products: RecommendationProduct[];
}

@Component({
  selector: 'app-client-history',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './client-history.component.html',
  styleUrls: ['./client-history.component.scss'],
})
export class ClientHistoryComponent implements OnInit {
  private readonly apiUrl =
    'http://127.0.0.1:8000/recommendations/history/user/1';

  private readonly deleteBatchUrl =
    'http://127.0.0.1:8000/recommendations/history/delete-batch';

  history: CleanHistoryItem[] = [];
  filteredHistory: CleanHistoryItem[] = [];

  selectedIds = new Set<number>();

  searchTerm = '';
  loading = false;
  deleting = false;
  errorMessage = '';
  successMessage = '';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory(): void {
    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.selectedIds.clear();

    this.http
      .get<ClientHistoryItem[] | { history?: ClientHistoryItem[]; results?: ClientHistoryItem[] }>(
        this.apiUrl
      )
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (response) => {
          const rawHistory = Array.isArray(response)
            ? response
            : response.history ?? response.results ?? [];

          this.history = rawHistory.map((item, index) =>
            this.normalizeHistoryItem(item, index)
          );

          this.filteredHistory = [...this.history];
        },
        error: (error) => {
          console.error('Client history loading error:', error);
          this.errorMessage =
            'Erreur lors du chargement de l’historique client. Vérifiez que le backend est lancé.';
        },
      });
  }

  normalizeHistoryItem(item: ClientHistoryItem, index: number): CleanHistoryItem {
    const dataUsed = this.safeParse(item.data_used);
    const recommendedProducts = this.safeParse(item.recommended_products);

    const clientId = item.user_id ?? item.client_id ?? 1;

    const clientName =
      item.client_name ||
      item.user_name ||
      item.full_name ||
      item.name ||
      dataUsed.client_name ||
      dataUsed.user_name ||
      `Client ${clientId}`;

    const query =
      item.query ||
      item.request_query ||
      item.search_query ||
      dataUsed.product_name ||
      dataUsed.category ||
      dataUsed.query ||
      'Recherche client';

    const mode = dataUsed.mode || 'recommendation';

    const category =
      dataUsed.category ||
      this.getFirstProductCategory(recommendedProducts) ||
      'Non définie';

    return {
      id: item.id ?? index + 1,
      clientId,
      clientName,
      query,
      mode: this.formatMode(mode),
      category,
      date: this.formatDate(item.created_at ?? item.date),
      products: this.normalizeProducts(recommendedProducts),
    };
  }

  safeParse(value: unknown): any {
    if (!value) {
      return {};
    }

    if (typeof value === 'object') {
      return value;
    }

    if (typeof value === 'string') {
      try {
        return JSON.parse(value);
      } catch {
        return {};
      }
    }

    return {};
  }

  normalizeProducts(value: unknown): RecommendationProduct[] {
    if (!Array.isArray(value)) {
      return [];
    }

    return value.slice(0, 6).map((product: any) => ({
      name: product.name || product.product_name || 'Produit recommandé',
      score:
        product.score === null || product.score === undefined
          ? null
          : Number(product.score),
      product_id: product.product_id ?? product.id ?? null,
      category: product.category ?? null,
    }));
  }

  getFirstProductCategory(products: unknown): string {
    if (!Array.isArray(products) || products.length === 0) {
      return 'Non définie';
    }

    return products[0]?.category || 'Non définie';
  }

  formatMode(mode: string): string {
    switch ((mode || '').toLowerCase()) {
      case 'content_based':
        return 'Content-based';
      case 'preference_based':
        return 'Preference-based';
      case 'collaborative':
        return 'Collaborative';
      default:
        return 'Recommendation';
    }
  }

  formatDate(value: string | undefined): string {
    if (!value) {
      return 'Date inconnue';
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return new Intl.DateTimeFormat('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  }

  filterHistory(): void {
    const query = this.searchTerm.trim().toLowerCase();

    if (!query) {
      this.filteredHistory = [...this.history];
      return;
    }

    this.filteredHistory = this.history.filter((item) => {
      const productNames = item.products
        .map((product) => product.name)
        .join(' ')
        .toLowerCase();

      return (
        item.clientName.toLowerCase().includes(query) ||
        item.query.toLowerCase().includes(query) ||
        item.category.toLowerCase().includes(query) ||
        item.mode.toLowerCase().includes(query) ||
        productNames.includes(query)
      );
    });
  }

  clearSearch(): void {
    this.searchTerm = '';
    this.filteredHistory = [...this.history];
  }

  getNumericId(id: number | string): number | null {
    const numericId = Number(id);
    return Number.isFinite(numericId) ? numericId : null;
  }

  isSelected(item: CleanHistoryItem): boolean {
    const id = this.getNumericId(item.id);
    return id !== null && this.selectedIds.has(id);
  }

  toggleSelection(item: CleanHistoryItem): void {
    const id = this.getNumericId(item.id);

    if (id === null) {
      return;
    }

    if (this.selectedIds.has(id)) {
      this.selectedIds.delete(id);
    } else {
      this.selectedIds.add(id);
    }
  }

  toggleSelectAllVisible(): void {
    const visibleIds = this.filteredHistory
      .map((item) => this.getNumericId(item.id))
      .filter((id): id is number => id !== null);

    const allVisibleSelected =
      visibleIds.length > 0 && visibleIds.every((id) => this.selectedIds.has(id));

    if (allVisibleSelected) {
      visibleIds.forEach((id) => this.selectedIds.delete(id));
    } else {
      visibleIds.forEach((id) => this.selectedIds.add(id));
    }
  }

  get allVisibleSelected(): boolean {
    const visibleIds = this.filteredHistory
      .map((item) => this.getNumericId(item.id))
      .filter((id): id is number => id !== null);

    return visibleIds.length > 0 && visibleIds.every((id) => this.selectedIds.has(id));
  }

  get selectedCount(): number {
    return this.selectedIds.size;
  }

  deleteSelected(): void {
    if (this.selectedIds.size === 0) {
      this.errorMessage = 'Veuillez sélectionner au moins une recommandation à supprimer.';
      return;
    }

    const ids = Array.from(this.selectedIds);

    const confirmed = confirm(
      `Voulez-vous vraiment supprimer ${ids.length} recommandation(s) sélectionnée(s) ?`
    );

    if (!confirmed) {
      return;
    }

    this.deleting = true;
    this.errorMessage = '';
    this.successMessage = '';

    this.http
      .post(this.deleteBatchUrl, { ids })
      .pipe(finalize(() => (this.deleting = false)))
      .subscribe({
        next: () => {
          this.history = this.history.filter((item) => {
            const id = this.getNumericId(item.id);
            return id === null || !this.selectedIds.has(id);
          });

          this.filteredHistory = this.filteredHistory.filter((item) => {
            const id = this.getNumericId(item.id);
            return id === null || !this.selectedIds.has(id);
          });

          this.successMessage = `${ids.length} recommandation(s) supprimée(s) avec succès.`;
          this.selectedIds.clear();
        },
        error: (error) => {
          console.error('Delete selected recommendations error:', error);
          this.errorMessage =
            'Erreur lors de la suppression. Vérifiez que l’endpoint backend de suppression existe.';
        },
      });
  }

  get totalSearches(): number {
    return this.history.length;
  }

  get totalProductsRecommended(): number {
    return this.history.reduce((sum, item) => sum + item.products.length, 0);
  }

  get uniqueCategories(): number {
    const categories = new Set(
      this.history
        .map((item) => item.category)
        .filter((category) => category && category !== 'Non définie')
    );

    return categories.size;
  }

  get lastSearchDate(): string {
    return this.history.length > 0 ? this.history[0].date : '—';
  }

  formatScore(score: number | null): string {
    if (score === null || Number.isNaN(score)) {
      return 'N/A';
    }

    return `${Math.round(score * 100)}%`;
  }
}
