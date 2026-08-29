package handlers

import (
	"testing"
)

func TestOriginAllowed(t *testing.T) {
	cases := []struct {
		name      string
		allowlist string
		origin    string
		want      bool
	}{
		{"清单内线上域放行", "https://game.asterforge.top,http://localhost:3001", "https://game.asterforge.top", true},
		{"异域拒绝", "https://game.asterforge.top", "https://evil.example", false},
		{"localhost 任意端口放行", "https://game.asterforge.top", "http://localhost:3001", true},
		{"127.0.0.1 任意端口放行", "https://game.asterforge.top", "http://127.0.0.1:5173", true},
		{"清单外同协议域拒绝", "https://game.asterforge.top", "https://game.asterforge.top.evil.com", false},
		{"大小写路径差异视为不同 Origin 拒绝", "https://game.asterforge.top", "https://Game.AsterForge.TOP/path", false},
		{"清单项两端空白被裁剪后匹配", " https://game.asterforge.top , http://localhost:3001 ", "https://game.asterforge.top", true},
		{"env 缺省回落只认线上域(线上放行)", "", "https://game.asterforge.top", true},
		{"env 缺省回落只认线上域(异域拒绝)", "", "https://evil.example", false},
		{"空 Origin 拒绝", "https://game.asterforge.top", "", false},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Setenv("WS_ORIGIN_ALLOWLIST", tc.allowlist)
			if got := originAllowed(tc.origin); got != tc.want {
				t.Errorf("originAllowed(%q) with allowlist %q = %v, want %v", tc.origin, tc.allowlist, got, tc.want)
			}
		})
	}
}
