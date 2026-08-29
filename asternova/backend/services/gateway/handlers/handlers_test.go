package handlers

import (
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/TimeCraker/game-backend-demo/services/auth/utils"
	"github.com/gin-gonic/gin"
)

func init() {
	gin.SetMode(gin.TestMode)
}

// TestMain 注入 JWT 密钥：HandleWS 校验分支走 utils.GenerateToken，
// 密钥 env 化后未设 JWT_SECRET 会被 fail loud 拒绝
func TestMain(m *testing.M) {
	os.Setenv("JWT_SECRET", "unit-test-secret-0123456789abcdef")
	os.Exit(m.Run())
}

// performWS 以 query 串调用 HandleWS，仅覆盖 WebSocket 升级之前的入参校验分支。
func performWS(query string) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("GET", "/ws?"+query, nil)
	HandleWS()(c)
	return w
}

func TestHandleWSInputValidation(t *testing.T) {
	validToken, err := utils.GenerateToken(42)
	if err != nil {
		t.Fatalf("生成测试 token 失败: %v", err)
	}

	cases := []struct {
		name       string
		query      string
		wantStatus int
	}{
		{"缺少 token", "scope=lobby", http.StatusUnauthorized},
		{"token 无效", "token=garbage&scope=lobby", http.StatusUnauthorized},
		{"battle 作用域缺 roomId", "token=" + validToken + "&scope=battle", http.StatusBadRequest},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			w := performWS(tc.query)
			if w.Code != tc.wantStatus {
				t.Errorf("status = %d, want %d", w.Code, tc.wantStatus)
			}
		})
	}
}

func TestHubRoomHasUser(t *testing.T) {
	h := &Hub{}
	h.RegisteredRooms.Store("room-1", &Room{ID: "room-1", Players: []int{1, 2}})

	cases := []struct {
		name   string
		roomID string
		userID int
		want   bool
	}{
		{"房间内用户", "room-1", 1, true},
		{"房间外用户", "room-1", 3, false},
		{"房间不存在", "ghost", 1, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := h.RoomHasUser(tc.roomID, tc.userID); got != tc.want {
				t.Errorf("RoomHasUser(%q, %d) = %v, want %v", tc.roomID, tc.userID, got, tc.want)
			}
		})
	}
}

func TestHubJoinRoomGuards(t *testing.T) {
	h := &Hub{}

	// nil client / 空 roomID / nil 连接均应被静默拒绝，不产生房间
	h.JoinRoom(nil, "room-1")
	h.JoinRoom(&Client{UserID: 1}, "")
	h.JoinRoom(&Client{UserID: 1, Conn: nil}, "room-1")

	if len(h.Rooms) != 0 {
		t.Errorf("非法入参不应创建房间, got %v", h.Rooms)
	}
}

func TestHubLeaveRoomGuards(t *testing.T) {
	t.Run("未入房玩家离开无副作用", func(t *testing.T) {
		h := &Hub{}
		h.LeaveRoom(&Client{UserID: 1}) // RoomID 为空，应直接返回
		if len(h.Rooms) != 0 {
			t.Errorf("空房间表不应被修改: %v", h.Rooms)
		}
	})

	t.Run("离开不存在的房间无副作用", func(t *testing.T) {
		h := &Hub{}
		h.LeaveRoom(&Client{UserID: 1, RoomID: "ghost"})
		if len(h.Rooms) != 0 {
			t.Errorf("空房间表不应被修改: %v", h.Rooms)
		}
	})
}

func TestHubBroadcastToRoomEmptyID(t *testing.T) {
	h := &Hub{}
	h.BroadcastToRoom("", 1, []byte("x")) // 空 roomID 应直接返回，不 panic
}
