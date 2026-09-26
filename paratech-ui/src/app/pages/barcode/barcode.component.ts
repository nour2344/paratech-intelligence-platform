import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { BarcodeScanResponse, BarcodeService } from '../../core/services/barcode.service';

@Component({
  selector: 'app-barcode',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './barcode.component.html',
  styleUrl: './barcode.component.scss',
})
export class BarcodeComponent {
  selectedFile: File | null = null;
  previewUrl: string | null = null;

  result: BarcodeScanResponse | null = null;
  loading = false;
  errorMessage = '';

  constructor(private barcodeService: BarcodeService) {}

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;

    if (!input.files || input.files.length === 0) {
      return;
    }

    this.selectedFile = input.files[0];
    this.result = null;
    this.errorMessage = '';

    const reader = new FileReader();
    reader.onload = () => {
      this.previewUrl = reader.result as string;
    };
    reader.readAsDataURL(this.selectedFile);
  }

  scanBarcode(): void {
    if (!this.selectedFile) {
      this.errorMessage = 'Veuillez sélectionner une image.';
      return;
    }

    this.loading = true;
    this.errorMessage = '';
    this.result = null;

    this.barcodeService.scanImage(this.selectedFile).subscribe({
      next: (response) => {
        this.result = response;
        this.loading = false;

        if (!response.success) {
          this.errorMessage = response.error || 'Aucun produit trouvé.';
        }
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage =
          error.error?.detail || 'Erreur lors du scan du code-barres.';
      },
    });
  }
}