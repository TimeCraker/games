package account

import (
	"crypto/rand"
	"encoding/hex"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/TimeCraker/asternova-backend/services/auth/db"
	"github.com/TimeCraker/asternova-backend/services/auth/db/sqlc"
	"github.com/TimeCraker/asternova-backend/services/auth/utils"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

// 邀请码经环境变量 GUEST_INVITE_CODE 下发；未配置则游客通道整体禁用，
// 防止公开仓库硬编码默认码被脚本刷号

type guestLoginRequest struct {
	InviteCode string `json:"inviteCode" binding:"required"`
}

func randomHex(nBytes int) string {
	b := make([]byte, nBytes)
	if _, err := rand.Read(b); err != nil {
		return ""
	}
	return hex.EncodeToString(b)
}

func randomGuestIdentity() (username string, email string) {
	suffix := strings.ToUpper(randomHex(3))
	if suffix == "" {
		suffix = strings.ToUpper(time.Now().Format("150405"))
	}
	username = "Guest_" + suffix
	email = strings.ToLower("guest_" + suffix + "@guest.asternova.local")
	return
}

// GuestLogin 邀请码游客登录：输入固定邀请码后自动分配随机访客身份并进入大厅
func GuestLogin(c *gin.Context) {
	var req guestLoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "参数错误"})
		return
	}
	inviteCode := os.Getenv("GUEST_INVITE_CODE")
	if inviteCode == "" {
		c.JSON(http.StatusServiceUnavailable, gin.H{"error": "游客通道未开放"})
		return
	}
	if strings.TrimSpace(req.InviteCode) != inviteCode {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "邀请码无效"})
		return
	}

	passwordSeed := randomHex(12)
	if passwordSeed == "" {
		passwordSeed = "guest_fallback_" + time.Now().Format("20060102150405")
	}
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(passwordSeed), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "服务器内部错误"})
		return
	}

	var created *sqlc.CreateUserRow
	for i := 0; i < 6; i++ {
		username, email := randomGuestIdentity()
		row, err := db.Q.CreateUser(c.Request.Context(), sqlc.CreateUserParams{
			Username: username,
			Email:    email,
			Password: string(hashedPassword),
		})
		if err == nil {
			created = &row
			break
		}
	}
	if created == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "游客身份分配失败，请重试"})
		return
	}

	token, err := utils.GenerateToken(int(created.ID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Token生成失败"})
		return
	}

	_ = db.SetUserOnline(uint(created.ID))
	c.JSON(http.StatusOK, gin.H{
		"message": "游客登录成功",
		"token":   token,
		"user": gin.H{
			"id":       created.ID,
			"username": created.Username,
			"email":    created.Email,
			"is_guest": true,
		},
	})
}

