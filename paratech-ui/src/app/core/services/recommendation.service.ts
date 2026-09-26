import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface RecommendedProduct {
  product_id?: number | null;
  product_name?: string;
  name?: string;
  category?: string | null;
  brand?: string | null;
  price?: number | null;
  score?: number | null;
}

export interface RecommendationInputData {
  mode?: string;
  product_name?: string;
  category?: string | null;
  max_price?: number | null;
}

export interface RecommendationRequest {
  user_id: number;
  query: string;
  input_data: RecommendationInputData;
}

export interface RecommendationResponse {
  message: string;
  recommended_products: RecommendedProduct[];
}

export interface RecommendationHistory {
  id: number;
  user_id: number;
  query: string;
  input_data: string;
  recommended_products: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root',
})
export class RecommendationService {
  private apiUrl = 'http://127.0.0.1:8000/recommendations';

  constructor(private http: HttpClient) {}

  predict(data: RecommendationRequest): Observable<RecommendationResponse> {
    return this.http.post<RecommendationResponse>(
      `${this.apiUrl}/predict`,
      data
    );
  }

  getUserHistory(userId: number): Observable<RecommendationHistory[]> {
    return this.http.get<RecommendationHistory[]>(
      `${this.apiUrl}/history/user/${userId}`
    );
  }

  getAllHistory(): Observable<RecommendationHistory[]> {
    return this.http.get<RecommendationHistory[]>(`${this.apiUrl}/history`);
  }
}