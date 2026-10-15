import { PID } from "./pid";

export interface MovementStrategy {
  update(current: number, target: number): number;
  reset(): void;
}

export class PIDMovementStrategy implements MovementStrategy {
  private readonly _pid: PID;

  constructor(kp: number, ki: number, kd: number) {
    this._pid = new PID(kp, ki, kd);
  }

  update(current: number, target: number): number {
    const error = target - current;

    const adjustment = this._pid.update(error);

    return current + adjustment;
  }

  reset(): void {
    this._pid.reset();
  }
}
export class EasingMovementStrategy implements MovementStrategy {
  private readonly factor: number;

  constructor(factor = 0.1) {
    this.factor = factor;
  }

  update(current: number, target: number): number {
    return current + (target - current) * this.factor;
  }

  reset(): void {
    return;
  }
}

export class TickMovementStrategy implements MovementStrategy {
  update(_current: number, target: number): number {
    return target;
  }

  reset(): void {
    return;
  }
}
