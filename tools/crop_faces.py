# -*- coding: utf-8 -*-
"""
智能人脸裁剪：检测人脸 -> 以脸为中心裁正方形 -> 统一输出 512x512
用于消消乐方块素材。统一用 PIL 读图（兼容中文路径）。
"""
import os, glob
import cv2
import numpy as np
from PIL import Image

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "assets", "faces", "raw")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "assets", "faces")
OUT_SIZE = 512

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def read_bgr(path):
    im = Image.open(path).convert("RGB")
    arr = np.array(im)
    return arr[:, :, ::-1].copy()  # RGB->BGR

def detect_face(img_bgr):
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40))
    if len(faces) == 0:
        return None
    faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
    fx, fy, fw, fh = faces[0]
    # 误检保护：脸占比过大（>短边55%）视为异常，降级
    if fw > w * 0.55 or fh > h * 0.55:
        return ("SUSPECT", (fx, fy, fw, fh))
    return (fx, fy, fw, fh)

def crop_to_face(img_bgr, face):
    h, w = img_bgr.shape[:2]
    short = min(h, w)
    if face is not None and face != "SUSPECT":
        fx, fy, fw, fh = face
        cx = fx + fw // 2
        cy = fy + fh // 2
        side = int(max(fw, fh) * 2.6)
        side = min(side, short)  # 不超过短边，避免 pad
        # 肖像构图：脸偏上 -> 裁剪中心略下移
        crop_cy = int(cy + side * 0.12)
        crop_cx = cx
    else:
        side = short
        crop_cx = w // 2
        crop_cy = h // 2
    half = side // 2
    x0 = crop_cx - half
    y0 = crop_cy - half
    x1 = x0 + side
    y1 = y0 + side
    # 平移进界
    if x0 < 0: x0, x1 = 0, side
    if y0 < 0: y0, y1 = 0, side
    if x1 > w: x0, x1 = w - side, w
    if y1 > h: y0, y1 = h - side, h
    crop = img_bgr[y0:y1, x0:x1]
    return crop

def process_one(path, idx):
    img = read_bgr(path)
    h, w = img.shape[:2]
    res = detect_face(img)
    name = os.path.basename(path)
    face = None
    if res is None:
        print(f"[{idx}] {name}  {w}x{h}  NO FACE -> center crop")
    elif res == "SUSPECT":
        print(f"[{idx}] {name}  {w}x{h}  FACE too large(误检?) -> center crop")
    else:
        face = res
        print(f"[{idx}] {name}  {w}x{h}  FACE x={face[0]} y={face[1]} w={face[2]} h={face[3]}")
    crop = crop_to_face(img, face if face else None)
    crop = cv2.resize(crop, (OUT_SIZE, OUT_SIZE), interpolation=cv2.INTER_AREA)
    out = os.path.join(OUT_DIR, f"face{idx}.jpg")
    cv2.imwrite(out, crop, [cv2.IMWRITE_JPEG_QUALITY, 88])
    # 另存一份带人脸框的调试缩略图
    dbg = img.copy()
    if face:
        cv2.rectangle(dbg, (face[0], face[1]), (face[0]+face[2], face[1]+face[3]), (0,255,0), 4)
    dbg = cv2.resize(dbg, (480, int(480*h/w)))
    cv2.imwrite(os.path.join(OUT_DIR, f"_dbg{idx}.jpg"), dbg)
    print(f"    -> face{idx}.jpg  +  _dbg{idx}.jpg")
    return out

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*")))
    files = [f for f in files if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
    print(f"found {len(files)} raw images")
    for i, f in enumerate(files):
        process_one(f, i)
    print("DONE")

if __name__ == "__main__":
    main()
