// 由 scripts/fetch-arcade-art.mjs 生成，请勿手改。
// 用途：next/image 的 placeholder="blur" + blurDataURL，消除 key art 加载白闪。

export type KeyArtSlug = "shoot-them-all" | "lets-running" | "merge" | "nebula-survivor" | "xiaoxiaole"

export const KEY_ART: Record<KeyArtSlug, { width: number; height: number; lqip: string }> = {
  "shoot-them-all": { width: 900, height: 600, lqip: "data:image/webp;base64,UklGRoAAAABXRUJQVlA4IHQAAADwBACdASoYABgAPs1SoE0npKMiN+gA8BmJQBjehkoTLG5a/OSsCWLUSk+XtFhaGAAA/vd5agomIvMFWKwKuIk1Ht5vUKxCyUWsSLrY1ZSaa60Do/ZhI2GiP0P5+yvPNjd/BJ73LrqbcXbqT5YiLbSGdAAAAA==" },
  "lets-running": { width: 900, height: 600, lqip: "data:image/webp;base64,UklGRlwAAABXRUJQVlA4IFAAAADQAwCdASoYAAsAPulgq00pJaQiMAgBIB0JYwCo9BommfcL24XvfgAA/vF+dwD5aENMXdWXTNAP5cc5DlWbuS6Ts4a+ACawiFhuHLBjleQAAA==" },
  "merge": { width: 900, height: 600, lqip: "data:image/webp;base64,UklGRngAAABXRUJQVlA4IGwAAACQBQCdASoYABgAPulmrk+pJSSiKAqpIB0JYwDA3BEd+pNlzrvgGxotJVtUk3/g/L+uPYgyIAD+9Cp9/EUGV+QPky29Lp2+zB4ACv30z517OW0WxK4NkwByXgKSrtohO27z6TZhfTAC8TU4EAA=" },
  "nebula-survivor": { width: 1600, height: 1000, lqip: "data:image/webp;base64,UklGRmoAAABXRUJQVlA4IF4AAADwBACdASoYABQAPulgpk2pJaMiMBgMASAdCUAYbgIdh9DMfGX8FdQec51g+sNYAQAA/vQoW48NwJ0WiXF2SXyfrmob5P1E7S8t6HPdtLfuMMz9d1dGNwdPbAAHaAAA" },
  "xiaoxiaole": { width: 900, height: 600, lqip: "data:image/webp;base64,UklGRmYAAABXRUJQVlA4IFoAAADQBACdASoYABgAPtFcok0oJaMlt/qoAQAaCWkAAOz1m/k6I1SrM4JxS6CSUOyl4AD++QsSDC4GZNanegTffHtRv8rhhLnndeqK2852sdeSffOosqRH024AAAA=" },
}
