import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss'],
})
export class LandingComponent {
  features = [
    {
      title: 'Business Intelligence',
      description:
        'Analysez les ventes, paiements, stocks et indicateurs clés avec des dashboards interactifs.',
      icon: 'BI',
    },
    {
      title: 'Prévision de la demande',
      description:
        'Anticipez les quantités futures vendues afin de mieux planifier le réapprovisionnement.',
      icon: 'AI',
    },
    {
      title: 'Risque de stock intelligent',
      description:
        'Identifiez les produits à risque de rupture grâce à une analyse basée sur les données.',
      icon: 'RX',
    },
    {
      title: 'Système de recommandation',
      description:
        'Aidez les clients à trouver des produits pertinents selon leurs besoins et préférences.',
      icon: '★',
    },
    {
      title: 'Barcode Recognition',
      description:
        'Scannez rapidement les produits pour faciliter l’identification et l’accès à l’information.',
      icon: '▦',
    },
    {
      title: 'Alertes intelligentes',
      description:
        'Recevez des alertes claires pour agir rapidement sur les situations critiques.',
      icon: '!',
    },
  ];

  roles = [
    {
      title: 'Owner',
      description:
        'Piloter la performance globale, suivre les ventes, le stock et les modules intelligents.',
    },
    {
      title: 'Pharmacist',
      description:
        'Gérer les produits, consulter les recommandations et surveiller les risques de rupture.',
    },
    {
      title: 'Cashier',
      description:
        'Scanner les produits, consulter les informations utiles et accompagner l’activité de caisse.',
    },
    {
      title: 'Client',
      description:
        'Découvrir des recommandations personnalisées et trouver rapidement le bon produit.',
    },
  ];
}
