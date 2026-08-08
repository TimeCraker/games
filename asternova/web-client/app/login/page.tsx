"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import { AnimatePresence, motion } from "framer-motion"
import { ArrowRight, KeyRound, Mail, Sparkles } from "lucide-react"

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"

import { getApiErrorMessage, guestLogin, login, loginWithEmail, register, resetPasswordWithEmail, sendCode } from "@/src/api/auth"
import { extractUserIdFromToken } from "@/src/api/jwt"
import { useGameStore } from "@/src/store/useGameStore"
import { BluePurpleBlackhole } from "@/src/components/bluePurpleBlackhole"

const cinematicEase = [0.22, 1, 0.36, 1] as const

const loginUiFont =
  'system-ui, -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", sans-serif'

const fieldClass =
  "h-11 rounded-xl border-white/[0.11] bg-black/45 text-[15px] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] transition-[border-color,box-shadow] placeholder:text-white/32 focus-visible:border-white/22 focus-visible:ring-2 focus-visible:ring-violet-400/25"

const labelClass = "text-[11px] font-semibold uppercase tracking-[0.2em] text-white/42"

export default function LoginPage() {
  const router = useRouter()

  const setToken = useGameStore((s) => s.setToken)
  const setUserId = useGameStore((s) => s.setUserId)
  const setUsername = useGameStore((s) => s.setUsername)

  const [activeTab, setActiveTab] = React.useState<"password_login" | "email_login">("password_login")

  const [identifier, setIdentifier] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [passwordSubmitting, setPasswordSubmitting] = React.useState(false)

  const [email, setEmail] = React.useState("")
  const [code, setCode] = React.useState("")
  const [setupRequired, setSetupRequired] = React.useState(false)
  const [setupUsername, setSetupUsername] = React.useState("")
  const [setupPassword, setSetupPassword] = React.useState("")
  const [codeSending, setCodeSending] = React.useState(false)
  const [emailSubmitting, setEmailSubmitting] = React.useState(false)
  const [resetOpen, setResetOpen] = React.useState(false)
  const [resetEmail, setResetEmail] = React.useState("")
  const [resetCode, setResetCode] = React.useState("")
  const [resetPassword, setResetPassword] = React.useState("")
  const [resetPasswordConfirm, setResetPasswordConfirm] = React.useState("")
  const [resetCodeSending, setResetCodeSending] = React.useState(false)
  const [resetSubmitting, setResetSubmitting] = React.useState(false)
  const [guestInviteCode, setGuestInviteCode] = React.useState("")
  const [guestSubmitting, setGuestSubmitting] = React.useState(false)

  function goToEmailRegister() {
    setActiveTab("email_login")
    window.setTimeout(() => {
      document.getElementById("email-login-email")?.focus()
    }, 80)
  }

  function validateSetupPassword(pwd: string): string | null {
    if (!pwd) {
      return "密码不能为空"
    }
    const re = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,20}$/
    if (!re.test(pwd)) {
      return "密码需为 6-20 位字母+数字组合"
    }
    return null
  }

  async function onSubmitPasswordLogin(e: React.FormEvent) {
    e.preventDefault()
    if (!identifier || !password) {
      toast.error("请输入用户名/邮箱和密码")
      return
    }

    setPasswordSubmitting(true)
    try {
      const res = await login(identifier, password)
      const userId = extractUserIdFromToken(res.token)

      setToken(res.token)
      setUserId(userId)
      setUsername(res.user?.username || identifier)

      toast.success("登录成功")
      router.push("/lobby")
    } catch (err) {
      toast.error(getApiErrorMessage(err))
    } finally {
      setPasswordSubmitting(false)
    }
  }

  async function onSendCode() {
    if (!email) {
      toast.error("请先填写邮箱")
      return
    }
    setCodeSending(true)
    try {
      const res = await sendCode(email)
      toast.success(res.message || "验证码已发送")
    } catch (err) {
      toast.error(getApiErrorMessage(err))
    } finally {
      setCodeSending(false)
    }
  }

  async function onSubmitEmailFlow(e: React.FormEvent) {
    e.preventDefault()

    if (!email || !code) {
      toast.error("请先填写邮箱和验证码")
      return
    }

    setEmailSubmitting(true)
    try {
      if (!setupRequired) {
        const res = await loginWithEmail(email, code)
        if ("token" in res) {
          const userId = extractUserIdFromToken(res.token)
          setToken(res.token)
          setUserId(userId)
          setUsername(res.user?.username || "")
          toast.success("登录成功")
          router.push("/lobby")
          return
        }
        if (res.action === "require_setup") {
          setSetupRequired(true)
          toast.success(res.message || "邮箱验证成功，请设置用户名和密码")
          return
        }
      }

      if (!setupUsername || !setupPassword) {
        toast.error("请设置用户名和密码")
        return
      }

      if (setupUsername.length > 10) {
        toast.error("用户名长度不能超过 10 位")
        return
      }

      const setupPasswordErr = validateSetupPassword(setupPassword)
      if (setupPasswordErr) {
        toast.error(setupPasswordErr)
        return
      }

      const regRes = await register(setupUsername, setupPassword, email, code)
      const userId = extractUserIdFromToken(regRes.token)
      setToken(regRes.token)
      setUserId(userId)
      setUsername(regRes.user.username)
      toast.success(regRes.message || "注册并登录成功")
      router.push("/lobby")
    } catch (err) {
      toast.error(getApiErrorMessage(err))
    } finally {
      setEmailSubmitting(false)
    }
  }

  async function onSendResetCode() {
    if (!resetEmail) {
      toast.error("请先填写邮箱")
      return
    }
    setResetCodeSending(true)
    try {
      const res = await sendCode(resetEmail)
      toast.success(res.message || "验证码已发送")
    } catch (err) {
      toast.error(getApiErrorMessage(err))
    } finally {
      setResetCodeSending(false)
    }
  }

  async function onSubmitResetPassword(e: React.FormEvent) {
    e.preventDefault()
    if (!resetEmail || !resetCode || !resetPassword || !resetPasswordConfirm) {
      toast.error("请完整填写重置信息")
      return
    }
    const pwdErr = validateSetupPassword(resetPassword)
    if (pwdErr) {
      toast.error(pwdErr)
      return
    }
    if (resetPassword !== resetPasswordConfirm) {
      toast.error("两次密码输入不一致")
      return
    }

    setResetSubmitting(true)
    try {
      const res = await resetPasswordWithEmail(resetEmail, resetCode, resetPassword, resetPasswordConfirm)
      setIdentifier(res.identifier || resetEmail)
      setPassword("")
      setActiveTab("password_login")
      setResetOpen(false)
      setResetCode("")
      setResetPassword("")
      setResetPasswordConfirm("")
      toast.success(res.message || "密码重置成功，请重新登录")
    } catch (err) {
      toast.error(getApiErrorMessage(err))
    } finally {
      setResetSubmitting(false)
    }
  }

  async function onSubmitGuestLogin(e: React.FormEvent) {
    e.preventDefault()
    if (!guestInviteCode.trim()) {
      toast.error("请输入邀请码")
      return
    }
    setGuestSubmitting(true)
    try {
      const res = await guestLogin(guestInviteCode.trim())
      const userId = extractUserIdFromToken(res.token)
      setToken(res.token)
      setUserId(userId)
      setUsername(res.user?.username || "Guest")
      toast.success(res.message || "游客登录成功")
      router.push("/lobby")
    } catch (err) {
      toast.error(getApiErrorMessage(err))
    } finally {
      setGuestSubmitting(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-transparent">
      {/* ===== 新增代码 START ===== */}
      <motion.div
        className="pointer-events-none absolute inset-0 z-0 bg-black"
        initial={{ opacity: 1 }}
        animate={{ opacity: 0 }}
        transition={{ duration: 0.38, ease: cinematicEase }}
      />

      <motion.div
        className="pointer-events-none absolute inset-0 -translate-x-[1.5%]"
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.1, delay: 0.12, ease: cinematicEase }}
      >
        <BluePurpleBlackhole className="pointer-events-none absolute inset-0 opacity-30" intensity={0.8} interactive={false} />
      </motion.div>

      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/2 z-[1] h-[56vmin] w-[56vmin] -translate-x-1/2 -translate-y-1/2 rounded-full"
        initial={{ opacity: 0, scale: 0.96, rotate: -8 }}
        animate={{ opacity: 1, scale: 1, rotate: 0 }}
        transition={{ duration: 1.15, delay: 0.22, ease: cinematicEase }}
      >
        <motion.div
          className="absolute inset-0 rounded-full border border-violet-300/35"
          style={{
            background:
              "conic-gradient(from 210deg, rgba(255,182,193,0.0), rgba(255,182,193,0.5), rgba(168,85,247,0.45), rgba(96,165,250,0.0))",
            maskImage: "radial-gradient(circle, transparent 64%, black 72%, transparent 78%)",
            WebkitMaskImage: "radial-gradient(circle, transparent 64%, black 72%, transparent 78%)",
            filter: "blur(1.4px)",
          }}
          initial={{ opacity: 0.15, rotate: -42 }}
          animate={{ opacity: 0.72, rotate: 0 }}
          transition={{ duration: 1.25, delay: 0.3, ease: cinematicEase }}
        />
      </motion.div>
      {/* ===== 新增代码 END ===== */}

      <div className="pointer-events-none absolute inset-0 opacity-70">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.18),transparent_45%),radial-gradient(circle_at_80%_30%,rgba(168,85,247,0.18),transparent_50%),radial-gradient(circle_at_40%_80%,rgba(34,197,94,0.10),transparent_45%)]" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/70 to-black" />
      </div>

      <motion.div
        className="relative z-10 w-full max-w-[420px] px-5 sm:px-6"
        style={{ fontFamily: loginUiFont }}
        initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
        transition={{ duration: 0.9, delay: 0.9, ease: cinematicEase }}
      >
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, delay: 1, ease: cinematicEase }}
          className="relative overflow-hidden rounded-[1.35rem] border border-white/[0.09] bg-[#070708]/[0.78] text-white shadow-[0_0_0_1px_rgba(255,255,255,0.04)_inset,0_24px_80px_rgba(0,0,0,0.55),0_0_100px_rgba(139,92,246,0.08)] backdrop-blur-2xl supports-[backdrop-filter]:bg-[#070708]/[0.62]"
        >
          <div
            className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/35 to-transparent opacity-80"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute -right-24 -top-24 h-48 w-48 rounded-full bg-violet-500/[0.12] blur-3xl"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute -bottom-28 -left-20 h-52 w-52 rounded-full bg-cyan-400/[0.08] blur-3xl"
            aria-hidden
          />

          <div className="relative px-6 pb-7 pt-7 sm:px-8 sm:pb-8 sm:pt-8">
            <header className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <Link
                  href="/"
                  className="group/brand inline-flex items-center rounded-md outline-none ring-offset-2 ring-offset-[#070708] focus-visible:ring-2 focus-visible:ring-white/35"
                  aria-label="返回首页"
                >
                  <span className="bg-gradient-to-r from-pink-200 via-fuchsia-200 to-sky-300 bg-clip-text text-[0.65rem] font-semibold uppercase tracking-[0.28em] text-transparent transition-opacity group-hover/brand:opacity-85 sm:text-[11px]">
                    AsterNova Studio
                  </span>
                </Link>
                <span className="rounded-full border border-white/[0.1] bg-white/[0.05] px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-white/55">
                  Secure access
                </span>
              </div>
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.65, delay: 1.08, ease: cinematicEase }}
                className="space-y-2"
              >
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white/[0.07] ring-1 ring-white/[0.1]">
                    <Sparkles className="h-[1.05rem] w-[1.05rem] text-white/88" strokeWidth={1.5} />
                  </div>
                  <h1 className="text-[1.35rem] font-semibold tracking-[-0.03em] text-white/95 sm:text-[1.45rem]">
                    AsterNova Access
                  </h1>
                </div>
                <p className="text-[13px] leading-relaxed text-white/52">
                  Reach Beyond the Stars. 登录已有账号；新用户请走邮箱验证，按提示完成注册。
                </p>
              </motion.div>
            </header>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 1.14, ease: cinematicEase }}
              className="mt-6 rounded-2xl border border-white/[0.08] bg-gradient-to-br from-white/[0.06] to-white/[0.02] p-[1px] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]"
            >
              <div className="flex items-center gap-3 rounded-[0.95rem] bg-black/32 px-3.5 py-2.5 sm:gap-4 sm:px-4 sm:py-3">
                <Mail className="hidden h-4 w-4 shrink-0 text-violet-300/75 sm:block" strokeWidth={2} aria-hidden />
                <p className="min-w-0 flex-1 text-[12px] leading-snug text-white/48 sm:text-[12.5px]">
                  <span className="font-medium text-white/78">新用户</span>
                  用邮箱验证码即可；未注册时会引导设置账号。
                </p>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={goToEmailRegister}
                  className="h-9 shrink-0 gap-1.5 rounded-xl border border-white/16 bg-white/[0.08] px-3.5 text-[12.5px] font-semibold text-white shadow-[0_0_20px_rgba(255,255,255,0.05)] transition hover:border-white/26 hover:bg-white/[0.12] sm:h-10 sm:min-w-[7.5rem] sm:px-4 sm:text-[13px]"
                >
                  邮箱注册
                  <ArrowRight className="h-3.5 w-3.5 opacity-90 sm:h-4 sm:w-4" strokeWidth={2.2} />
                </Button>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 1.18, ease: cinematicEase }}
              className="mt-3 rounded-2xl border border-white/[0.08] bg-gradient-to-br from-white/[0.045] to-white/[0.01] p-[1px] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"
            >
              <form
                onSubmit={onSubmitGuestLogin}
                className="flex items-center gap-2 rounded-[0.95rem] bg-black/30 px-3 py-2.5"
              >
                <span className="rounded-lg border border-white/10 bg-white/[0.06] px-2 py-1 text-[10px] font-semibold tracking-[0.08em] text-white/65">
                  游客
                </span>
                <Input
                  value={guestInviteCode}
                  onChange={(e) => setGuestInviteCode(e.target.value)}
                  className="h-9 border-white/[0.08] bg-black/35 text-[13px] text-white/90 placeholder:text-white/32 focus-visible:border-white/20 focus-visible:ring-1 focus-visible:ring-violet-400/20"
                  placeholder="输入邀请码"
                />
                <Button
                  type="submit"
                  disabled={guestSubmitting}
                  className="h-9 shrink-0 rounded-lg border border-white/14 bg-white/[0.1] px-3 text-[12px] font-semibold text-white hover:bg-white/[0.14]"
                >
                  {guestSubmitting ? "进入中…" : "游客进入"}
                </Button>
              </form>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 1.24, ease: cinematicEase }}
              className="mt-7"
            >
              <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "password_login" | "email_login")}>
                <TabsList className="grid h-auto w-full grid-cols-2 gap-1 rounded-2xl border border-white/[0.07] bg-black/40 p-1 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                  <TabsTrigger
                    value="password_login"
                    className="group/tab relative h-10 rounded-xl border border-transparent text-[13px] font-medium text-white/45 transition data-[state=active]:border-white/[0.12] data-[state=active]:bg-white/[0.12] data-[state=active]:text-white data-[state=active]:shadow-[0_0_20px_rgba(255,255,255,0.06)]"
                  >
                    <KeyRound
                      className="mr-1.5 h-3.5 w-3.5 opacity-55 transition group-data-[state=active]/tab:opacity-100"
                      strokeWidth={2}
                    />
                    账号密码
                  </TabsTrigger>
                  <TabsTrigger
                    value="email_login"
                    className="group/tab relative h-10 rounded-xl border border-transparent text-[13px] font-medium text-white/45 transition data-[state=active]:border-white/[0.12] data-[state=active]:bg-white/[0.12] data-[state=active]:text-white data-[state=active]:shadow-[0_0_20px_rgba(255,255,255,0.06)]"
                  >
                    <Mail
                      className="mr-1.5 h-3.5 w-3.5 opacity-55 transition group-data-[state=active]/tab:opacity-100"
                      strokeWidth={2}
                    />
                    邮箱验证码
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="password_login" className="mt-7 outline-none">
                  <form className="space-y-5" onSubmit={onSubmitPasswordLogin}>
                    <div className="space-y-2">
                      <Label htmlFor="login-identifier" className={labelClass}>
                        用户名 / 邮箱
                      </Label>
                      <Input
                        id="login-identifier"
                        value={identifier}
                        onChange={(e) => setIdentifier(e.target.value)}
                        autoComplete="username"
                        className={fieldClass}
                        placeholder="输入用户名或邮箱"
                      />
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={() => {
                          setResetEmail(identifier.includes("@") ? identifier : "")
                          setResetOpen(true)
                        }}
                        className="text-[12px] font-medium text-cyan-200/85 transition hover:text-cyan-100"
                      >
                        忘记密码？
                      </button>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="login-password" className={labelClass}>
                        密码
                      </Label>
                      <Input
                        id="login-password"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                        className={fieldClass}
                        placeholder="输入你的密码"
                      />
                    </div>

                    <Button
                      type="submit"
                      disabled={passwordSubmitting}
                      className="mt-1 h-12 w-full rounded-xl bg-gradient-to-r from-cyan-300/95 via-sky-300/95 to-cyan-200/90 text-[15px] font-semibold tracking-[-0.02em] text-black shadow-[0_0_32px_rgba(34,211,238,0.22),inset_0_1px_0_rgba(255,255,255,0.45)] transition hover:brightness-105 disabled:opacity-55"
                    >
                      {passwordSubmitting ? "登录中…" : "登录"}
                    </Button>
                  </form>
                </TabsContent>

                <TabsContent value="email_login" className="mt-7 outline-none">
                  <form className="space-y-5" onSubmit={onSubmitEmailFlow}>
                    <div className="space-y-2">
                      <Label htmlFor="email-login-email" className={labelClass}>
                        邮箱
                      </Label>
                      <Input
                        id="email-login-email"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                        disabled={setupRequired}
                        className={fieldClass}
                        placeholder="用于接收验证码"
                      />
                    </div>

                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-3">
                      <div className="space-y-2 sm:col-span-2">
                        <Label htmlFor="email-login-code" className={labelClass}>
                          验证码
                        </Label>
                        <Input
                          id="email-login-code"
                          value={code}
                          onChange={(e) => setCode(e.target.value)}
                          inputMode="numeric"
                          disabled={setupRequired}
                          className={fieldClass}
                          placeholder="6 位验证码"
                        />
                      </div>
                      <div className="flex items-end sm:col-span-1">
                        <Button
                          type="button"
                          variant="secondary"
                          className="h-11 w-full rounded-xl border border-white/14 bg-white/[0.08] text-[13px] font-medium text-white/90 hover:bg-white/[0.13]"
                          onClick={onSendCode}
                          disabled={codeSending || setupRequired}
                        >
                          {codeSending ? "发送中…" : "发送验证码"}
                        </Button>
                      </div>
                    </div>

                    {setupRequired && (
                      <>
                        <div className="space-y-2">
                          <Label htmlFor="setup-username" className={labelClass}>
                            设置用户名
                          </Label>
                          <Input
                            id="setup-username"
                            value={setupUsername}
                            onChange={(e) => setSetupUsername(e.target.value)}
                            autoComplete="username"
                            className={fieldClass}
                            placeholder="为自己起一个星际代号"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="setup-password" className={labelClass}>
                            设置密码
                          </Label>
                          <Input
                            id="setup-password"
                            type="password"
                            value={setupPassword}
                            onChange={(e) => setSetupPassword(e.target.value)}
                            autoComplete="new-password"
                            className={fieldClass}
                            placeholder="设置一个安全的密码"
                          />
                        </div>
                      </>
                    )}

                    <Button
                      type="submit"
                      disabled={emailSubmitting}
                      className="mt-1 h-12 w-full rounded-xl bg-gradient-to-r from-violet-400/95 via-fuchsia-400/90 to-violet-300/95 text-[15px] font-semibold tracking-[-0.02em] text-black shadow-[0_0_36px_rgba(167,139,250,0.28),inset_0_1px_0_rgba(255,255,255,0.4)] transition hover:brightness-105 disabled:opacity-55"
                    >
                      {emailSubmitting
                        ? "提交中…"
                        : setupRequired
                          ? "完成设置并进入游戏"
                          : "登录 / 注册"}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </motion.div>
          </div>
        </motion.div>
      </motion.div>

      <AnimatePresence>
        {resetOpen ? (
          <motion.div
            className="fixed inset-0 z-[120] flex items-end justify-center bg-black/60 p-3 backdrop-blur-md sm:items-center sm:p-5"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setResetOpen(false)}
          >
            <motion.div
              initial={{ opacity: 0, y: 18, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.98 }}
              transition={{ type: "spring", stiffness: 360, damping: 28 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-[430px] rounded-[1.5rem] border border-white/[0.12] bg-[#070708]/[0.9] p-5 shadow-[0_24px_80px_rgba(0,0,0,0.62)] backdrop-blur-2xl sm:p-6"
            >
              <h3 className="text-[1.15rem] font-semibold tracking-tight text-white">忘记密码</h3>
              <p className="mt-1 text-[12px] text-white/52">邮箱验证通过后即可重置密码</p>

              <form className="mt-5 space-y-4" onSubmit={onSubmitResetPassword}>
                <div className="space-y-2">
                  <Label htmlFor="reset-email" className={labelClass}>
                    邮箱
                  </Label>
                  <Input
                    id="reset-email"
                    type="email"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                    autoComplete="email"
                    className={fieldClass}
                    placeholder="输入注册邮箱"
                  />
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 sm:gap-3">
                  <div className="space-y-2 sm:col-span-2">
                    <Label htmlFor="reset-code" className={labelClass}>
                      验证码
                    </Label>
                    <Input
                      id="reset-code"
                      value={resetCode}
                      onChange={(e) => setResetCode(e.target.value)}
                      inputMode="numeric"
                      className={fieldClass}
                      placeholder="6 位验证码"
                    />
                  </div>
                  <div className="flex items-end sm:col-span-1">
                    <Button
                      type="button"
                      variant="secondary"
                      className="h-11 w-full rounded-xl border border-white/14 bg-white/[0.08] text-[13px] font-medium text-white/90 hover:bg-white/[0.13]"
                      onClick={onSendResetCode}
                      disabled={resetCodeSending}
                    >
                      {resetCodeSending ? "发送中…" : "发送验证码"}
                    </Button>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reset-password" className={labelClass}>
                    新密码
                  </Label>
                  <Input
                    id="reset-password"
                    type="password"
                    value={resetPassword}
                    onChange={(e) => setResetPassword(e.target.value)}
                    autoComplete="new-password"
                    className={fieldClass}
                    placeholder="输入新密码"
                  />
                  <p className="text-[11px] text-white/45">密码需 6-20 位，且包含字母和数字。</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="reset-password-confirm" className={labelClass}>
                    确认新密码
                  </Label>
                  <Input
                    id="reset-password-confirm"
                    type="password"
                    value={resetPasswordConfirm}
                    onChange={(e) => setResetPasswordConfirm(e.target.value)}
                    autoComplete="new-password"
                    className={fieldClass}
                    placeholder="再次输入新密码"
                  />
                </div>

                <div className="mt-2 flex gap-2.5">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setResetOpen(false)}
                    className="h-11 flex-1 rounded-xl border border-white/14 bg-white/[0.08] text-white/85 hover:bg-white/[0.13]"
                  >
                    取消
                  </Button>
                  <Button
                    type="submit"
                    disabled={resetSubmitting}
                    className="h-11 flex-1 rounded-xl bg-gradient-to-r from-cyan-300/95 via-sky-300/95 to-cyan-200/90 text-[14px] font-semibold text-black shadow-[0_0_28px_rgba(34,211,238,0.2)]"
                  >
                    {resetSubmitting ? "提交中…" : "确认修改"}
                  </Button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  )
}

