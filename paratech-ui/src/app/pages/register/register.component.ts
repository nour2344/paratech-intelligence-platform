import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.scss'],
})
export class RegisterComponent {
  fullName = '';
  email = '';
  password = '';
  confirmPassword = '';

  fullNameTouched = false;
  emailTouched = false;
  passwordTouched = false;
  confirmPasswordTouched = false;

  errorMessage = '';
  successMessage = '';
  loading = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  get cleanFullName(): string {
    return this.fullName.trim();
  }

  get cleanEmail(): string {
    return this.email.trim().toLowerCase();
  }

  get cleanPassword(): string {
    return this.password.trim();
  }

  get cleanConfirmPassword(): string {
    return this.confirmPassword.trim();
  }

  get isFullNameValid(): boolean {
    return this.cleanFullName.length >= 2;
  }

  get isEmailValid(): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    return emailRegex.test(this.cleanEmail);
  }

  get isPasswordValid(): boolean {
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d).{6,}$/;
    return passwordRegex.test(this.cleanPassword);
  }

  get doPasswordsMatch(): boolean {
    return (
      this.cleanPassword.length > 0 &&
      this.cleanConfirmPassword.length > 0 &&
      this.cleanPassword === this.cleanConfirmPassword
    );
  }

  get isFormValid(): boolean {
    return (
      this.isFullNameValid &&
      this.isEmailValid &&
      this.isPasswordValid &&
      this.doPasswordsMatch
    );
  }

  markFullNameTouched(): void {
    this.fullNameTouched = true;
  }

  markEmailTouched(): void {
    this.emailTouched = true;
  }

  markPasswordTouched(): void {
    this.passwordTouched = true;
  }

  markConfirmPasswordTouched(): void {
    this.confirmPasswordTouched = true;
  }

  private extractErrorMessage(error: any): string {
    const detail = error?.error?.detail || error?.error?.message || error?.message;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item) => item?.msg || item?.message || JSON.stringify(item))
        .join(' ');
    }

    return 'Une erreur est survenue lors de la création du compte.';
  }

  register(): void {
    this.fullNameTouched = true;
    this.emailTouched = true;
    this.passwordTouched = true;
    this.confirmPasswordTouched = true;

    this.errorMessage = '';
    this.successMessage = '';

    if (!this.cleanFullName || !this.cleanEmail || !this.cleanPassword || !this.cleanConfirmPassword) {
      this.errorMessage = 'Veuillez remplir tous les champs.';
      return;
    }

    if (!this.isFullNameValid) {
      this.errorMessage = 'Le nom complet doit contenir au moins 2 caractères.';
      return;
    }

    if (!this.isEmailValid) {
      this.errorMessage = 'Veuillez saisir une adresse email valide.';
      return;
    }

    if (!this.isPasswordValid) {
      this.errorMessage =
        'Le mot de passe doit contenir au moins 6 caractères, avec au moins une lettre et un chiffre.';
      return;
    }

    if (!this.doPasswordsMatch) {
      this.errorMessage = 'Les deux mots de passe ne correspondent pas.';
      return;
    }

    this.loading = true;

    this.authService
      .register({
        full_name: this.cleanFullName,
        email: this.cleanEmail,
        password: this.cleanPassword,
      })
      .subscribe({
        next: () => {
          this.loading = false;
          this.successMessage = 'Compte créé avec succès. Vous pouvez maintenant vous connecter.';

          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 900);
        },
        error: (error) => {
          this.loading = false;
          console.error('Register error:', error);
          this.errorMessage = this.extractErrorMessage(error);
        },
      });
  }
}
