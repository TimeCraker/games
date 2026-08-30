-- 网关侧(gameplay 域):聊天记录 + 玩家位置存档(JSONB)

-- name: InsertMessage :exec
INSERT INTO messages (sender, content)
VALUES ($1, $2);

-- name: GetPlayerPosition :one
SELECT payload
FROM player_positions
WHERE user_id = $1;

-- name: UpsertPlayerPosition :exec
INSERT INTO player_positions (user_id, payload)
VALUES ($1, $2)
ON CONFLICT (user_id) DO UPDATE
SET payload = EXCLUDED.payload,
    updated_at = now();
