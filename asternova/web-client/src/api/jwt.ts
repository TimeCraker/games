import { jwtDecode } from "jwt-decode"

type JwtPayloadShape = {
  user_id?: number
  userID?: number
  exp?: number
  iat?: number
}

export function extractUserIdFromToken(token: string): number {
  const payload = jwtDecode<JwtPayloadShape>(token)

  const candidate = payload.user_id ?? payload.userID
  if (typeof candidate === "number" && Number.isFinite(candidate)) {
    return candidate
  }

  throw new Error("无法从 Token 中解析 userId")
}

