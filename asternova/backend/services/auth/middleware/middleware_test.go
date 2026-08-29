package middleware

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

// TestMain 注入 JWT 密钥：AuthMiddleware 走 utils.GenerateToken/ParseToken，
// 密钥 env 化后未设 JWT_SECRET 会被 fail loud 拒绝
func TestMain(m *testing.M) {
	os.Setenv("JWT_SECRET", "unit-test-secret-0123456789abcdef")
	os.Exit(m.Run())
}

// perform 构造一个仅挂载被测中间件的上下文并执行。
func perform(authHeader string) (*gin.Context, *httptest.ResponseRecorder) {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("GET", "/", nil)
	if authHeader != "" {
		c.Request.Header.Set("Authorization", authHeader)
	}
	AuthMiddleware()(c)
	return c, w
}

func TestAuthMiddleware(t *testing.T) {
	validToken, err := utils.GenerateToken(42)
	if err != nil {
		t.Fatalf("生成测试 token 失败: %v", err)
	}

	cases := []struct {
		name       string
		authHeader string
		wantStatus int
		wantAbort  bool
	}{
		{"缺少 Authorization 头", "", http.StatusUnauthorized, true},
		{"非 Bearer 前缀", "Token abc.def.ghi", http.StatusUnauthorized, true},
		{"只有 Bearer 无 token", "Bearer", http.StatusUnauthorized, true},
		{"Bearer 后多余分段", "Bearer a b", http.StatusUnauthorized, true},
		{"非法 token 内容", "Bearer garbage", http.StatusUnauthorized, true},
		{"合法 token 放行", "Bearer " + validToken, http.StatusOK, false},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			c, w := perform(tc.authHeader)

			if c.IsAborted() != tc.wantAbort {
				t.Errorf("IsAborted = %v, want %v", c.IsAborted(), tc.wantAbort)
			}
			if w.Code != tc.wantStatus {
				t.Errorf("status = %d, want %d", w.Code, tc.wantStatus)
			}
		})
	}

	t.Run("合法 token 注入 userID", func(t *testing.T) {
		c, _ := perform("Bearer " + validToken)
		v, exists := c.Get("userID")
		if !exists {
			t.Fatal("userID 未注入上下文")
		}
		if id, ok := v.(int); !ok || id != 42 {
			t.Errorf("userID = %v(%T), want int 42", v, v)
		}
	})
}
