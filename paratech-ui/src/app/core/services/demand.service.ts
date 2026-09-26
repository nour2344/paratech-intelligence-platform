import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface DemandProduct {
  product_id: number;
  product_name: string;
  category?: string;
}

export interface DemandProductsResponse {
  count: number;
  products: DemandProduct[];
}

export interface DemandForecastByNameRequest {
  product_name: string;
  horizon: number;
}

export interface DemandForecastPoint {
  date: string;
  predicted_quantity: number;
}

export interface DemandForecastMetrics {
  mae: number;
  rmse: number;
  r2: number;
}

export interface DemandForecastResponse {
  product_id: number;
  product_name: string;
  model: string;
  horizon: number;
  metrics: DemandForecastMetrics;
  forecast: DemandForecastPoint[];
}

export interface DemandBusinessSummary {
  totalForecast: number;
  averagePerDay: number;
  peakDay: DemandForecastPoint | null;
  lowestDay: DemandForecastPoint | null;
  recommendation: string;
  status: 'low' | 'medium' | 'high';
  statusLabel: string;
}

@Injectable({
  providedIn: 'root',
})
export class DemandService {
  private readonly apiUrl = 'http://127.0.0.1:8000/demand';

  constructor(private http: HttpClient) {}

  getProducts(): Observable<DemandProductsResponse> {
    return this.http.get<DemandProductsResponse>(`${this.apiUrl}/products`);
  }

  forecastByName(
    productName: string,
    horizon: number
  ): Observable<DemandForecastResponse> {
    const body: DemandForecastByNameRequest = {
      product_name: productName,
      horizon,
    };

    return this.http.post<DemandForecastResponse>(
      `${this.apiUrl}/forecast/by-name`,
      body
    );
  }

  buildBusinessSummary(forecast: DemandForecastResponse): DemandBusinessSummary {
    const points = forecast.forecast ?? [];

    const totalForecast = points.reduce(
      (sum, item) => sum + Number(item.predicted_quantity || 0),
      0
    );

    const averagePerDay =
      forecast.horizon > 0 ? totalForecast / forecast.horizon : 0;

    const peakDay =
      points.length > 0
        ? points.reduce((max, item) =>
            Number(item.predicted_quantity) > Number(max.predicted_quantity)
              ? item
              : max
          )
        : null;

    const lowestDay =
      points.length > 0
        ? points.reduce((min, item) =>
            Number(item.predicted_quantity) < Number(min.predicted_quantity)
              ? item
              : min
          )
        : null;

    let status: 'low' | 'medium' | 'high' = 'low';
    let statusLabel = 'Demande faible';
    let recommendation =
      'La demande prévue est faible. Le stock peut être surveillé normalement, sans commande urgente.';

    if (averagePerDay >= 5) {
      status = 'high';
      statusLabel = 'Demande élevée';
      recommendation =
        'La demande prévue est élevée. Il est recommandé de préparer un réapprovisionnement suffisant afin d’éviter une rupture de stock.';
    } else if (averagePerDay >= 2) {
      status = 'medium';
      statusLabel = 'Demande moyenne';
      recommendation =
        'La demande prévue est modérée. Il est recommandé de surveiller le stock et de prévoir une commande si le niveau diminue.';
    }

    return {
      totalForecast,
      averagePerDay,
      peakDay,
      lowestDay,
      recommendation,
      status,
      statusLabel,
    };
  }
}