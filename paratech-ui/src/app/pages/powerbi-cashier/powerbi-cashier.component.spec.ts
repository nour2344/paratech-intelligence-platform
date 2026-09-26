import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PowerbiCashierComponent } from './powerbi-cashier.component';

describe('PowerbiCashierComponent', () => {
  let component: PowerbiCashierComponent;
  let fixture: ComponentFixture<PowerbiCashierComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PowerbiCashierComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PowerbiCashierComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
