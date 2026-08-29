package utils

import (
	"testing"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

func TestGenerateAndParseTokenRoundTrip(t *testing.T) {
	cases := []struct {
		name   string
		userID int
	}{
		{"常规正数 ID", 42},
		{"零值 ID", 0},
		{"大数 ID", 1 << 20},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			token, err := GenerateToken(tc.userID)
			if err != nil {
				t.Fatalf("GenerateToken 失败: %v", err)
			}
			if token == "" {
				t.Fatal("生成的 token 为空")
			}

			claims, err := ParseToken(token)
			if err != nil {
				t.Fatalf("ParseToken 失败: %v", err)
			}
			if claims.UserID != tc.userID {
				t.Errorf("claims.UserID = %d, want %d", claims.UserID, tc.userID)
			}
		})
	}
}

func TestTokenExpiryWindow(t *testing.T) {
	token, err := GenerateToken(1)
	if err != nil {
		t.Fatalf("GenerateToken 失败: %v", err)
	}
	claims, err := ParseToken(token)
	if err != nil {
		t.Fatalf("ParseToken 失败: %v", err)
	}
	if claims.ExpiresAt == nil {
		t.Fatal("token 应携带过期时间")
	}
	// 有效期契约：72 小时
	if d := time.Until(claims.ExpiresAt.Time); d < 71*time.Hour || d > 72*time.Hour+time.Minute {
		t.Errorf("有效期 = %v, want 约 72h", d)
	}
}

func TestParseTokenRejectsTamperedToken(t *testing.T) {
	token, err := GenerateToken(42)
	if err != nil {
		t.Fatalf("GenerateToken 失败: %v", err)
	}

	// 篡改 payload 末段后签名不再匹配
	tampered := token[:len(token)-2] + "xx"
	if _, err := ParseToken(tampered); err == nil {
		t.Error("篡改后的 token 应被拒绝")
	}
}

func TestParseTokenRejectsWrongSecret(t *testing.T) {
	// 用其他密钥签发，模拟伪造 token
	claims := Claims{
		UserID: 42,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
		},
	}
	forged, err := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString([]byte("another-secret"))
	if err != nil {
		t.Fatalf("构造伪造 token 失败: %v", err)
	}
	if _, err := ParseToken(forged); err == nil {
		t.Error("错误密钥签发的 token 应被拒绝")
	}
}

func TestParseTokenRejectsExpired(t *testing.T) {
	// 用真实密钥签发一个已过期的 token
	claims := Claims{
		UserID: 42,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(-time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now().Add(-2 * time.Hour)),
		},
	}
	expired, err := jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString(jwtSecret)
	if err != nil {
		t.Fatalf("构造过期 token 失败: %v", err)
	}
	if _, err := ParseToken(expired); err == nil {
		t.Error("过期 token 应被拒绝")
	}
}

func TestParseTokenRejectsGarbage(t *testing.T) {
	cases := []struct {
		name  string
		token string
	}{
		{"空字符串", ""},
		{"纯乱码", "not-a-jwt"},
		{"缺少签名段", "eyJhbGciOiJIUzI1NiJ9.eyJmb28iOiJiYXIifQ."},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if _, err := ParseToken(tc.token); err == nil {
				t.Errorf("ParseToken(%q) 应返回错误", tc.token)
			}
		})
	}
}
