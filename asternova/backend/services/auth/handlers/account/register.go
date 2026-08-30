package account

import (
	"net/http"

	"github.com/TimeCraker/asternova-backend/services/auth/db"
	"github.com/TimeCraker/asternova-backend/services/auth/db/sqlc"
	"github.com/TimeCraker/asternova-backend/services/auth/utils"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

// RegisterRequest 定义了注册请求的 JSON 格式
type RegisterRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
	// 新增邮箱和验证码字段
	Email string `json:"email" binding:"required,email"`
	Code  string `json:"code" binding:"required,len=6"`
}

// Register 处理用户注册逻辑
func Register(c *gin.Context) {
	var req RegisterRequest

	// 1. 绑定并校验 JSON 输入
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "参数格式不正确"})
		return
	}

	// 1.5 从 Redis 校验验证码 (统一使用 auth_code)
	codeKey := "auth_code:" + req.Email
	expectedCode, err := db.RDB.Get(db.Ctx, codeKey).Result()
	if err != nil || expectedCode != req.Code {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "验证码错误或已过期"})
		return
	}

	// 2. 检查用户名是否已存在
	if _, err := db.Q.GetUserByUsername(c.Request.Context(), req.Username); err == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "该用户名已被占用"})
		return
	}

	// 2.5 检查邮箱是否已被注册
	if _, err := db.Q.GetUserByEmail(c.Request.Context(), req.Email); err == nil {
		c.JSON(http.StatusConflict, gin.H{"error": "该邮箱已被注册"})
		return
	}

	// 3. 加密密码
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "服务器内部错误"})
		return
	}

	// 4. 构造用户模型并存入数据库
	row, err := db.Q.CreateUser(c.Request.Context(), sqlc.CreateUserParams{
		Username: req.Username,
		Password: string(hashedPassword),
		Email:    req.Email,
	})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "用户保存失败"})
		return
	}

	// 创建成功后删除验证码，并直接签发 token（注册即登录）
	_ = db.RDB.Del(db.Ctx, codeKey).Err()
	token, err := utils.GenerateToken(int(row.ID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Token生成失败"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"message": "注册并登录成功",
		"token":   token,
		"user": gin.H{
			"id":       row.ID,
			"username": row.Username,
			"email":    row.Email,
		},
	})
}
