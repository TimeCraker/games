import base64
import os

PROJECT_DIR = r"c:\Users\TimeCraker\Desktop\my_workspace\games\asternova"
GLB_PATH = os.path.join(PROJECT_DIR, r"art\models\weapons\aster_katana\aster_katana.glb")
HTML_OUT = os.path.join(PROJECT_DIR, r"art\models\weapons\aster_katana\aster_katana_3d_viewer.html")

with open(GLB_PATH, "rb") as f:
    glb_base64 = base64.b64encode(f.read()).decode("utf-8")

html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>星霜月华 · 360° 实时 3D 佩刀检视器 | Aster Katana 3D Inspector</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      user-select: none;
    }}
    body {{
      width: 100vw;
      height: 100vh;
      overflow: hidden;
      background: radial-gradient(circle at center, #161b2a 0%, #0d1017 60%, #07090e 100%);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
      color: #e8ecf4;
    }}
    #webgl-canvas {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1;
    }}
    /* Top Left Header */
    .hud-header {{
      position: absolute;
      top: 24px;
      left: 28px;
      z-index: 10;
      background: rgba(15, 20, 32, 0.75);
      border: 1px solid rgba(80, 140, 220, 0.35);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-radius: 12px;
      padding: 16px 22px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
      pointer-events: auto;
    }}
    .hud-title {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 1px;
      background: linear-gradient(135deg, #ffffff 20%, #90d4ff 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .hud-subtitle {{
      font-size: 12px;
      color: #7b93b8;
      margin-top: 4px;
      letter-spacing: 0.5px;
    }}
    .hud-stats {{
      margin-top: 10px;
      display: flex;
      gap: 12px;
      font-size: 12px;
      color: #a0c2eb;
      border-top: 1px solid rgba(255, 255, 255, 0.08);
      padding-top: 8px;
    }}
    .hud-tag {{
      background: rgba(40, 75, 125, 0.4);
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid rgba(90, 160, 255, 0.25);
    }}
    /* Top Right Controls */
    .hud-controls {{
      position: absolute;
      top: 24px;
      right: 28px;
      z-index: 10;
      background: rgba(15, 20, 32, 0.75);
      border: 1px solid rgba(80, 140, 220, 0.35);
      backdrop-filter: blur(12px);
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      width: 260px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
      pointer-events: auto;
    }}
    .btn {{
      background: linear-gradient(180deg, rgba(35, 55, 90, 0.85) 0%, rgba(20, 35, 60, 0.85) 100%);
      border: 1px solid rgba(90, 150, 235, 0.45);
      color: #e2eeff;
      padding: 9px 14px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      transition: all 0.2s ease;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    .btn:hover {{
      background: linear-gradient(180deg, rgba(50, 80, 130, 0.95) 0%, rgba(30, 50, 85, 0.95) 100%);
      border-color: rgba(130, 195, 255, 0.8);
      box-shadow: 0 0 14px rgba(70, 160, 255, 0.4);
      transform: translateY(-1px);
    }}
    .btn:active {{
      transform: translateY(1px);
    }}
    .btn.active {{
      background: linear-gradient(180deg, #1f508a 0%, #153860 100%);
      border-color: #64b5f6;
      box-shadow: inset 0 2px 4px rgba(0,0,0,0.3), 0 0 12px rgba(100, 181, 246, 0.5);
    }}
    .section-label {{
      font-size: 11px;
      color: #7995bc;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-top: 4px;
      margin-bottom: 2px;
    }}
    .preset-grid {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 5px;
    }}
    .btn-preset {{
      padding: 6px 2px;
      font-size: 11px;
      border-radius: 6px;
    }}
    /* Bottom Help Bar */
    .hud-bottom {{
      position: absolute;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 10;
      background: rgba(15, 20, 32, 0.75);
      border: 1px solid rgba(80, 140, 220, 0.35);
      backdrop-filter: blur(12px);
      border-radius: 30px;
      padding: 8px 24px;
      font-size: 12px;
      color: #b0cbe8;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
      display: flex;
      gap: 16px;
      pointer-events: none;
    }}
    .hud-bottom span {{
      color: #ffffff;
      font-weight: 600;
    }}
    /* Loading overlay */
    #loading {{
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: #0d1017;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 100;
      transition: opacity 0.5s ease;
    }}
    .spinner {{
      width: 50px;
      height: 50px;
      border: 3px solid rgba(80, 150, 255, 0.2);
      border-top-color: #60a5fa;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }}
    @keyframes spin {{
      to {{ transform: rotate(360deg); }}
    }}
  </style>
  <script type="importmap">
    {{
      "imports": {{
        "three": "https://cdnjs.cloudflare.com/ajax/libs/three.js/0.160.0/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
      }}
    }}
  </script>
</head>
<body>
  <div id="loading">
    <div class="spinner"></div>
    <p style="margin-top: 16px; color: #8ab4f8; font-size: 14px; letter-spacing: 1px;">正在加载「星霜月华」3D 资产...</p>
  </div>

  <canvas id="webgl-canvas"></canvas>

  <div class="hud-header">
    <div class="hud-title">✦ 星霜月华 ✦</div>
    <div class="hud-subtitle">Aster's Signature Katana · 360° Real-time 3D Inspector</div>
    <div class="hud-stats">
      <div class="hud-tag">📐 899 三角面</div>
      <div class="hud-tag">🎨 2048x2048 Atlas</div>
      <div class="hud-tag">⚔️ 拔刀分件装配</div>
      <div class="hud-tag">⚡ 120 FPS</div>
    </div>
  </div>

  <div class="hud-controls">
    <button class="btn" id="btn-draw">
      <span>⚔️</span>
      <span id="txt-draw">拔刀出鞘 (Space)</span>
    </button>
    <button class="btn active" id="btn-auto-rotate">
      <span>🔄</span>
      <span id="txt-rotate">自动旋转: 开 (R)</span>
    </button>
    <button class="btn" id="btn-wireframe">
      <span>🕸️</span>
      <span>线框拓扑模式 (W)</span>
    </button>
    
    <div class="section-label">特写视角切换 [1 - 5]</div>
    <div class="preset-grid">
      <button class="btn btn-preset" id="p1">1 全景</button>
      <button class="btn btn-preset" id="p2">2 护手</button>
      <button class="btn btn-preset" id="p3">3 刀尖</button>
      <button class="btn btn-preset" id="p4">4 刀柄</button>
      <button class="btn btn-preset" id="p5">5 系绪</button>
    </div>

    <button class="btn" id="btn-reset" style="margin-top: 4px;">
      <span>🎯</span>
      <span>重置视角 (C)</span>
    </button>
  </div>

  <div class="hud-bottom">
    <div><span>🖱️ 左键:</span> 360°环绕</div>
    <div><span>滚轮:</span> 缩放</div>
    <div><span>右键:</span> 平移视野</div>
    <div><span>空格:</span> 拔刀/入鞘</div>
    <div><span>W:</span> 线框</div>
    <div><span>R:</span> 自动旋转</div>
    <div><span>1~5:</span> 特写</div>
    <div><span>C:</span> 重置</div>
  </div>

  <script type="module">
    import * as THREE from 'three';
    import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
    import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';

    // 1. Scene, Camera, Renderer
    const canvas = document.getElementById('webgl-canvas');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0c0f18);
    scene.fog = new THREE.FogExp2(0x0c0f18, 0.35);

    const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.05, 50);
    camera.position.set(0.95, 0.45, 1.15);

    const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true, powerPreference: "high-performance" }});
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // 2. Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.target.set(0, 0, -0.12);
    controls.minDistance = 0.22;
    controls.maxDistance = 3.5;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 1.5;

    // 3. Lighting Setup (NPR 3-Point Cel Lighting)
    const ambientLight = new THREE.AmbientLight(0xd5e2f5, 0.65);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xfff5e6, 1.35);
    keyLight.position.set(2.5, 4.0, 3.0);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 2048;
    keyLight.shadow.mapSize.height = 2048;
    keyLight.shadow.camera.near = 0.5;
    keyLight.shadow.camera.far = 10;
    keyLight.shadow.bias = -0.0005;
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x80caff, 1.2);
    rimLight.position.set(-3.0, 2.5, -3.5);
    scene.add(rimLight);

    const fillLight = new THREE.DirectionalLight(0xedd4ff, 0.45);
    fillLight.position.set(2.0, -1.5, -2.0);
    scene.add(fillLight);

    // 4. Showcase Pedestal & Floor Ring
    const pedestalGeo = new THREE.CylinderGeometry(0.72, 0.78, 0.03, 64);
    const pedestalMat = new THREE.MeshStandardMaterial({{
      color: 0x121724,
      metalness: 0.8,
      roughness: 0.25,
    }});
    const pedestal = new THREE.Mesh(pedestalGeo, pedestalMat);
    pedestal.position.set(0, -0.38, -0.12);
    pedestal.receiveShadow = true;
    scene.add(pedestal);

    const ringGeo = new THREE.TorusGeometry(0.75, 0.006, 16, 64);
    const ringMat = new THREE.MeshBasicMaterial({{
      color: 0x60b8ff,
    }});
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2;
    ring.position.set(0, -0.365, -0.12);
    scene.add(ring);

    // Subtle Floating Star Dust
    const particleCount = 75;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    for(let i = 0; i < particleCount * 3; i += 3) {{
      particlePos[i] = (Math.random() - 0.5) * 2.2;
      particlePos[i+1] = Math.random() * 1.5 - 0.3;
      particlePos[i+2] = (Math.random() - 0.5) * 2.2;
    }}
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));
    const particleMat = new THREE.PointsMaterial({{
      color: 0x98d4ff,
      size: 0.016,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    }});
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 5. Load Embedded Katana GLB
    const glbBase64 = "{glb_base64}";
    const binaryString = atob(glbBase64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {{
      bytes[i] = binaryString.charCodeAt(i);
    }}

    let bladeMesh = null;
    let scabbardMesh = null;
    let isDrawn = false;
    let isWireframe = false;

    const loader = new GLTFLoader();
    loader.parse(bytes.buffer, '', (gltf) => {{
      const katanaGroup = gltf.scene;
      katanaGroup.rotation.y = THREE.MathUtils.degToRad(-15);
      katanaGroup.rotation.x = THREE.MathUtils.degToRad(5);
      
      katanaGroup.traverse((child) => {{
        if (child.isMesh) {{
          child.castShadow = true;
          child.receiveShadow = true;
          if (child.name.includes("Blade")) {{
            bladeMesh = child;
          }} else if (child.name.includes("Scabbard")) {{
            scabbardMesh = child;
          }}
        }}
      }});

      scene.add(katanaGroup);
      document.getElementById('loading').style.opacity = '0';
      setTimeout(() => document.getElementById('loading').style.display = 'none', 500);
    }});

    // 6. Camera Animation Tween Helper
    let camTargetPos = new THREE.Vector3(0.95, 0.45, 1.15);
    let camTargetLook = new THREE.Vector3(0, 0, -0.12);
    let isCamAnimating = false;
    let camAnimProgress = 0;
    let camStartPos = new THREE.Vector3();
    let camStartLook = new THREE.Vector3();

    function tweenCameraTo(targetEye, targetLookAt) {{
      camStartPos.copy(camera.position);
      camStartLook.copy(controls.target);
      camTargetPos.copy(targetEye);
      camTargetLook.copy(targetLookAt);
      camAnimProgress = 0;
      isCamAnimating = true;
    }}

    // 7. Blade Draw Animation Helper
    let bladeAnimProgress = 1.0;
    let bladeStartPos = new THREE.Vector3();
    let bladeTargetPos = new THREE.Vector3();
    let isBladeAnimating = false;

    function toggleBlade() {{
      if (!bladeMesh) return;
      isDrawn = !isDrawn;
      document.getElementById('txt-draw').innerText = isDrawn ? "收刀入鞘 (Space)" : "拔刀出鞘 (Space)";
      document.getElementById('btn-draw').classList.toggle('active', isDrawn);
      
      bladeStartPos.copy(bladeMesh.position);
      if (isDrawn) {{
        // Slide out along +Z by 0.74m and offset slightly in +X
        bladeTargetPos.set(0.06, 0.02, 0.74);
      }} else {{
        bladeTargetPos.set(0, 0, 0);
      }}
      bladeAnimProgress = 0;
      isBladeAnimating = true;
    }}

    function toggleAutoRotate() {{
      controls.autoRotate = !controls.autoRotate;
      document.getElementById('txt-rotate').innerText = controls.autoRotate ? "自动旋转: 开 (R)" : "自动旋转: 关 (R)";
      document.getElementById('btn-auto-rotate').classList.toggle('active', controls.autoRotate);
    }}

    function toggleWireframe() {{
      if (!bladeMesh || !scabbardMesh) return;
      isWireframe = !isWireframe;
      document.getElementById('btn-wireframe').classList.toggle('active', isWireframe);
      
      [bladeMesh, scabbardMesh].forEach(mesh => {{
        if (Array.isArray(mesh.material)) {{
          mesh.material.forEach(m => m.wireframe = isWireframe);
        }} else if (mesh.material) {{
          mesh.material.wireframe = isWireframe;
        }}
      }});
    }}

    function setPreset(idx) {{
      switch(idx) {{
        case 1: // Full
          tweenCameraTo(new THREE.Vector3(0.95, 0.45, 1.15), new THREE.Vector3(0, 0, -0.12));
          break;
        case 2: // Tsuba (Star Guard)
          tweenCameraTo(new THREE.Vector3(0.25, 0.18, 0.28), new THREE.Vector3(0, 0, 0));
          break;
        case 3: // Kissaki (Blade tip)
          if (isDrawn) {{
            tweenCameraTo(new THREE.Vector3(0.35, 0.15, 0.32), new THREE.Vector3(0.06, 0.02, 0.05));
          }} else {{
            tweenCameraTo(new THREE.Vector3(0.28, 0.12, -0.42), new THREE.Vector3(0, 0, -0.68));
          }}
          break;
        case 4: // Tsuka & Tassel
          if (isDrawn) {{
            tweenCameraTo(new THREE.Vector3(0.32, 0.15, 1.18), new THREE.Vector3(0.06, 0.02, 0.96));
          }} else {{
            tweenCameraTo(new THREE.Vector3(0.28, 0.12, 0.45), new THREE.Vector3(0, 0, 0.22));
          }}
          break;
        case 5: // Sageo ribbon bow
          tweenCameraTo(new THREE.Vector3(0.28, 0.14, 0.18), new THREE.Vector3(0, 0, -0.08));
          break;
      }}
    }}

    // 8. Event Listeners
    document.getElementById('btn-draw').addEventListener('click', toggleBlade);
    document.getElementById('btn-auto-rotate').addEventListener('click', toggleAutoRotate);
    document.getElementById('btn-wireframe').addEventListener('click', toggleWireframe);
    document.getElementById('btn-reset').addEventListener('click', () => setPreset(1));

    document.getElementById('p1').addEventListener('click', () => setPreset(1));
    document.getElementById('p2').addEventListener('click', () => setPreset(2));
    document.getElementById('p3').addEventListener('click', () => setPreset(3));
    document.getElementById('p4').addEventListener('click', () => setPreset(4));
    document.getElementById('p5').addEventListener('click', () => setPreset(5));

    window.addEventListener('keydown', (e) => {{
      if (e.code === 'Space') {{
        e.preventDefault();
        toggleBlade();
      }} else if (e.code === 'KeyR') {{
        toggleAutoRotate();
      }} else if (e.code === 'KeyW') {{
        toggleWireframe();
      }} else if (e.code === 'KeyC') {{
        setPreset(1);
      }} else if (e.code === 'Digit1') {{
        setPreset(1);
      }} else if (e.code === 'Digit2') {{
        setPreset(2);
      }} else if (e.code === 'Digit3') {{
        setPreset(3);
      }} else if (e.code === 'Digit4') {{
        setPreset(4);
      }} else if (e.code === 'Digit5') {{
        setPreset(5);
      }}
    }});

    window.addEventListener('resize', () => {{
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    }});

    // 9. Main Render Loop
    const clock = new THREE.Clock();
    function animate() {{
      requestAnimationFrame(animate);
      const delta = clock.getDelta();

      // Blade drawing smooth ease-out
      if (isBladeAnimating) {{
        bladeAnimProgress += delta * 2.2;
        if (bladeAnimProgress >= 1.0) {{
          bladeAnimProgress = 1.0;
          isBladeAnimating = false;
        }}
        const t = 1 - Math.pow(1 - bladeAnimProgress, 3); // ease-out cubic
        bladeMesh.position.lerpVectors(bladeStartPos, bladeTargetPos, t);
      }}

      // Camera smooth interpolation
      if (isCamAnimating) {{
        camAnimProgress += delta * 2.5;
        if (camAnimProgress >= 1.0) {{
          camAnimProgress = 1.0;
          isCamAnimating = false;
        }}
        const t = 1 - Math.pow(1 - camAnimProgress, 3);
        camera.position.lerpVectors(camStartPos, camTargetPos, t);
        controls.target.lerpVectors(camStartLook, camTargetLook, t);
      }}

      // Floating dust particles
      const positions = particleGeo.attributes.position.array;
      for (let i = 1; i < positions.length; i += 3) {{
        positions[i] += delta * 0.05;
        if (positions[i] > 1.2) positions[i] = -0.3;
      }}
      particleGeo.attributes.position.needsUpdate = true;

      controls.update();
      renderer.render(scene, camera);
    }}
    animate();
  </script>
</body>
</html>
'''

with open(HTML_OUT, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"Generated standalone 3D Web Viewer at: {HTML_OUT}")
print(f"File size: {os.path.getsize(HTML_OUT) / 1024:.1f} KB")
