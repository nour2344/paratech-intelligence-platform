import { ComponentFixture, TestBed } from '@angular/core/testing';

import { StockShortageComponent } from './stock-ml-risk.component';

describe('StockShortageComponent', () => {
  let component: StockShortageComponent;
  let fixture: ComponentFixture<StockShortageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StockShortageComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(StockShortageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
