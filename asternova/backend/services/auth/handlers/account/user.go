package account

import (
	"net/http"

	"github.com/gin-gonic/gin"

	// 引入 db 包以使用 db.Q(sqlc 查询层)
	"github.com/TimeCraker/asternova-backend/services/auth/db"
)

// GetMe 获取当前登录玩家的详细信息
func GetMe(c *gin.Context) {
	// 1. 从中间件 Context 中获取 userID (由 AuthMiddleware 解析 Token 后存入)
	userID, exists := c.Get("userID")
	if !exists {
		c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "未授权，请先登录"})
		return
	}

	// 2. 查询数据库
	user, err := db.Q.GetUserByID(c.Request.Context(), int64(userID.(int)))
	if err != nil {
		c.AbortWithStatusJSON(http.StatusNotFound, gin.H{"error": "玩家数据不存在"})
		return
	}

	// 3. 返回脱敏后的用户信息
	c.JSON(http.StatusOK, gin.H{
		"id":       user.ID,
		"username": user.Username,
		"created":  user.CreatedAt,
	})
}
