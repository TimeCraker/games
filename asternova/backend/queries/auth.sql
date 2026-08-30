-- 用户查询(auth 域)

-- name: GetUserByID :one
SELECT id, username, password, email, created_at, updated_at, deleted_at
FROM users
WHERE id = $1;

-- name: GetUserByUsername :one
SELECT id, username, password, email, created_at, updated_at, deleted_at
FROM users
WHERE username = $1;

-- name: GetUserByEmail :one
SELECT id, username, password, email, created_at, updated_at, deleted_at
FROM users
WHERE email = $1;

-- name: GetUserByIdentifier :one
SELECT id, username, password, email, created_at, updated_at, deleted_at
FROM users
WHERE username = $1 OR email = $1;

-- name: CreateUser :one
INSERT INTO users (username, password, email)
VALUES ($1, $2, $3)
RETURNING id, username, password, email, created_at, updated_at, deleted_at;

-- name: UpdateUserPassword :exec
UPDATE users
SET password = $1, updated_at = now()
WHERE id = $2;
