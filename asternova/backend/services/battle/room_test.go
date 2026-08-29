package battle

import (
	"encoding/json"
	"testing"

	pb "github.com/TimeCraker/game-backend-demo/services/proto"
	"google.golang.org/protobuf/proto"
)

func TestNewBattleRoomInitialLayout(t *testing.T) {
	r := NewBattleRoom("room-1", 11, 22)

	if r.RoomID != "room-1" {
		t.Errorf("RoomID = %q, want room-1", r.RoomID)
	}
	if r.Player1.UserID != 11 || r.Player2.UserID != 22 {
		t.Errorf("玩家编号 = (%d, %d), want (11, 22)", r.Player1.UserID, r.Player2.UserID)
	}
	if r.Player1.Position.X != -300 || r.Player2.Position.X != 300 {
		t.Errorf("出生位置 = (%v, %v), want P1 在 -300、P2 在 300", r.Player1.Position.X, r.Player2.Position.X)
	}
	if r.Player1.HP != 100 || r.Player2.HP != 100 {
		t.Errorf("初始 HP = (%d, %d), want (100, 100)", r.Player1.HP, r.Player2.HP)
	}
	if r.Player1.FacingX != 1 || r.Player2.FacingX != -1 {
		t.Errorf("初始朝向 = (%v, %v), want 相对而立 (1, -1)", r.Player1.FacingX, r.Player2.FacingX)
	}
	if r.IsGameOver {
		t.Error("新房间不应处于结算状态")
	}
}

func TestApplyInputRoutesByUserID(t *testing.T) {
	r := NewBattleRoom("room-1", 1, 2)

	r.applyInput(InputEvent{UserID: 2, Input: InputSnapshot{InputX: 0.7}})
	if r.Player2.Input.InputX != 0.7 {
		t.Errorf("P2 输入未写入: %v", r.Player2.Input)
	}
	if r.Player1.Input.InputX != 0 {
		t.Error("P1 输入不应被他人事件污染")
	}

	// 未知用户事件应被忽略
	r.applyInput(InputEvent{UserID: 99, Input: InputSnapshot{InputX: 9}})
	if r.Player1.Input.InputX == 9 || r.Player2.Input.InputX == 9 {
		t.Error("未知用户事件不应写入任何玩家状态")
	}
}

func TestApplyUltimate(t *testing.T) {
	t.Run("能量不足不触发", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.Energy = 14
		r.applyUltimate(1)
		if r.Player1.CurrentState == SkillCast {
			t.Error("能量不足不应进入技能状态")
		}
		if r.Player1.Energy != 14 {
			t.Errorf("能量 = %d, want 保持 14", r.Player1.Energy)
		}
	})

	t.Run("能量满触发并挂极速者 Buff", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.Energy = 15
		r.applyUltimate(1)
		if r.Player1.CurrentState != SkillCast {
			t.Errorf("状态 = %d, want SkillCast(%d)", r.Player1.CurrentState, SkillCast)
		}
		if r.Player1.Energy != 0 {
			t.Errorf("大招后能量 = %d, want 清零", r.Player1.Energy)
		}
		if r.Player1.SpeedsterBuffTimer != 15.0 {
			t.Errorf("SpeedsterBuffTimer = %v, want 15", r.Player1.SpeedsterBuffTimer)
		}
	})

	t.Run("未知用户忽略", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.applyUltimate(99)
		if r.Player1.CurrentState == SkillCast || r.Player2.CurrentState == SkillCast {
			t.Error("未知用户不应触发大招")
		}
	})
}

func TestCheckMeleeHit(t *testing.T) {
	newRoom := func() *BattleRoom {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.CurrentState = Attack
		r.Player1.Position = Vector2{}
		r.Player1.Input.MouseX = 100 // 面朝 +X
		r.Player2.Position = Vector2{X: 100}
		return r
	}

	t.Run("扇形范围内且面向受害者命中", func(t *testing.T) {
		r := newRoom()
		if !r.checkMeleeHit(&r.Player1, &r.Player2) {
			t.Error("正前方 100 距离应命中")
		}
	})

	t.Run("超出判定半径不命中", func(t *testing.T) {
		r := newRoom()
		r.Player2.Position = Vector2{X: MeleeRadius + 1}
		if r.checkMeleeHit(&r.Player1, &r.Player2) {
			t.Error("超出 MeleeRadius 不应命中")
		}
	})

	t.Run("扇形边界外(dot<0.5)不命中", func(t *testing.T) {
		r := newRoom()
		r.Player2.Position = Vector2{X: 60, Z: 107} // dot ≈ 0.489 < 0.5，距离 122.7 在半径内
		if r.checkMeleeHit(&r.Player1, &r.Player2) {
			t.Error("扇形边界外不应命中")
		}
	})

	t.Run("HasHit 后单次判定生效", func(t *testing.T) {
		r := newRoom()
		r.Player1.HasHit = true
		if r.checkMeleeHit(&r.Player1, &r.Player2) {
			t.Error("同一攻击窗口内 HasHit=true 不应重复命中")
		}
	})

	t.Run("非攻击状态不命中", func(t *testing.T) {
		r := newRoom()
		r.Player1.CurrentState = Idle
		if r.checkMeleeHit(&r.Player1, &r.Player2) {
			t.Error("非 Attack 状态不应命中")
		}
	})

	t.Run("零距离不命中", func(t *testing.T) {
		r := newRoom()
		r.Player2.Position = r.Player1.Position
		if r.checkMeleeHit(&r.Player1, &r.Player2) {
			t.Error("完全重叠（dist=0）应排除避免除零")
		}
	})
}

func TestCheckDashHit(t *testing.T) {
	t.Run("冲刺贴近命中", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.Position = Vector2{} // 出生点在 -300，先归零
		r.Player1.CurrentState = Dashing
		r.Player2.Position = Vector2{X: DashHitRadius}
		if !r.checkDashHit(&r.Player1, &r.Player2) {
			t.Error("DashHitRadius 内应命中")
		}
	})

	t.Run("非冲刺状态不命中", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.CurrentState = Move
		if r.checkDashHit(&r.Player1, &r.Player2) {
			t.Error("非 Dashing 状态不应触发冲刺碰撞")
		}
	})

	t.Run("已命中过不重复结算", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.CurrentState = Dashing
		r.Player1.HasHit = true
		if r.checkDashHit(&r.Player1, &r.Player2) {
			t.Error("HasHit=true 不应重复触发冲刺碰撞")
		}
	})
}

func TestApplyNormalHit(t *testing.T) {
	t.Run("普通命中：扣血+硬直+攻击方奖励", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.CurrentState = Attack
		r.Player1.Position = Vector2{}
		r.Player1.Input.MouseX = 100
		r.Player1.Velocity = Vector2{X: 500} // 命中后应清零
		r.Player2.Position = Vector2{X: 100}

		r.applyNormalHit(&r.Player1, &r.Player2)

		if got, want := r.Player2.HP, 100-BaseDamage; got != want {
			t.Errorf("受害者 HP = %d, want %d", got, want)
		}
		if r.Player2.CurrentState != HitStun {
			t.Errorf("受害者状态 = %d, want HitStun(%d)", r.Player2.CurrentState, HitStun)
		}
		if !almostEqual(r.Player2.StateTimer, HitStunNormal) {
			t.Errorf("受害者硬直 = %v, want %v", r.Player2.StateTimer, HitStunNormal)
		}
		if got, want := r.Player1.Energy, EnergyReward; got != want {
			t.Errorf("攻击方能量 = %d, want %d", got, want)
		}
		if r.Player1.CurrentState != PostCast || !r.Player1.HasHit {
			t.Errorf("攻击方应进入命中后摇: state=%d hasHit=%v", r.Player1.CurrentState, r.Player1.HasHit)
		}
		if r.Player1.Velocity.X != 0 {
			t.Errorf("攻击方速度应清零, got %v", r.Player1.Velocity.X)
		}
	})

	t.Run("霸体：SkillCast 目标不进硬直，攻击方反被弹开", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player1.CurrentState = Attack // 攻击方
		r.Player2.CurrentState = SkillCast

		r.applyNormalHit(&r.Player1, &r.Player2)

		if r.Player2.CurrentState != SkillCast {
			t.Errorf("霸体目标状态被打断 = %d, want 保持 SkillCast(%d)", r.Player2.CurrentState, SkillCast)
		}
		if got, want := r.Player2.HP, 100-BaseDamage; got != want {
			t.Errorf("霸体目标仍应扣血: HP = %d, want %d", got, want)
		}
		if r.Player1.CurrentState != HitStun {
			t.Errorf("攻击方状态 = %d, want 反噬 HitStun(%d)", r.Player1.CurrentState, HitStun)
		}
	})
}

func TestApplyClash(t *testing.T) {
	r := NewBattleRoom("room-1", 1, 2)
	r.Player1.Velocity = Vector2{X: 500}
	r.Player2.Velocity = Vector2{X: -300}

	r.applyClash(&r.Player1, &r.Player2)

	for i, p := range []*BattlePlayer{&r.Player1, &r.Player2} {
		if got, want := p.HP, 100-BaseDamage; got != want {
			t.Errorf("P%d HP = %d, want %d", i+1, got, want)
		}
		if p.CurrentState != HitStun {
			t.Errorf("P%d 状态 = %d, want HitStun", i+1, p.CurrentState)
		}
		if !p.HasHit {
			t.Errorf("P%d HasHit = false, want true（拼刀双方均视为已出手）", i+1)
		}
		if p.Velocity.Length() < KnockbackSpeed-1 {
			t.Errorf("P%d 弹开速度 = %v, want ≥ 击退初速", i+1, p.Velocity.Length())
		}
	}
}

func TestEnforceDeath(t *testing.T) {
	t.Run("存活玩家不触发", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.enforceDeath(&r.Player1)
		if r.IsGameOver {
			t.Error("无人阵亡不应进入结算")
		}
	})

	t.Run("阵亡触发广播与胜利者标记", func(t *testing.T) {
		r := NewBattleRoom("room-1", 1, 2)
		r.Player2.HP = 0
		r.enforceDeath(&r.Player2)

		if r.Player2.CurrentState != Dead {
			t.Errorf("状态 = %d, want Dead(%d)", r.Player2.CurrentState, Dead)
		}
		if !r.IsGameOver {
			t.Error("应标记 IsGameOver")
		}
		select {
		case payload := <-r.BroadcastCh:
			var msg pb.GameMessage
			if err := proto.Unmarshal(payload, &msg); err != nil {
				t.Fatalf("game_over 广播解码失败: %v", err)
			}
			if msg.Type != "game_over" {
				t.Errorf("广播类型 = %q, want game_over", msg.Type)
			}
			if msg.UserId != r.Player1.UserID {
				t.Errorf("胜利者 = %d, want P1(%d)", msg.UserId, r.Player1.UserID)
			}
		default:
			t.Fatal("阵亡后 BroadcastCh 应有 game_over 消息")
		}
		// enforceDeath 内部启动了 4 秒后 Stop 的协程；Stop 幂等，测试结束后自然结束
	})
}

func TestEmitStateSnapshot(t *testing.T) {
	r := NewBattleRoom("room-1", 1, 2)
	r.emitStateSnapshot()

	select {
	case payload := <-r.BroadcastCh:
		var msg pb.GameMessage
		if err := proto.Unmarshal(payload, &msg); err != nil {
			t.Fatalf("快照解码失败: %v", err)
		}
		if msg.Type != "state" {
			t.Errorf("快照类型 = %q, want state", msg.Type)
		}
		if len(msg.Players) != 2 {
			t.Fatalf("快照玩家数 = %d, want 2", len(msg.Players))
		}
		if msg.Players[0].UserId != 1 || msg.Players[1].UserId != 2 {
			t.Errorf("快照玩家编号 = (%d, %d), want (1, 2)", msg.Players[0].UserId, msg.Players[1].UserId)
		}
		if msg.Players[0].Hp != 100 {
			t.Errorf("快照 P1 HP = %d, want 100", msg.Players[0].Hp)
		}
	default:
		t.Fatal("BroadcastCh 应收到快照")
	}
}

func TestGenerateRoomInfo(t *testing.T) {
	r := NewBattleRoom("room-9", 5, 6)
	data := r.GenerateRoomInfo()

	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("room_info JSON 解码失败: %v", err)
	}
	if decoded["type"] != "room_info" {
		t.Errorf("type = %v, want room_info", decoded["type"])
	}
	// JSON 数字解码后是 float64
	if decoded["p1_id"] != float64(5) || decoded["p2_id"] != float64(6) {
		t.Errorf("玩家编号 = (%v, %v), want (5, 6)", decoded["p1_id"], decoded["p2_id"])
	}
	if decoded["p1_class"] != "Role1_Speedster" {
		t.Errorf("p1_class = %v, want Role1_Speedster", decoded["p1_class"])
	}
}

func TestRunCombatArbiterDashClash(t *testing.T) {
	// 双方同时冲刺且互相在碰撞半径内 -> 绝对拼刀
	r := NewBattleRoom("room-1", 1, 2)
	r.Player1.Position = Vector2{} // 出生点在 -300，先归零
	r.Player1.CurrentState = Dashing
	r.Player1.Velocity = Vector2{X: 100}
	r.Player2.CurrentState = Dashing
	r.Player2.Position = Vector2{X: 50} // 距离 50 ≤ DashHitRadius
	r.Player2.Velocity = Vector2{X: -100}

	r.runCombatArbiter()

	if r.Player1.CurrentState != HitStun || r.Player2.CurrentState != HitStun {
		t.Errorf("拼刀后双方状态 = (%d, %d), want 均 HitStun", r.Player1.CurrentState, r.Player2.CurrentState)
	}
	if got, want := r.Player1.HP, 100-BaseDamage; got != want {
		t.Errorf("P1 HP = %d, want %d", got, want)
	}
}

func TestRunCombatArbiterOneSidedHit(t *testing.T) {
	// P1 攻击窗口内、P2 站在扇形内 -> 单方命中，不触发拼刀
	r := NewBattleRoom("room-1", 1, 2)
	r.Player1.CurrentState = Attack
	r.Player1.Position = Vector2{}
	r.Player1.Input.MouseX = 100
	r.Player2.Position = Vector2{X: 100}
	r.Player2.CurrentState = Idle

	r.runCombatArbiter()

	if r.Player2.CurrentState != HitStun {
		t.Errorf("P2 状态 = %d, want HitStun", r.Player2.CurrentState)
	}
	if got, want := r.Player2.HP, 100-BaseDamage; got != want {
		t.Errorf("P2 HP = %d, want %d", got, want)
	}
	if r.Player1.HP != 100 {
		t.Errorf("P1 HP = %d, want 不掉血 100", r.Player1.HP)
	}
}
