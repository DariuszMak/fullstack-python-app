export class PID {
  private readonly kp: number;
  private readonly ki: number;
  private readonly kd: number;
  /** @internal */ _prevError = 0;
  /** @internal */ _integral = 0;

  constructor(kp: number, ki: number, kd: number) {
    this.kp = kp;
    this.ki = ki;
    this.kd = kd;
  }

  update(error: number): number {
    this._integral += error;
    const derivative = error - this._prevError;
    this._prevError = error;
    return this.kp * error + this.ki * this._integral + this.kd * derivative;
  }

  reset(): void {
    this._prevError = 0;
    this._integral = 0;
  }
}
