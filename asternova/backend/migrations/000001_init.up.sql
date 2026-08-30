-- AsterNova PostgreSQL 初始 schema
-- 迁移自 MySQL 8 + GORM AutoMigrate(本地开发数据直接弃,无数据搬运)

-- 用户表(等价迁移自 GORM models.User,含 gorm.Model 标准四列)
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ,
    username    VARCHAR(50)  NOT NULL,
    password    VARCHAR(255) NOT NULL,
    email       VARCHAR(100) NOT NULL,
    CONSTRAINT users_username_key UNIQUE (username),
    CONSTRAINT users_email_key    UNIQUE (email)
);

CREATE INDEX idx_users_deleted_at ON users (deleted_at);

-- 聊天消息表(等价迁移自 GORM models.Message)
CREATE TABLE messages (
    id         BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    sender     VARCHAR(255) NOT NULL,
    content    TEXT         NOT NULL
);

-- 玩家存档表(原 player_positions,按 architecture.md §5 定案升级为 JSONB 范式:
-- payload 内携带 schema_version,当前结构 {"schema_version":1,"x":..,"y":..,"z":..})
CREATE TABLE player_positions (
    user_id    BIGINT PRIMARY KEY,
    payload    JSONB       NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
