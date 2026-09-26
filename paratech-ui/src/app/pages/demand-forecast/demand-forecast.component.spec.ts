import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DemandForecastComponent } from './demand-forecast.component';

describe('DemandForecastComponent', () => {
  let component: DemandForecastComponent;
  let fixture: ComponentFixture<DemandForecastComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DemandForecastComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(DemandForecastComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
