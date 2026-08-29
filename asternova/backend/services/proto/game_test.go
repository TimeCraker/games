package proto

import (
	"testing"

	"google.golang.org/protobuf/proto"
)

// TestGameMessageMarshalRoundTrip 验证网关与客户端依赖的协议编解码往返一致性
func TestGameMessageMarshalRoundTrip(t *testing.T) {
	cases := []struct {
		name string
		msg  *GameMessage
	}{
		{
			name: "聊天消息",
			msg:  &GameMessage{Type: "chat", UserId: 7, Content: "hello"},
		},
		{
			name: "移动消息含坐标与朝向",
			msg:  &GameMessage{Type: "move", UserId: 8, X: 1.5, Y: 0, Z: -2.25, RotY: 90.5},
		},
		{
			name: "战斗输入消息",
			msg: &GameMessage{
				Type: "input", UserId: 9,
				InputX: 0.5, InputY: -0.5,
				IsCharging: true, IsAttacking: false,
				MouseX: 100, MouseY: 200,
			},
		},
		{
			name: "状态快照含玩家列表",
			msg: &GameMessage{
				Type: "state", RoomId: "room-1",
				Players: []*PlayerPos{
					{UserId: 1, X: 10, Y: 0, Z: 20, RotY: 45, CurrentState: 1, Hp: 100, Energy: 5},
					{UserId: 2, X: -10, Y: 0, Z: -20, RotY: 225, CurrentState: 7, Hp: 70, Energy: 15},
				},
			},
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			payload, err := proto.Marshal(tc.msg)
			if err != nil {
				t.Fatalf("Marshal 失败: %v", err)
			}
			if len(payload) == 0 {
				t.Fatal("序列化结果为空")
			}

			var got GameMessage
			if err := proto.Unmarshal(payload, &got); err != nil {
				t.Fatalf("Unmarshal 失败: %v", err)
			}
			if !proto.Equal(tc.msg, &got) {
				t.Errorf("往返不一致:\n want %+v\n got  %+v", tc.msg, &got)
			}
		})
	}
}

func TestGameMessageUnmarshalRejectsGarbage(t *testing.T) {
	var msg GameMessage
	if err := proto.Unmarshal([]byte{0xff, 0xff, 0xff}, &msg); err == nil {
		t.Error("非法字节流应返回解析错误")
	}
}
