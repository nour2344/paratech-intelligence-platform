import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  email = '';
  password = '';

  emailTouched = false;
  passwordTouched = false;

  errorMessage = '';
  loading = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  get cleanEmail(): string {
    return this.email.trim().toLowerCase();
  }

  get cleanPassword(): string {
    return this.password.trim();
  }

  get isEmailValid(): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    return emailRegex.test(this.cleanEmail);
  }

  get isPasswordValid(): boolean {
    return this.cleanPassword.length >= 6;
  }

  get isFormValid(): boolean {
    return this.isEmailValid && this.isPasswordValid;
  }

  markEmailTouched(): void {
    this.emailTouched = true;
  }

  markPasswordTouched(): void {
    this.passwordTouched = true;
  }

  login(): void {
    this.emailTouched = true;
    this.passwordTouched = true;
    this.errorMessage = '';

    if (!this.cleanEmail || !this.cleanPassword) {
      this.errorMessage = 'Veuillez remplir tous les champs.';
      return;
    }

    if (!this.isEmailValid) {
      this.errorMessage = 'Veuillez saisir une adresse email valide.';
      return;
    }

    if (!this.isPasswordValid) {
      this.errorMessage = 'Le mot de passe doit contenir au moins 6 caractères.';
      return;
    }

    this.loading = true;

    this.authService
      .login({
        email: this.cleanEmail,
        password: this.cleanPassword,
      })
      .subscribe({
        next: (response) => {
          this.loading = false;

          localStorage.setItem('access_token', response.access_token);
          localStorage.setItem('token', response.access_token);
          localStorage.setItem('role', response.user.role);
          localStorage.setItem('user', JSON.stringify(response.user));

          const role = String(response.user.role).toUpperCase();

          if (role === 'OWNER') {
            this.router.navigate(['/owner/dashboard']);
          } else if (role === 'PHARMACIST') {
            this.router.navigate(['/pharmacist/dashboard']);
          } else if (role === 'CASHIER') {
            this.router.navigate(['/cashier/dashboard']);
          } else if (role === 'CLIENT') {
            this.router.navigate(['/client/recommendations']);
          } else {
            this.router.navigate(['/']);
          }
        },
        error: (error) => {
          this.loading = false;
          console.error('Login error:', error);
          this.errorMessage = 'Email ou mot de passe incorrect.';
        },
      });
  }
}
