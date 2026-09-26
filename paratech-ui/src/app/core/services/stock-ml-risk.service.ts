import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface StockMlProduct {
  product_name: string;
  category: string;
  current_stock: number;
  alert_threshold: number;
}

export interface StockMlSearchResponse {
  count: number;
  results: StockMlProduct[];
}

export interface StockMlAnalyzeRequest {
  product_name: string;
}

export interface StockMlAlert {
  active: boolean;
  severity: string;
  title: string;
  message: string;
}

export interface StockMlAnalysisResponse {
  product_name: string;
  category: string;
  current_stock: number;
  alert_threshold: number;
  average_daily_sales: number;
  estimated_days_before_stockout: number;
  risk_level: string;
  risk_label: string;
  confidence: number;
  alert: StockMlAlert;
  recommendation: string;
}

@Injectable({
  providedIn: 'root',
})
export class StockMlRiskService {
  private readonly apiUrl = 'http://127.0.0.1:8000/stock-ml';

  constructor(private http: HttpClient) {}

  searchProducts(name: string): Observable<StockMlSearchResponse> {
    const params = new HttpParams().set('name', name);

    return this.http.get<StockMlSearchResponse>(`${this.apiUrl}/search`, {
      params,
    });
  }

  analyzeProduct(productName: string): Observable<StockMlAnalysisResponse> {
    const body: StockMlAnalyzeRequest = {
      product_name: productName,
    };

    return this.http.post<StockMlAnalysisResponse>(
      `${this.apiUrl}/analyze`,
      body
    );
  }

  getAlerts(): Observable<StockMlAnalysisResponse[]> {
    return this.http.get<StockMlAnalysisResponse[]>(`${this.apiUrl}/alerts`);
  }
}