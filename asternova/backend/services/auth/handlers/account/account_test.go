package account

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
)

func init() {
	gin.SetMode(gin.TestMode)
}

func TestRandomHex(t *testing.T) {
	cases := []struct {
		name     string
		nBytes   int
		wantLen  int
	}{
		{"3 字节输出 6 个 hex 字符", 3, 6},
		{"12 字节输出 24 个 hex 字符", 12, 24},
		{"0 字节输出空串", 0, 0},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			got := randomHex(tc.nBytes)
			if len(got) != tc.wantLen {
				t.Fatalf("randomHex(%d) 长度 = %d, want %d", tc.nBytes, len(got), tc.wantLen)
			}
			for _, ch := range got {
				isHex := (ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f')
				if !isHex {
					t.Errorf("randomHex(%d) 含非小写 hex 字符 %q", tc.nBytes, ch)
					break
				}
			}
		})
	}
}

func TestRandomGuestIdentityFormat(t *testing.T) {
	for i := 0; i < 20; i++ {
		username, email := randomGuestIdentity()

		if !strings.HasPrefix(username, "Guest_") {
			t.Errorf("username = %q, want Guest_ 前缀", username)
		}
		suffix := strings.TrimPrefix(username, "Guest_")
		if len(suffix) != 6 {
			t.Errorf("username 后缀长度 = %d, want 6（3 字节 hex）", len(suffix))
		}
		if strings.ToUpper(suffix) != suffix {
			t.Errorf("username 后缀 %q 应为大写", suffix)
		}

		if !strings.HasSuffix(email, "@guest.asternova.local") {
			t.Errorf("email = %q, want @guest.asternova.local 域名", email)
		}
		if strings.ContainsAny(email, "ABCDEF") {
			t.Errorf("email = %q 应全小写", email)
		}
		if !strings.HasPrefix(email, "guest_"+strings.ToLower(suffix)) {
			t.Errorf("email 用户部分应与 username 后缀对应: %q vs %q", email, username)
		}
	}
}

func TestIsValidPassword(t *testing.T) {
	cases := []struct {
		name     string
		password string
		want     bool
	}{
		{"字母+数字组合合法", "abc123", true},
		{"含大写字母合法", "Abc123", true},
		{"纯数字不合法", "123456", false},
		{"纯字母不合法", "abcdef", false},
		{"短于 6 位不合法", "ab12", false},
		{"长于 20 位不合法", "abcde12345abcde123456", false},
		{"含空格不合法", "abc 123", false},
		{"含下划线不合法", "abc_123", false},
		{"含符号不合法", "abc-123", false},
		{"含中文不合法", "密码abc123", false},
		{"空串不合法", "", false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := isValidPassword(tc.password); got != tc.want {
				t.Errorf("isValidPassword(%q) = %v, want %v", tc.password, got, tc.want)
			}
		})
	}
}

// postJSON 构造 JSON POST 请求调用 handler，返回响应。
func postJSON(handler gin.HandlerFunc, body string) *httptest.ResponseRecorder {
	w := httptest.NewRecorder()
	c, _ := gin.CreateTestContext(w)
	c.Request = httptest.NewRequest("POST", "/", strings.NewReader(body))
	c.Request.Header.Set("Content-Type", "application/json")
	handler(c)
	return w
}

func responseError(t *testing.T, w *httptest.ResponseRecorder) string {
	t.Helper()
	var resp map[string]string
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatalf("响应不是合法 JSON: %v (body=%q)", err, w.Body.String())
	}
	return resp["error"]
}

// 以下仅覆盖触达外部设施（MySQL/Redis）之前的入参校验分支，
// 数据库/Redis 相关路径不纳入无设施单测范围。

func TestRegisterRejectsInvalidPayload(t *testing.T) {
	cases := []struct {
		name string
		body string
	}{
		{"缺少邮箱", `{"username":"a","password":"abc123","code":"123456"}`},
		{"邮箱格式错误", `{"username":"a","password":"abc123","email":"not-an-email","code":"123456"}`},
		{"验证码长度不足", `{"username":"a","password":"abc123","email":"a@b.com","code":"123"}`},
		{"非 JSON 主体", `not-json`},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			w := postJSON(Register, tc.body)
			if w.Code != http.StatusBadRequest {
				t.Errorf("status = %d, want 400", w.Code)
			}
			if msg := responseError(t, w); msg != "参数格式不正确" {
				t.Errorf("error = %q, want 参数格式不正确", msg)
			}
		})
	}
}

func TestLoginRejectsInvalidPayload(t *testing.T) {
	cases := []struct {
		name string
		body string
	}{
		{"缺少密码", `{"identifier":"someone"}`},
		{"缺少标识符", `{"password":"abc123"}`},
		{"非 JSON 主体", `not-json`},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			w := postJSON(Login, tc.body)
			if w.Code != http.StatusBadRequest {
				t.Errorf("status = %d, want 400", w.Code)
			}
			if msg := responseError(t, w); msg != "参数错误" {
				t.Errorf("error = %q, want 参数错误", msg)
			}
		})
	}
}

func TestLoginWithEmailRejectsInvalidPayload(t *testing.T) {
	w := postJSON(LoginWithEmail, `{"email":"bad-email","code":"123456"}`)
	if w.Code != http.StatusBadRequest {
		t.Errorf("status = %d, want 400", w.Code)
	}
}

func TestGuestLoginInviteCodeGate(t *testing.T) {
	t.Run("缺少邀请码", func(t *testing.T) {
		t.Setenv("GUEST_INVITE_CODE", "test-code")
		w := postJSON(GuestLogin, `{}`)
		if w.Code != http.StatusBadRequest {
			t.Errorf("status = %d, want 400", w.Code)
		}
	})

	t.Run("邀请码错误", func(t *testing.T) {
		// 错误邀请码在写入数据库之前即被拒绝
		t.Setenv("GUEST_INVITE_CODE", "test-code")
		w := postJSON(GuestLogin, `{"inviteCode":"wrong"}`)
		if w.Code != http.StatusUnauthorized {
			t.Errorf("status = %d, want 401", w.Code)
		}
		if msg := responseError(t, w); msg != "邀请码无效" {
			t.Errorf("error = %q, want 邀请码无效", msg)
		}
	})

	t.Run("未配置邀请码时通道禁用", func(t *testing.T) {
		// GUEST_INVITE_CODE 未配置 → 整个游客通道 503，防止公开仓库泄露默认码
		w := postJSON(GuestLogin, `{"inviteCode":"77"}`)
		if w.Code != http.StatusServiceUnavailable {
			t.Errorf("status = %d, want 503", w.Code)
		}
		if msg := responseError(t, w); msg != "游客通道未开放" {
			t.Errorf("error = %q, want 游客通道未开放", msg)
		}
	})
}

func TestResetPasswordPreChecksBeforeStore(t *testing.T) {
	t.Run("两次密码不一致", func(t *testing.T) {
		w := postJSON(ResetPasswordWithEmail, `{"email":"a@b.com","code":"123456","newPassword":"abc123","confirmPassword":"abc124"}`)
		if w.Code != http.StatusBadRequest {
			t.Errorf("status = %d, want 400", w.Code)
		}
		if msg := responseError(t, w); msg != "两次密码输入不一致" {
			t.Errorf("error = %q, want 两次密码输入不一致", msg)
		}
	})

	t.Run("密码强度不足", func(t *testing.T) {
		w := postJSON(ResetPasswordWithEmail, `{"email":"a@b.com","code":"123456","newPassword":"abc1","confirmPassword":"abc1"}`)
		if w.Code != http.StatusBadRequest {
			t.Errorf("status = %d, want 400", w.Code)
		}
		if msg := responseError(t, w); msg != "密码需为 6-20 位字母+数字组合" {
			t.Errorf("error = %q, want 密码需为 6-20 位字母+数字组合", msg)
		}
	})
}
