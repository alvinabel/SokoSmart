import { deflateSync } from 'node:zlib'
import { mkdirSync, writeFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT = join(__dirname, '..', 'frontend', 'public', 'icons')
mkdirSync(OUT, { recursive: true })

const RED = [244, 67, 94]
const WHITE = [255, 255, 255]
const GREEN = [76, 175, 80]
const TRANSPARENT = [0, 0, 0, 0]

const crcTable = (() => {
  const table = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    table[n] = c >>> 0
  }
  return table
})()

function crc32(buf) {
  let c = 0xffffffff
  for (let i = 0; i < buf.length; i++) c = crcTable[(c ^ buf[i]) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}

function chunk(type, data) {
  const length = Buffer.alloc(4)
  length.writeUInt32BE(data.length, 0)
  const typeBuf = Buffer.from(type, 'ascii')
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0)
  return Buffer.concat([length, typeBuf, data, crc])
}

function encodePNG(size, pixelFn) {
  const raw = Buffer.alloc(size * (1 + size * 4))
  for (let y = 0; y < size; y++) {
    const row = y * (1 + size * 4)
    raw[row] = 0
    for (let x = 0; x < size; x++) {
      const [r, g, b, a] = pixelFn(x, y)
      const off = row + 1 + x * 4
      raw[off] = r
      raw[off + 1] = g
      raw[off + 2] = b
      raw[off + 3] = a
    }
  }
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(size, 0)
  ihdr.writeUInt32BE(size, 4)
  ihdr[8] = 8
  ihdr[9] = 6
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ])
}

function distToSeg(px, py, ax, ay, bx, by) {
  const dx = bx - ax
  const dy = by - ay
  const lenSq = dx * dx + dy * dy
  let t = lenSq === 0 ? 0 : ((px - ax) * dx + (py - ay) * dy) / lenSq
  t = Math.max(0, Math.min(1, t))
  const cx = ax + t * dx
  const cy = ay + t * dy
  return Math.hypot(px - cx, py - cy)
}

function insideLeaf(nx, ny, cx, cy, angle) {
  const rad = (angle * Math.PI) / 180
  const dx = nx - cx
  const dy = ny - cy
  const xr = dx * Math.cos(rad) + dy * Math.sin(rad)
  const yr = -dx * Math.sin(rad) + dy * Math.cos(rad)
  const rx = 0.175
  const ry = 0.085
  return (xr * xr) / (rx * rx) + (yr * yr) / (ry * ry) <= 1
}

function insideGlyph(nx, ny) {
  const thickness = 0.115
  const dLeft = distToSeg(nx, ny, 0.3, 0.74, 0.465, 0.26)
  const dRight = distToSeg(nx, ny, 0.535, 0.26, 0.7, 0.74)
  const leg = Math.min(dLeft, dRight) < thickness / 2
  const crossbar = ny >= 0.435 && ny <= 0.565 && nx >= 0.335 && nx <= 0.665
  if (leg || crossbar) return WHITE
  if (insideLeaf(nx, ny, 0.35, 0.155, -55) || insideLeaf(nx, ny, 0.65, 0.155, 55)) return GREEN
  return null
}

function insideRoundedRect(nx, ny, radius) {
  const left = nx >= radius && nx <= 1 - radius
  const top = ny >= radius && ny <= 1 - radius
  if (left && top) return true
  const cx = nx < 0.5 ? radius : 1 - radius
  const cy = ny < 0.5 ? radius : 1 - radius
  return Math.hypot(nx - cx, ny - cy) <= radius
}

function makePixelFn({ size, maskable = false, rounded = true }) {
  const SS = 4
  const scale = maskable ? 0.82 : 1
  return (px, py) => {
    let ra = 0
    let ga = 0
    let ba = 0
    let alpha = 0
    for (let sy = 0; sy < SS; sy++) {
      for (let sx = 0; sx < SS; sx++) {
        const nx = (px + (sx + 0.5) / SS) / size
        const ny = (py + (sy + 0.5) / SS) / size
        let color = null
        if (rounded && !insideRoundedRect(nx, ny, 0.18)) color = TRANSPARENT
        else {
          const cx = maskable ? (nx - 0.5) / scale + 0.5 : nx
          const cy = maskable ? (ny - 0.5) / scale + 0.5 : ny
          color = insideGlyph(cx, cy) || RED
        }
        const a = color[3] === undefined ? 255 : color[3]
        ra += color[0] * a
        ga += color[1] * a
        ba += color[2] * a
        alpha += a
      }
    }
    const total = SS * SS
    const ao = alpha / total
    if (ao === 0) return [0, 0, 0, 0]
    return [Math.round(ra / alpha), Math.round(ga / alpha), Math.round(ba / alpha), Math.round(ao)]
  }
}

const targets = [
  { file: 'icon-192.png', size: 192, maskable: false },
  { file: 'icon-512.png', size: 512, maskable: false },
  { file: 'icon-512-maskable.png', size: 512, maskable: true },
  { file: 'apple-touch-icon.png', size: 180, maskable: true, rounded: false },
]

for (const t of targets) {
  const png = encodePNG(t.size, makePixelFn(t))
  writeFileSync(join(OUT, t.file), png)
  console.log(`wrote ${t.file} (${png.length} bytes)`)
}