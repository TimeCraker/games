package handlers

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/TimeCraker/asternova-backend/services/auth/db"
	"github.com/TimeCraker/asternova-backend/services/auth/db/sqlc"
	"github.com/TimeCraker/asternova-backend/services/auth/utils"

	"github.com/TimeCraker/asternova-backend/services/battle"
	"github.com/TimeCraker/asternova-backend/services/match"
	pb "github.com/TimeCraker/asternova-backend/services/proto"
	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"google.golang.org/protobuf/proto"
)

// posPayload 是玩家位置存档的 JSONB 载荷
// (architecture.md §5 定案:玩家存档类数据用 JSONB + payload 内 schema_version)
type posPayload struct {
	SchemaVersion int     `json:"schema_version"`
	X             float64 `json:"x"`
	Y             float64 `json:"y"`
	Z             float64 `json:"z"`
}

const (
	pingPeriod = 20 * time.Second
	pongWait   = 60 * time.Second
)

// originAllowed 判定请求 Origin 是否在允许清单内：
// 本地开发（localhost/127.0.0.1 任意端口）恒放行，其余按 WS_ORIGIN_ALLOWLIST 逐项匹配，
// env 缺省时只认线上域。清单外的任意网站一律拒绝，防跨站 WebSocket 劫持。
func originAllowed(origin string) bool {
	if strings.HasPrefix(origin, "http://localhost:") || strings.HasPrefix(origin, "http://127.0.0.1:") {
		return true
	}
	list := os.Getenv("WS_ORIGIN_ALLOWLIST")
	if list == "" {
		list = "https://game.asterforge.top" // 缺省只认线上域
	}
	for _, o := range strings.Split(list, ",") {
		if strings.TrimSpace(o) == origin {
			return true
		}
	}
	return false
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool { return originAllowed(r.Header.Get("Origin")) },
}

func HandleWS() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenString := c.Query("token")
		if tokenString == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "缺少 token"})
			return
		}

		claims, err := utils.ParseToken(tokenString)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "无效的 token"})
			return
		}

		userID := int(claims.UserID)
		roomID := c.Query("roomId")
		if roomID == "" {
			roomID = c.Query("room_id")
		}

		scope := c.Query("scope")
		if scope == "" {
			if roomID != "" {
				scope = "battle"
			} else {
				scope = "lobby"
			}
		}

		if scope == "battle" && roomID == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "battle scope requires roomId"})
			return
		}

		conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
		if err != nil {
			return
		}

		// 【核心修复】无论是大厅还是战斗，全部包装为带并发锁的安全 Client
		client := &Client{UserID: userID, Conn: conn}

		if scope == "lobby" {
			GlobalHub.Register(userID, client)
			sendInitialPlayersData(client)
			broadcastNewPlayerJoin(userID)
		} else {
			if !GlobalHub.RoomHasUser(roomID, userID) {
				_ = client.WriteMessage(websocket.TextMessage, []byte(`{"error":"非法房间"}`))
				_ = conn.Close()
				return
			}
			GlobalHub.JoinRoom(client, roomID)
			// 玩家真正连上战斗 WS 时，向 room 索要情报并立刻单独下发
			if roomValue, ok := GlobalHub.ActiveBattles.Load(roomID); ok {
				if br, castOK := roomValue.(*battle.BattleRoom); castOK {
					infoData := br.GenerateRoomInfo()
					_ = client.WriteMessage(websocket.TextMessage, infoData)
				}
			}
			log.Printf("🏠 玩家 %d 已加入战斗房间 roomId=%s", userID, roomID)
		}

		conn.SetReadDeadline(time.Now().Add(pongWait))
		conn.SetPongHandler(func(string) error {
			conn.SetReadDeadline(time.Now().Add(pongWait))
			return nil
		})

		// 心跳协程：现在通过 client.WriteMessage 发送，完美杜绝了多协程并发写入 Panic
		go func() {
			ticker := time.NewTicker(pingPeriod)
			defer ticker.Stop()
			for {
				<-ticker.C
				if err := client.WriteMessage(websocket.PingMessage, nil); err != nil {
					return
				}
			}
		}()

		// 唯一的、干净的读消息循环
		for {
			messageType, message, err := conn.ReadMessage()
			if err != nil {
				match.GlobalMatcher.RemovePlayer(uint32(userID))
				if scope == "battle" {
					GlobalHub.LeaveRoom(client)
				} else {
					GlobalHub.Unregister(userID)
					broadcastPlayerLeave(userID)
				}
				break
			}

			// 拦截 Godot 发来的 JSON 文本格式大招指令
			if len(message) > 0 && message[0] == '{' {
				var jsonObj struct {
					Type string `json:"type"`
				}
				if err := json.Unmarshal(message, &jsonObj); err == nil && jsonObj.Type == "cast_ultimate" {
					if scope == "battle" {
						if roomValue, ok := GlobalHub.ActiveBattles.Load(roomID); ok {
							if br, castOK := roomValue.(*battle.BattleRoom); castOK {
								select {
								case br.UltCh <- uint32(userID):
								default:
								}
							}
						}
					}
					continue
				}
			}

			// 统一解码层
			var msg pb.GameMessage
			if messageType == websocket.TextMessage {
				if err := json.Unmarshal(message, &msg); err != nil {
					continue
				}
			} else if messageType == websocket.BinaryMessage {
				if err := proto.Unmarshal(message, &msg); err != nil {
					continue
				}
			} else {
				continue
			}

			// 全局拦截：匹配请求
			if msg.Type == "match_req" {
				match.GlobalMatcher.AddPlayer(uint32(userID))
				continue
			}

			// 战斗作用域路由
			if scope == "battle" {
				if msg.Type == "input" {
					if roomValue, ok := GlobalHub.ActiveBattles.Load(roomID); ok {
						if battleRoom, castOK := roomValue.(*battle.BattleRoom); castOK {
							// 非阻塞丢入物理引擎，绝不卡死主协程
							select {
							case battleRoom.InputCh <- battle.InputEvent{
								UserID: uint32(userID),
								Input: battle.InputSnapshot{
									InputX:      float64(msg.InputX),
									InputY:      float64(msg.InputY),
									IsCharging:  msg.IsCharging,
									IsAttacking: msg.IsAttacking,
									MouseX:      float64(msg.MouseX),
									MouseY:      float64(msg.MouseY),
								},
							}:
							default:
							}
						}
					}
				}
				continue
			}

			// 大厅作用域路由
			if msg.Type == "chat" {
				handleChatLogic(userID, msg.Content)
			} else if msg.Type == "move" {
				handleMoveLogic(userID, msg.X, msg.Y, msg.Z)
			}
		}
	}
}

func sendInitialPlayersData(client *Client) {
	var pbPlayers []*pb.PlayerPos
	GlobalHub.Clients.Range(func(key, value interface{}) bool {
		id := key.(int)
		raw, err := db.Q.GetPlayerPosition(context.Background(), int64(id))
		if err == nil {
			var pos posPayload
			if json.Unmarshal(raw, &pos) == nil {
				pbPlayers = append(pbPlayers, &pb.PlayerPos{
					UserId: uint32(id),
					X:      float32(pos.X),
					Y:      float32(pos.Y),
					Z:      float32(pos.Z),
					RotY:   0,
				})
			}
		}
		return true
	})
	if len(pbPlayers) > 0 {
		data := &pb.GameMessage{Type: "init_players", Players: pbPlayers}
		payload, _ := proto.Marshal(data)
		_ = client.WriteMessage(websocket.BinaryMessage, payload)
	}
}

func handleChatLogic(userID int, content string) {
	_ = db.Q.InsertMessage(context.Background(), sqlc.InsertMessageParams{
		Sender:  fmt.Sprintf("玩家 %d", userID),
		Content: content,
	})
	resp := &pb.GameMessage{Type: "chat", Content: content, UserId: uint32(userID)}
	payload, _ := proto.Marshal(resp)
	GlobalHub.Broadcast(payload)
}

func handleMoveLogic(userID int, x, y, z float32) {
	posBytes, err := json.Marshal(posPayload{SchemaVersion: 1, X: float64(x), Y: float64(y), Z: float64(z)})
	if err == nil {
		_ = db.Q.UpsertPlayerPosition(context.Background(), sqlc.UpsertPlayerPositionParams{
			UserID:  int64(userID),
			Payload: posBytes,
		})
	}
	resp := &pb.GameMessage{Type: "move", UserId: uint32(userID), X: x, Y: y, Z: z}
	payload, _ := proto.Marshal(resp)
	GlobalHub.Broadcast(payload)
}

func broadcastNewPlayerJoin(userID int) {
	raw, err := db.Q.GetPlayerPosition(context.Background(), int64(userID))
	if err == nil {
		var pos posPayload
		if json.Unmarshal(raw, &pos) == nil {
			resp := &pb.GameMessage{
				Type: "init_players",
				Players: []*pb.PlayerPos{
					{UserId: uint32(userID), X: float32(pos.X), Y: float32(pos.Y), Z: float32(pos.Z), RotY: 0},
				},
			}
			payload, _ := proto.Marshal(resp)
			GlobalHub.Broadcast(payload)
		}
	}
}

func broadcastPlayerLeave(userID int) {
	resp := &pb.GameMessage{Type: "logout", UserId: uint32(userID)}
	payload, _ := proto.Marshal(resp)
	GlobalHub.Broadcast(payload)
}
