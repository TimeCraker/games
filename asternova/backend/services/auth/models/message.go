package models

import (
	"time"
)

// Message 对应数据库中的 messages 表(表结构见 migrations/000001_init.up.sql)
type Message struct {
	ID        uint      `json:"id"`
	Sender    string    `json:"sender"`     // 发送者用户名
	Content   string    `json:"content"`    // 消息内容
	CreatedAt time.Time `json:"created_at"` // 创建时间
}
