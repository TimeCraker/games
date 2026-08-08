/**
 * 全局公共 URL：来自根目录 .env.development / .env.production 的 NEXT_PUBLIC_*（构建时内联）。
 * 业务代码请从这里取地址，避免散落硬编码。
 */
const trimTrailingSlash = (value: string) => value.replace(/\/$/, "")

export const apiUrlRoot = trimTrailingSlash(process.env.NEXT_PUBLIC_API_URL ?? "")

export const wsUrl = process.env.NEXT_PUBLIC_WS_URL ?? ""

/** Go 网关 REST 前缀：{apiUrlRoot}/api/v1 */
export const apiV1BaseUrl = apiUrlRoot ? `${apiUrlRoot}/api/v1` : ""
