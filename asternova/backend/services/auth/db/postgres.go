package db

import (
	"context"
	"database/sql"
	"errors"
	"io/fs"
	"log"
	"os"
	"time"

	migrate "github.com/golang-migrate/migrate/v4"
	"github.com/golang-migrate/migrate/v4/database/postgres"
	"github.com/golang-migrate/migrate/v4/source/iofs"
	_ "github.com/jackc/pgx/v5/stdlib" // 注册 database/sql "pgx" 驱动供迁移连接使用
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/TimeCraker/asternova-backend/services/auth/db/sqlc"
)

// Q 是 sqlc 生成的查询层,所有 SQL 声明在 backend/queries/*.sql,业务代码不得手写内联 SQL
var Q *sqlc.Queries

// InitPostgres 连接 PostgreSQL(连接池),并执行启动迁移(幂等)。
// migrationsFS 由 main 包注入(go:embed 不允许引用上级目录)。
func InitPostgres(migrationsFS fs.FS) {
	dsn := os.Getenv("DATABASE_DSN")
	if dsn == "" {
		dsn = "postgres://postgres:rootpassword@localhost:5432/game_dev?sslmode=disable"
	}

	runMigrations(dsn, migrationsFS)

	pool, err := pgxpool.New(context.Background(), dsn)
	if err != nil {
		log.Fatalf("❌ PostgreSQL 连接池创建失败: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := pool.Ping(ctx); err != nil {
		log.Fatalf("❌ PostgreSQL 连接失败: %v", err)
	}

	Q = sqlc.New(pool)
	log.Println("✅ PostgreSQL 初始化成功,表结构已通过 migrations 同步")
}

// runMigrations 执行内嵌的 golang-migrate 迁移(幂等:已应用的迁移自动跳过)
func runMigrations(dsn string, migrationsFS fs.FS) {
	src, err := iofs.New(migrationsFS, "migrations")
	if err != nil {
		log.Fatalf("❌ 读取内嵌迁移文件失败: %v", err)
	}

	sqlDB, err := sql.Open("pgx", dsn)
	if err != nil {
		log.Fatalf("❌ 迁移连接创建失败: %v", err)
	}
	defer sqlDB.Close()

	driver, err := postgres.WithInstance(sqlDB, &postgres.Config{})
	if err != nil {
		log.Fatalf("❌ 迁移驱动初始化失败: %v", err)
	}

	m, err := migrate.NewWithInstance("iofs", src, "game_dev", driver)
	if err != nil {
		log.Fatalf("❌ 迁移实例创建失败: %v", err)
	}

	if err := m.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
		log.Fatalf("❌ 数据库迁移失败: %v", err)
	}
	log.Println("✅ 数据库迁移检查完成(migrate up)")
}
