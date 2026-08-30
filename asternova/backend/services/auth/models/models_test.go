package models

import (
	"encoding/json"
	"testing"
	"time"
)

// 以下断言的是下行 JSON 契约（前端依赖字段名），非实现细节。

func TestMessageJSONContract(t *testing.T) {
	m := Message{
		ID:        1,
		Sender:    "alice",
		Content:   "hello",
		CreatedAt: time.Date(2026, 8, 29, 12, 0, 0, 0, time.UTC),
	}
	data, err := json.Marshal(m)
	if err != nil {
		t.Fatalf("Marshal 失败: %v", err)
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("Unmarshal 失败: %v", err)
	}
	want := map[string]interface{}{
		"id":         float64(1),
		"sender":     "alice",
		"content":    "hello",
		"created_at": "2026-08-29T12:00:00Z",
	}
	for key, wantVal := range want {
		gotVal, ok := decoded[key]
		if !ok {
			t.Errorf("缺少字段 %q", key)
			continue
		}
		if gotVal != wantVal {
			t.Errorf("字段 %q = %v, want %v", key, gotVal, wantVal)
		}
	}
}

// 原 TestPlayerPositionJSONContract 已随 PlayerPosition struct 移除:
// 该表按 architecture.md §5 迁移为 player_positions(JSONB payload + schema_version),
// 载荷契约见 services/gateway/handlers/websocket.go 的 posPayload。
