#!/usr/bin/env node
/**
 * fetch-arcade-art.mjs — 拉取 NASA 公共领域天体图作为小游戏 key art
 *
 * 授权：NASA 图像绝大多数不受版权保护，可商用。
 *       红线：不使用 NASA 徽章 / 不暗示背书。
 * 依赖：sharp（Next 既有依赖，无需新增）
 * 用法：node scripts/fetch-arcade-art.mjs
 *
 * 输出：
 *   public/art/arcade/<slug>.webp      —— key art 本体
 *   public/art/arcade/CREDITS.md       —— 署名清单
 *   src/lib/keyArt.ts                  —— 尺寸 + LQIP base64（供 next/image placeholder="blur"）
 */
import fs from "node:fs/promises"
import path from "node:path"
import { fileURLToPath } from "node:url"
import sharp from "sharp"

const HERE = path.dirname(fileURLToPath(import.meta.url))
const OUT_DIR = path.resolve(HERE, "..", "public", "art", "arcade")
const LQIP_TS = path.resolve(HERE, "..", "src", "lib", "keyArt.ts")

/** 题材映射 + 构图焦点 + 色彩分级（pos 已逐张目视校准，勿盲改） */
const PICKS = [
  { slug: "shoot-them-all",  id: "PIA03606",                      pos: "attention", w: 900,  h: 600,  label: "蟹状星云（超新星爆发遗迹）",       grade: { saturation: 1.08, brightness: 0.97, contrast: 1.06 } },
  { slug: "lets-running",    id: "PIA21778",                      pos: "attention", w: 900,  h: 600,  label: "木星边缘与大红斑（沿弧线的疾驰感）", grade: { saturation: 1.10, brightness: 0.98, contrast: 1.05 } },
  { slug: "merge",           id: "GSFC_20171208_Archive_e001327", pos: "attention", w: 900,  h: 600,  label: "触须星系（两星系合并）",           grade: { saturation: 1.06, brightness: 0.97, contrast: 1.06 } },
  { slug: "nebula-survivor", id: "PIA25434",                      pos: "attention", w: 1600, h: 1000, label: "猎户座星云",                       grade: { saturation: 1.05, brightness: 0.96, contrast: 1.04 } },
  { slug: "xiaoxiaole",      id: "PIA21327",                      pos: "attention", w: 900,  h: 600,  label: "土星极地六边形与环（Hail the Hexagon）", grade: { duotone: "#D8A33C", brightness: 1.14, contrast: 1.08 } },
  // 大厅背景氛围层（强模糊 + 低透明度使用，故单独宽幅）
  { slug: "bg-nebula",       query: "Carina Nebula",              pos: "attention", w: 1920, h: 1080, label: "船底座星云（大厅背景氛围）",        grade: { saturation: 0.92, brightness: 0.86, contrast: 1.0 }, isBackground: true },
]

const SIZE_PREF = ["large", "medium", "orig", "small", "thumb"]

async function listAssets(id) {
  const r = await fetch("https://images-api.nasa.gov/asset/" + id)
  if (!r.ok) throw new Error("asset list " + r.status)
  const j = await r.json()
  const hrefs = (j.collection?.items ?? []).map((i) => i.href).filter((h) => /\.(jpg|jpeg|png)$/i.test(h))
  if (!hrefs.length) throw new Error("no raster asset")
  for (const t of SIZE_PREF) {
    const u = hrefs.find((h) => h.includes("~" + t + "."))
    if (u) return { url: u, tier: t }
  }
  return { url: hrefs[0], tier: "unknown" }
}

async function meta(id) {
  const r = await fetch("https://images-api.nasa.gov/search?nasa_id=" + id)
  if (!r.ok) return null
  const j = await r.json()
  return j.collection?.items?.[0]?.data?.[0] ?? null
}

/** 生成 LQIP：24px 宽 + 模糊，转 base64 data URI（供 next/image placeholder="blur"） */
async function makeLqip(buf, w, h) {
  const tiny = await sharp(buf)
    .resize({ width: 24, fit: "cover", position: "attention" })
    .blur(1.4)
    .webp({ quality: 42 })
    .toBuffer()
  return "data:image/webp;base64," + tiny.toString("base64")
}

await fs.mkdir(OUT_DIR, { recursive: true })
const credits = []
const lqipEntries = []
const blur = (w) => Math.max(0, 6 - w)

for (const p of PICKS) {
  try {
    if (!p.id && p.query) {
      const sr = await fetch("https://images-api.nasa.gov/search?media_type=image&q=" + encodeURIComponent(p.query))
      const sj = await sr.json()
      const hit = sj.collection?.items?.[0]?.data?.[0]
      if (!hit) throw new Error("no search hit for " + p.query)
      p.id = hit.nasa_id
    }
    const { url, tier } = await listAssets(p.id)
    const res = await fetch(url)
    if (!res.ok) throw new Error("download " + res.status)
    const buf = Buffer.from(await res.arrayBuffer())
    const meta0 = await sharp(buf).metadata()
    const g = p.grade ?? {}

    // 1) 缩放 + 构图
    let pipe = sharp(buf).resize({ width: p.w, height: p.h, fit: "cover", position: p.pos })
    // 2) 灰度图走琥珀双色调；彩色图保留原色
    if (g.duotone) pipe = pipe.grayscale().tint(g.duotone)
    pipe = pipe.modulate({ saturation: g.saturation ?? 1, brightness: g.brightness ?? 1 })
    // 3) 对比曲线（分离调色的第一步）
    pipe = pipe.linear(g.contrast ?? 1, -(128 * ((g.contrast ?? 1) - 1)))

    // 4) 暖色 soft-light 叠加（高光暖化、阴影保留）+ 5) 暗角
    const warm = await sharp({
      create: { width: p.w, height: p.h, channels: 4, background: { r: 216, g: 163, b: 60, alpha: 0.1 } },
    }).png().toBuffer()
    const vignette = Buffer.from(
      '<svg width="' + p.w + '" height="' + p.h + '">' +
      '<defs><radialGradient id="v" cx="50%" cy="42%" r="74%">' +
      '<stop offset="48%" stop-color="#000" stop-opacity="0"/>' +
      '<stop offset="100%" stop-color="#000" stop-opacity="0.6"/>' +
      '</radialGradient></defs>' +
      '<rect width="100%" height="100%" fill="url(#v)"/></svg>'
    )

    const info = await pipe
      .composite([{ input: warm, blend: "soft-light" }, { input: vignette, blend: "over" }])
      .webp({ quality: 84, effort: 5 })
      .toFile(path.join(OUT_DIR, p.slug + ".webp"))

    const lqip = await makeLqip(buf, p.w, p.h)
    if (!p.isBackground) lqipEntries.push({ slug: p.slug, w: p.w, h: p.h, lqip })

    const m = await meta(p.id)
    const credit = m ? [m.center, m.secondary_creator || m.photographer].filter(Boolean).join(" / ") : "NASA"
    credits.push({
      slug: p.slug, label: p.label, id: p.id, title: m?.title ?? "", credit, src: url,
      grade: g.duotone ? ("琥珀双色调 " + g.duotone) : "分离调色（暖高光 + 暗角）",
    })

    console.log(JSON.stringify({
      slug: p.slug, tier,
      input: meta0.width + "x" + meta0.height + " " + Math.round(buf.length / 1024) + "KB",
      output: info.width + "x" + info.height,
      webp: Math.round(info.size / 1024) + "KB",
      lqip: lqip.length + "B",
    }))
  } catch (e) {
    console.log(JSON.stringify({ slug: p.slug, error: String(e.message).slice(0, 160) }))
  }
}

// 署名清单
const lines = [
  "# Arcade Key Art — 素材来源与署名 / Credits",
  "",
  "本目录 key art 来自 NASA 公共领域图像档案（一般不受版权保护，可用于商业项目）。",
  "使用遵循 NASA 媒体使用准则：**不使用 NASA 徽章标识，不暗示 NASA 对本项目的背书**。",
  "获取方式见 scripts/fetch-arcade-art.mjs（可复现）。",
  "",
  "| 游戏 | 天体 | NASA ID | 标题 | 署名 | 色彩分级 |",
  "|---|---|---|---|---|---|",
  ...credits.map((c) => "| `" + c.slug + "` | " + c.label + " | [" + c.id + "](https://images.nasa.gov/details-" + c.id + ") | " + c.title + " | " + c.credit + " | " + c.grade + " |"),
  "",
  "```",
  ...credits.map((c) => c.slug + ": " + c.src),
  "```",
  "",
]
await fs.writeFile(path.join(OUT_DIR, "CREDITS.md"), lines.join("\n"), "utf8")

// LQIP 模块（供 next/image placeholder="blur"）
const ts = [
  "// 由 scripts/fetch-arcade-art.mjs 生成，请勿手改。",
  "// 用途：next/image 的 placeholder=\"blur\" + blurDataURL，消除 key art 加载白闪。",
  "",
  "export type KeyArtSlug = " + lqipEntries.map((e) => '"' + e.slug + '"').join(" | "),
  "",
  "export const KEY_ART: Record<KeyArtSlug, { width: number; height: number; lqip: string }> = {",
  ...lqipEntries.map((e) => "  " + JSON.stringify(e.slug) + ": { width: " + e.w + ", height: " + e.h + ", lqip: " + JSON.stringify(e.lqip) + " },"),
  "}",
  "",
].join("\n")
await fs.writeFile(LQIP_TS, ts, "utf8")
console.log("CREDITS.md + src/lib/keyArt.ts written (" + lqipEntries.length + " entries)")
