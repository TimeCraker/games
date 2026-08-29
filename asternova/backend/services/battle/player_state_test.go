package battle

import (
	"math"
	"testing"
)

// step 按 fixed delta 推进一帧，返回推进后的玩家指针。
func step(p *BattlePlayer, delta float64) *BattlePlayer {
	p.Update(delta)
	return p
}

func TestPlayerAttackChain(t *testing.T) {
	p := &BattlePlayer{UserID: 1, CurrentState: Idle}
	p.Input.IsAttacking = true

	// 第一帧：Idle + 攻击输入 -> 进入前摇
	step(p, 0.016)
	if p.CurrentState != PreCast {
		t.Fatalf("第一帧后状态 = %d, want PreCast(%d)", p.CurrentState, PreCast)
	}
	if !almostEqual(p.StateTimer, AttackPreCast) {
		t.Errorf("前摇计时 = %v, want %v", p.StateTimer, AttackPreCast)
	}

	// 前摇耗尽 -> 进入攻击判定窗口，HasHit 复位
	step(p, AttackPreCast+0.001)
	if p.CurrentState != Attack {
		t.Fatalf("前摇耗尽后状态 = %d, want Attack(%d)", p.CurrentState, Attack)
	}
	if p.HasHit {
		t.Error("进入攻击窗口时 HasHit 应复位为 false")
	}

	// 攻击窗口耗尽 -> 挥空进入 PostCast（惩罚更长）
	step(p, AttackDuration+0.001)
	if p.CurrentState != PostCast {
		t.Fatalf("攻击窗口耗尽后状态 = %d, want PostCast(%d)", p.CurrentState, PostCast)
	}
	if !almostEqual(p.StateTimer, AttackPostCastMiss) {
		t.Errorf("挥空后摇 = %v, want %v", p.StateTimer, AttackPostCastMiss)
	}

	// 命中场景 -> 命中后摇更短（奖励）
	p.Input.IsAttacking = false
	p.CurrentState = Attack
	p.HasHit = true
	p.StateTimer = AttackDuration
	step(p, AttackDuration+0.001)
	if p.CurrentState != PostCast || !almostEqual(p.StateTimer, AttackPostCastHit) {
		t.Errorf("命中后摇 = (%d, %v), want (PostCast, %v)", p.CurrentState, p.StateTimer, AttackPostCastHit)
	}

	// 后摇耗尽 -> 回到 Idle
	step(p, AttackPostCastHit+0.001)
	if p.CurrentState != Idle {
		t.Errorf("后摇耗尽后状态 = %d, want Idle(%d)", p.CurrentState, Idle)
	}
}

func TestPlayerHeldAttackLoopsAfterRecovery(t *testing.T) {
	// 持续按住攻击键：一套连招结束后应能再次进入前摇（自动连发语义）
	p := &BattlePlayer{CurrentState: Idle}
	p.Input.IsAttacking = true
	step(p, 0.016)                                   // PreCast
	step(p, AttackPreCast+0.001)                     // Attack
	step(p, AttackDuration+0.001)                    // PostCast
	step(p, AttackPostCastMiss+0.001)                // Idle + 同帧再次触发 PreCast
	if p.CurrentState != PreCast {
		t.Errorf("按住攻击键连招结束后状态 = %d, want 再次进入 PreCast(%d)", p.CurrentState, PreCast)
	}
}

func TestPlayerChargingAndDash(t *testing.T) {
	p := &BattlePlayer{UserID: 1, CurrentState: Idle, Position: Vector2{}, Energy: 0, FacingX: 1}
	p.Input.IsCharging = true
	p.Input.MouseX = 1000 // 鼠标在右侧 -> 冲刺应朝 +X

	// 蓄力累计
	step(p, 0.5)
	if p.CurrentState != Charging {
		t.Fatalf("按住蓄力后状态 = %d, want Charging(%d)", p.CurrentState, Charging)
	}
	if !almostEqual(p.ChargeTimer, 0.5) {
		t.Errorf("ChargeTimer = %v, want 0.5", p.ChargeTimer)
	}

	// 松开 -> 冲刺：初速沿鼠标方向，能量按蓄力时间入账
	p.Input.IsCharging = false
	step(p, 1.0/60.0)
	if p.CurrentState != Dashing {
		t.Fatalf("松开蓄力后状态 = %d, want Dashing(%d)", p.CurrentState, Dashing)
	}
	// 0.5s 蓄力 -> distance = 0.5 * (200 * 1.5) = 150 -> burst = 150 * 18 = 2700
	if p.Velocity.X <= 0 || math.Abs(p.Velocity.Z) > 1e-6 {
		t.Errorf("冲刺初速 = %v, want 沿 +X 的正向速度", p.Velocity)
	}
	if p.ChargeTimer != 0 {
		t.Errorf("起跑后 ChargeTimer = %v, want 0", p.ChargeTimer)
	}
	if got, want := p.Energy, int32(1); got != want { // 0.5 * 2.0 = 1
		t.Errorf("蓄力 0.5s 后能量 = %d, want %d", got, want)
	}
}

func TestPlayerChargeTooShortStaysIdle(t *testing.T) {
	// 蓄力距离不足 10 时不应进入冲刺
	p := &BattlePlayer{CurrentState: Idle}
	p.Input.IsCharging = true
	step(p, 0.001) // distance = 0.001 * 300 = 0.3 < 10
	p.Input.IsCharging = false
	step(p, 1.0/60.0)
	if p.CurrentState != Idle {
		t.Errorf("过短蓄力松开后状态 = %d, want Idle(%d)", p.CurrentState, Idle)
	}
}

func TestPlayerEnergyCappedAt15(t *testing.T) {
	p := &BattlePlayer{CurrentState: Idle, Energy: 14}
	p.Input.IsCharging = true
	step(p, 3.0) // 远超 MaxEffectiveChargeTime -> effectiveTime 2.5 -> gain 5
	p.Input.IsCharging = false
	step(p, 1.0/60.0)
	if p.Energy != 15 {
		t.Errorf("蓄力溢出后能量 = %d, want 上限 15", p.Energy)
	}
}

func TestPlayerSpeedsterBuffEffects(t *testing.T) {
	t.Run("攻击窗口结束直接回 Idle 不进后摇", func(t *testing.T) {
		p := &BattlePlayer{CurrentState: Attack, SpeedsterBuffTimer: 10, HasHit: false}
		step(p, AttackDuration+0.001)
		if p.CurrentState != Idle {
			t.Errorf("大招期间攻击结束状态 = %d, want Idle(%d)", p.CurrentState, Idle)
		}
	})

	t.Run("蓄力速率提升 1.5 倍", func(t *testing.T) {
		p := &BattlePlayer{CurrentState: Idle, SpeedsterBuffTimer: 10}
		p.Input.IsCharging = true
		step(p, 0.4)
		if !almostEqual(p.ChargeTimer, 0.6) {
			t.Errorf("大招蓄力 ChargeTimer = %v, want 0.6", p.ChargeTimer)
		}
	})

	t.Run("大招期间冲刺不积攒能量", func(t *testing.T) {
		p := &BattlePlayer{CurrentState: Idle, Energy: 0, SpeedsterBuffTimer: 10}
		p.Input.IsCharging = true
		step(p, 1.0)
		p.Input.IsCharging = false
		step(p, 1.0/60.0)
		if p.Energy != 0 {
			t.Errorf("大招期间冲刺后能量 = %d, want 0", p.Energy)
		}
	})
}

func TestPlayerHitStunDecelerates(t *testing.T) {
	// 受击轨道：速度按 HitStunFriction 快速衰减但不瞬间清零
	// StateTimer 必须为正（真实受击时由 applyNormalHit/applyClash 写入），
	// 否则 Update 首帧就会把 HitStun 转回 Idle 走常规移动轨道
	p := &BattlePlayer{CurrentState: HitStun, StateTimer: HitStunNormal, Velocity: Vector2{X: KnockbackSpeed}}
	step(p, 1.0/60.0)
	want := KnockbackSpeed * (1 - HitStunFriction/60.0)
	if !almostEqual(p.Velocity.X, want) {
		t.Errorf("受击一帧后速度 = %v, want %v", p.Velocity.X, want)
	}
	if p.Velocity.X >= KnockbackSpeed {
		t.Error("受击状态下速度应单调衰减")
	}
}

func TestPlayerMoveFacing(t *testing.T) {
	t.Run("Move 状态按输入方向更新 FacingX", func(t *testing.T) {
		cases := []struct {
			name    string
			inputX  float64
			want    float64
		}{
			{"向右", 0.5, 1.0},
			{"向左", -0.5, -1.0},
		}
		for _, tc := range cases {
			t.Run(tc.name, func(t *testing.T) {
				p := &BattlePlayer{CurrentState: Idle, FacingX: -tc.want}
				p.Input.InputX = tc.inputX
				step(p, 1.0/60.0)
				if p.FacingX != tc.want {
					t.Errorf("输入 %v 后 FacingX = %v, want %v", tc.inputX, p.FacingX, tc.want)
				}
			})
		}
	})

	t.Run("蓄力状态按鼠标相对位置更新 FacingX", func(t *testing.T) {
		p := &BattlePlayer{CurrentState: Idle, Position: Vector2{X: 0}, FacingX: 1}
		p.Input.IsCharging = true
		p.Input.MouseX = -50 // 鼠标在左侧
		step(p, 1.0/60.0)
		if p.FacingX != -1.0 {
			t.Errorf("蓄力朝左后 FacingX = %v, want -1", p.FacingX)
		}
	})
}

func TestPlayerRotYFollowsMouse(t *testing.T) {
	p := &BattlePlayer{CurrentState: Idle, Position: Vector2{}}
	p.Input.MouseX = 3
	p.Input.MouseY = 4
	step(p, 1.0/60.0)
	want := math.Atan2(4, 3) * 180.0 / math.Pi
	if !almostEqual(p.RotY, want) {
		t.Errorf("RotY = %v, want %v", p.RotY, want)
	}
}

func TestPlayerPositionIntegratesVelocity(t *testing.T) {
	// Idle 状态给输入 -> 进入 Move -> 位置沿输入方向随时间推进
	p := &BattlePlayer{CurrentState: Idle}
	p.Input.InputX = 1
	for i := 0; i < 10; i++ {
		step(p, 1.0/60.0)
	}
	if p.Position.X <= 0 {
		t.Errorf("持续向右输入 10 帧后 X = %v, want > 0", p.Position.X)
	}
	if p.Position.X > BaseSpeed*10/60.0 {
		t.Errorf("10 帧位移 X = %v, 超出理论最大位移", p.Position.X)
	}
}
