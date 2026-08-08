import axios, { AxiosError } from "axios"

import { apiV1BaseUrl } from "@/src/config/public-env"

// ===== 新增代码 START =====
// 使用 process.env.NEXT_PUBLIC_API_URL（经 public-env 归一化）作为 REST 根，对应 /api/v1
const API_BASE_URL = apiV1BaseUrl

export const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})
// ===== 新增代码 END =====

type ApiErrorBody = {
  error?: string
  message?: string
}

export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const axErr = err as AxiosError<ApiErrorBody>
    const body = axErr.response?.data
    return (
      body?.error ||
      body?.message ||
      axErr.response?.statusText ||
      axErr.message ||
      "请求失败"
    )
  }
  if (err instanceof Error) return err.message
  return "请求失败"
}

export async function sendCode(email: string): Promise<{ message: string }> {
  const res = await authApi.post("/send_code", { email })
  return res.data as { message: string }
}

export async function register(
  username: string,
  password: string,
  email: string,
  code: string,
): Promise<{ message: string; token: string; user: { id: number; username: string; email: string } }> {
  const res = await authApi.post("/register", { username, password, email, code })
  return res.data as { message: string; token: string; user: { id: number; username: string; email: string } }
}

export async function login(
  identifier: string,
  password: string,
): Promise<{ message: string; token: string; user?: { id: number; username: string; email: string } }> {
  const res = await authApi.post("/login", { identifier, password })
  return res.data as { message: string; token: string; user?: { id: number; username: string; email: string } }
}

export async function guestLogin(
  inviteCode: string,
): Promise<{ message: string; token: string; user?: { id: number; username: string; email: string; is_guest?: boolean } }> {
  const res = await authApi.post("/guest_login", { inviteCode })
  return res.data as { message: string; token: string; user?: { id: number; username: string; email: string; is_guest?: boolean } }
}

export async function loginWithEmail(
  email: string,
  code: string,
): Promise<
  | { message: string; token: string; user?: { id: number; username: string; email: string } }
  | { action: "require_setup"; message: string }
> {
  const res = await authApi.post("/login_with_email", { email, code })
  return res.data as
    | { message: string; token: string; user?: { id: number; username: string; email: string } }
    | { action: "require_setup"; message: string }
}

export async function resetPasswordWithEmail(
  email: string,
  code: string,
  newPassword: string,
  confirmPassword: string,
): Promise<{ message: string; identifier: string }> {
  const res = await authApi.post("/reset_password", {
    email,
    code,
    newPassword,
    confirmPassword,
  })
  return res.data as { message: string; identifier: string }
}

