package match

import (
	"testing"
	"time"
)

// newTestMatcher 构造独立匹配器，避免污染 GlobalMatcher 单例状态。
func newTestMatcher() *Matcher {
	return &Matcher{
		queue:    make([]uint32, 0),
		ResultCh: make(chan MatchResult, 10),
	}
}

func TestAddPlayerEnqueues(t *testing.T) {
	m := newTestMatcher()
	m.AddPlayer(1)
	m.AddPlayer(2)

	if len(m.queue) != 2 {
		t.Fatalf("队列长度 = %d, want 2", len(m.queue))
	}
	if m.queue[0] != 1 || m.queue[1] != 2 {
		t.Errorf("队列内容 = %v, want [1 2]（保持排队顺序）", m.queue)
	}
}

func TestAddPlayerDebounces(t *testing.T) {
	m := newTestMatcher()
	m.AddPlayer(1)
	m.AddPlayer(1) // 重复点击匹配
	m.AddPlayer(1)

	if len(m.queue) != 1 {
		t.Fatalf("队列长度 = %d, want 1（防抖应忽略重复入队）", len(m.queue))
	}
}

func TestRemovePlayer(t *testing.T) {
	t.Run("移除队首", func(t *testing.T) {
		m := newTestMatcher()
		m.AddPlayer(1)
		m.AddPlayer(2)
		m.AddPlayer(3)
		m.RemovePlayer(1)
		if len(m.queue) != 2 || m.queue[0] != 2 || m.queue[1] != 3 {
			t.Errorf("移除队首后队列 = %v, want [2 3]", m.queue)
		}
	})

	t.Run("移除队中", func(t *testing.T) {
		m := newTestMatcher()
		m.AddPlayer(1)
		m.AddPlayer(2)
		m.AddPlayer(3)
		m.RemovePlayer(2)
		if len(m.queue) != 2 || m.queue[0] != 1 || m.queue[1] != 3 {
			t.Errorf("移除队中后队列 = %v, want [1 3]", m.queue)
		}
	})

	t.Run("移除不存在的玩家无副作用", func(t *testing.T) {
		m := newTestMatcher()
		m.AddPlayer(1)
		m.RemovePlayer(99)
		if len(m.queue) != 1 || m.queue[0] != 1 {
			t.Errorf("移除不存在玩家后队列 = %v, want [1]", m.queue)
		}
	})

	t.Run("对空队列移除无副作用", func(t *testing.T) {
		m := newTestMatcher()
		m.RemovePlayer(1) // 不应 panic
	})
}

func TestMatcherStartMatchmaking(t *testing.T) {
	// Start 使用 1 秒 Tick 扫描队列，此处等待略超一个周期验证发车行为
	m := newTestMatcher()
	m.Start()

	m.AddPlayer(101)
	m.AddPlayer(202)

	select {
	case res := <-m.ResultCh:
		if res.Player1 != 101 || res.Player2 != 202 {
			t.Errorf("发车结果 = (P1:%d, P2:%d), want (101, 202)", res.Player1, res.Player2)
		}
		if res.RoomID == "" {
			t.Error("RoomID 不应为空")
		}
		// 房间号应为合法 UUID（36 字符含连字符）
		if len(res.RoomID) != 36 {
			t.Errorf("RoomID = %q, 长度 %d, want 36（UUID 格式）", res.RoomID, len(res.RoomID))
		}
	case <-time.After(2 * time.Second):
		t.Fatal("2 秒内未产出匹配结果")
	}

	// 发车后两人应移出队列
	m.mu.Lock()
	remaining := len(m.queue)
	m.mu.Unlock()
	if remaining != 0 {
		t.Errorf("发车后队列长度 = %d, want 0", remaining)
	}
}

func TestMatcherStartNoMatchWithSinglePlayer(t *testing.T) {
	m := newTestMatcher()
	m.Start()
	m.AddPlayer(1)

	select {
	case res := <-m.ResultCh:
		t.Errorf("单人排队不应发车, got %+v", res)
	case <-time.After(1500 * time.Millisecond):
		// 预期：一个 Tick 周期内不满 2 人，不产出结果
	}
}
