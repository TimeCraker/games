package utils

import (
	"strings"
	"testing"
)

// TestSendVerificationEmailRequiresSecret 验证 SMTP_SECRET 缺失时返回明确错误，
// 且在触达网络（tls.Dial / smtp 认证）之前就短路返回。
func TestSendVerificationEmailRequiresSecret(t *testing.T) {
	t.Setenv("SMTP_SECRET", "")

	err := SendVerificationEmail("recipient@example.com", "123456")
	if err == nil {
		t.Fatal("SMTP_SECRET 为空时应返回错误")
	}
	if !strings.Contains(err.Error(), "SMTP_SECRET not set") {
		t.Errorf("错误信息 = %q, want 含 \"SMTP_SECRET not set\"", err.Error())
	}
}
