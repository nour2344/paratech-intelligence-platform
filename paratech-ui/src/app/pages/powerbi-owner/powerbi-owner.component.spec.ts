import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PowerbiOwnerComponent } from './powerbi-owner.component';

describe('PowerbiOwnerComponent', () => {
  let component: PowerbiOwnerComponent;
  let fixture: ComponentFixture<PowerbiOwnerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PowerbiOwnerComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PowerbiOwnerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
