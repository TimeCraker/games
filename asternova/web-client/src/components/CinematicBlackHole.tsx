"use client"

import * as React from "react"
import * as THREE from "three"
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer"
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass"
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass"

export type CinematicBlackHoleProps = {
  className?: string
  intensity?: number
  opacity?: number
  interactive?: boolean
}

type ShaderUniforms = {
  u_time: { value: number }
  u_resolution: { value: THREE.Vector2 }
  u_viewDir: { value: THREE.Vector3 }
  u_intensity: { value: number }
}

export function CinematicBlackHole(props: CinematicBlackHoleProps) {
  const { className = "", intensity = 1, opacity = 1, interactive = true } = props

  const wrapRef = React.useRef<HTMLDivElement | null>(null)
  const rafRef = React.useRef<number | null>(null)

  const rendererRef = React.useRef<THREE.WebGLRenderer | null>(null)
  const sceneRef = React.useRef<THREE.Scene | null>(null)
  const cameraRef = React.useRef<THREE.PerspectiveCamera | null>(null)
  const composerRef = React.useRef<EffectComposer | null>(null)
  const uniformsRef = React.useRef<ShaderUniforms | null>(null)
  const orbitTargetRef = React.useRef({ x: 0, y: 0 })
  const orbitRef = React.useRef({ x: 0, y: 0 })

  React.useEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return

    let renderer: THREE.WebGLRenderer
    let geometry: THREE.PlaneGeometry
    let material: THREE.ShaderMaterial

    const width = Math.max(1, wrap.clientWidth)
    const height = Math.max(1, wrap.clientHeight)
    const pr = Math.min(2, window.devicePixelRatio || 1)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(58, width / height, 0.01, 10)
    camera.position.set(0, 0, 1)
    camera.rotation.set(-0.08, 0.0, 0.0)

    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    })
    renderer.setPixelRatio(pr)
    renderer.setSize(width, height, false)
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.0 * intensity

    const vertexShader = `
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`

    const fragmentShader = `
precision highp float;
varying vec2 vUv;
uniform float u_time;
uniform vec2 u_resolution;
uniform vec3 u_viewDir;
uniform float u_intensity;

float hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float noise2(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0, 0.0));
  float c = hash21(i + vec2(0.0, 1.0));
  float d = hash21(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
  for (int i = 0; i < 4; i++) {
    v += a * noise2(p);
    p = m * p;
    a *= 0.5;
  }
  return v;
}

vec3 starfield(vec2 uv) {
  vec2 p = uv * 95.0;
  vec2 id = floor(p);
  vec2 gv = fract(p) - 0.5;
  float rnd = hash21(id);
  float star = 0.0;
  if (rnd > 0.992) {
    float d = length(gv);
    star = smoothstep(0.08, 0.0, d);
    star *= (0.4 + 0.6 * hash21(id + 7.13));
  }

  float neb = fbm(uv * 3.5 + vec2(0.0, u_time * 0.01));
  vec3 bg = vec3(0.0025, 0.003, 0.008);
  bg += vec3(0.008, 0.012, 0.02) * neb * 0.12;
  bg += vec3(0.65, 0.72, 0.85) * star * 0.38;
  return bg;
}

void main() {
  vec2 res = max(u_resolution, vec2(1.0));
  float minDim = min(res.x, res.y);
  vec2 uv = (gl_FragCoord.xy - 0.5 * res) / minDim;

  float r = length(uv);
  float theta = atan(uv.y, uv.x);
  float eventHorizon = 0.16;

  // 引力透镜：越靠近黑洞扭曲越强
  vec2 dir = normalize(uv + vec2(1e-6));
  float lensStrength = 0.12 + 0.18 * u_intensity;
  float distortion = lensStrength / max(r * 8.0, 0.08);
  vec2 uvLensed = uv + dir * distortion;

  // 背景固定深空：不跟随鼠标
  vec3 bg = starfield(uvLensed);

  // 事件视界：完全黑体
  if (r < eventHorizon) {
    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    return;
  }

  // 吸积盘：极薄主环 + 内圈高亮
  vec2 diskUv = vec2(uvLensed.x, uvLensed.y * 3.9);
  float diskR = length(diskUv);
  float diskAngle = atan(diskUv.y, diskUv.x);

  float diskRadius = 0.34;
  float diskWidth = 0.008;
  float mainRing = exp(-abs(diskR - diskRadius) / diskWidth);
  mainRing *= smoothstep(eventHorizon * 1.04, diskRadius + 0.12, diskR);
  float innerRing = exp(-abs(diskR - (diskRadius - 0.022)) / 0.009);
  innerRing *= smoothstep(eventHorizon * 1.05, diskRadius + 0.04, diskR);

  // 高速旋转
  float spin = u_time * 0.26;
  float rotAngle = diskAngle + spin;

  // 多普勒：dot(viewDir, velocity) 亮度不对称
  vec2 tangent = vec2(-sin(rotAngle), cos(rotAngle));
  vec3 velocity = normalize(vec3(tangent, 0.0));
  vec3 viewDir = normalize(u_viewDir);
  float doppler = dot(viewDir, velocity); // [-1, 1]
  float approach = clamp(doppler * 0.5 + 0.5, 0.0, 1.0);
  float recede = 1.0 - approach;

  float bright = mix(0.2, 2.2, pow(approach, 2.35));
  bright *= mix(1.0, 0.48, pow(recede, 1.05));

  float innerHot = smoothstep(diskRadius + 0.016, diskRadius - 0.018, diskR);
  vec3 colBlue = vec3(0.18, 0.58, 1.0);
  vec3 colPurple = vec3(0.62, 0.18, 1.0);
  vec3 colWhite = vec3(0.98, 0.99, 1.0);
  vec3 diskBase = mix(colPurple, colBlue, 0.5 + 0.5 * sin(rotAngle * 3.0));
  vec3 diskColor = diskBase * bright;
  diskColor = mix(diskColor, colWhite * (1.2 + bright * 0.35), innerHot * approach);

  float streak = 0.9 + 0.1 * sin(rotAngle * 9.0 + u_time * 0.35);
  streak *= 0.92 + 0.08 * sin(rotAngle * 4.0 - u_time * 0.18);
  vec3 disk = diskColor * (mainRing * 0.95 + innerRing * 0.65) * streak;

  // 黑洞边缘环形光圈：更细、更精致的蓝紫波浪流动
  float edgeR = eventHorizon + 0.125;
  float edgeW = 0.011;
  float edgeRing = exp(-abs(r - edgeR) / edgeW);

  // 低频主波 + 高频细纹：无接缝角向映射 + 1.5x 速度
  vec2 nrm = normalize(uv + vec2(1e-6));
  float phaseA = dot(nrm, vec2(cos(u_time * 0.63), sin(u_time * 0.63)));
  float phaseB = dot(nrm, vec2(cos(-u_time * 0.42), sin(-u_time * 0.42)));
  float phaseC = dot(nrm, vec2(cos(u_time * 0.24), sin(u_time * 0.24)));
  float waveSlow = 0.5 + 0.5 * sin(phaseA * 3.2 + u_time * 0.11);
  float waveMid = 0.5 + 0.5 * sin(phaseB * 5.8 - u_time * 0.075);
  float waveFine = 0.5 + 0.5 * sin(phaseC * 14.0 + u_time * 0.04);
  float ripple = (0.76 + 0.24 * waveSlow) * (0.88 + 0.12 * waveMid);
  float thicknessWave = 0.975 + 0.025 * waveFine;
  edgeRing *= ripple * thicknessWave;

  vec3 edgePurple = vec3(0.62, 0.18, 1.0);
  vec3 edgeBlue = vec3(0.2, 0.64, 1.0);
  vec3 edgeWhiteBlue = vec3(0.9, 0.97, 1.0);
  float gradA = 0.5 + 0.5 * sin(dot(nrm, vec2(cos(u_time * 0.24), sin(u_time * 0.24))) * 1.8);
  float gradB = 0.5 + 0.5 * sin(dot(nrm, vec2(cos(-u_time * 0.2), sin(-u_time * 0.2))) * 2.8);
  vec3 edgeCol = mix(edgePurple, edgeBlue, gradA);
  edgeCol = mix(edgeCol, edgeWhiteBlue, 0.08 * gradB);
  vec3 edgeHalo = edgeCol * edgeRing * 0.98;

  // 靠近视界的吞噬暗晕
  float swallow = 1.0 - smoothstep(eventHorizon * 1.02, eventHorizon * 3.4, r);
  bg *= mix(0.82, 0.2, swallow);

  vec3 col = bg + disk + edgeHalo;
  float vignette = smoothstep(1.55, 0.35, length(uv));
  col *= 0.8 + 0.2 * vignette;

  gl_FragColor = vec4(col, 1.0);
}
`

    const uniforms: ShaderUniforms = {
      u_time: { value: 0 },
      u_resolution: { value: new THREE.Vector2(width * pr, height * pr) },
      u_viewDir: { value: new THREE.Vector3(0, 0, 1) },
      u_intensity: { value: intensity },
    }
    uniformsRef.current = uniforms

    geometry = new THREE.PlaneGeometry(2, 2)
    material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader,
      fragmentShader,
      depthTest: false,
      depthWrite: false,
    })
    const mesh = new THREE.Mesh(geometry, material)
    scene.add(mesh)

    const composer = new EffectComposer(renderer)
    composer.addPass(new RenderPass(scene, camera))
    composer.addPass(new UnrealBloomPass(new THREE.Vector2(width, height), 0.62, 0.34, 0.3))

    wrap.appendChild(renderer.domElement)
    renderer.domElement.className = "absolute inset-0 z-0 pointer-events-none"
    renderer.domElement.style.width = "100%"
    renderer.domElement.style.height = "100%"

    rendererRef.current = renderer
    sceneRef.current = scene
    cameraRef.current = camera
    composerRef.current = composer

    const onPointerMove = (ev: PointerEvent) => {
      if (!interactive) return
      const rect = wrap.getBoundingClientRect()
      const nx = (ev.clientX - rect.left) / Math.max(1, rect.width)
      const ny = (ev.clientY - rect.top) / Math.max(1, rect.height)
      orbitTargetRef.current.x = Math.max(-1, Math.min(1, (nx - 0.5) * 2.0))
      orbitTargetRef.current.y = Math.max(-1, Math.min(1, (ny - 0.5) * 2.0))
    }

    const onResize = () => {
      const w = Math.max(1, wrap.clientWidth)
      const h = Math.max(1, wrap.clientHeight)
      const p = Math.min(2, window.devicePixelRatio || 1)
      if (!rendererRef.current || !cameraRef.current || !composerRef.current || !uniformsRef.current) return
      rendererRef.current.setPixelRatio(p)
      rendererRef.current.setSize(w, h, false)
      cameraRef.current.aspect = w / h
      cameraRef.current.updateProjectionMatrix()
      composerRef.current.setSize(w, h)
      uniformsRef.current.u_resolution.value.set(w * p, h * p)
    }

    window.addEventListener("pointermove", onPointerMove, { passive: true })
    window.addEventListener("resize", onResize)

    const clock = new THREE.Clock()
    const viewDir = new THREE.Vector3(0, 0, 1)
    const tick = () => {
      const dt = clock.getDelta()
      const t = clock.elapsedTime

      orbitRef.current.x += (orbitTargetRef.current.x - orbitRef.current.x) * (1 - Math.exp(-dt * 8.0))
      orbitRef.current.y += (orbitTargetRef.current.y - orbitRef.current.y) * (1 - Math.exp(-dt * 8.0))

      const yaw = orbitRef.current.x * 0.1
      const pitch = orbitRef.current.y * 0.1 - 0.08
      camera.rotation.set(pitch, yaw, 0)
      camera.updateMatrixWorld()
      camera.getWorldDirection(viewDir)

      if (uniformsRef.current) {
        uniformsRef.current.u_time.value = t
        uniformsRef.current.u_viewDir.value.copy(viewDir)
        uniformsRef.current.u_intensity.value = intensity
      }

      composer.render()
      rafRef.current = window.requestAnimationFrame(tick)
    }

    rafRef.current = window.requestAnimationFrame(tick)

    return () => {
      window.removeEventListener("pointermove", onPointerMove)
      window.removeEventListener("resize", onResize)
      if (rafRef.current) window.cancelAnimationFrame(rafRef.current)
      rafRef.current = null

      try {
        material.dispose()
        geometry.dispose()
        renderer.dispose()
      } catch {
        // ignore
      }

      try {
        if (renderer.domElement.parentElement === wrap) wrap.removeChild(renderer.domElement)
      } catch {
        // ignore
      }

      composerRef.current = null
      rendererRef.current = null
      sceneRef.current = null
      cameraRef.current = null
      uniformsRef.current = null
    }
  }, [interactive, intensity])

  return (
    <div
      ref={wrapRef}
      className={`fixed inset-0 z-0 pointer-events-none w-screen h-screen bg-black ${className}`.trim()}
      style={{ opacity }}
    />
  )
}
