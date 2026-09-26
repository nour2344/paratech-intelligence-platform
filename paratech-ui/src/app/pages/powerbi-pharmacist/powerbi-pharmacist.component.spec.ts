import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PowerbiPharmacistComponent } from './powerbi-pharmacist.component';

describe('PowerbiPharmacistComponent', () => {
  let component: PowerbiPharmacistComponent;
  let fixture: ComponentFixture<PowerbiPharmacistComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PowerbiPharmacistComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PowerbiPharmacistComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
