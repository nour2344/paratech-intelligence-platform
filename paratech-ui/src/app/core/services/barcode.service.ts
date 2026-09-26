import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface BarcodeProduct {
  product_id: string;
  product_name: string;
  product_category: string;
  product_description: string;
  stock_quantity: string;
  stock_value: string;
  tva: string;
  alert_quantity: string;
}

export interface BarcodeRecommendation {
  product_id: number;
  product_name: string;
  product_category: string;
  similarity_score: number;
}

export interface BarcodeScanResponse {
  success: boolean;
  barcode: string | null;
  product: BarcodeProduct | null;
  recommendations: BarcodeRecommendation[];
  error: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class BarcodeService {
  private apiUrl = 'http://127.0.0.1:8000/barcode';

  constructor(private http: HttpClient) {}

  scanImage(file: File): Observable<BarcodeScanResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<BarcodeScanResponse>(
      `${this.apiUrl}/scan`,
      formData
    );
  }

  health(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }
}