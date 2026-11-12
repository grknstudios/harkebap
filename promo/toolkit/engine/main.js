// ===== Pop Games promo — procedural motion graphics =====
const W = 1920, H = 1080;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');
const IMG = {};
const EVENTS = []; // global-time sound events {t,type}
function ev(t, type) { EVENTS.push({ t: +t.toFixed(3), type }); }

// ---------- utils ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eOutCubic = t => 1 - Math.pow(1 - t, 3);
const eInCubic = t => t * t * t;
const eInOut = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
const eOutBack = t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
const eOutBounce = x => { const n1 = 7.5625, d1 = 2.75;
  if (x < 1 / d1) return n1 * x * x; if (x < 2 / d1) return n1 * (x -= 1.5 / d1) * x + .75;
  if (x < 2.5 / d1) return n1 * (x -= 2.25 / d1) * x + .9375; return n1 * (x -= 2.625 / d1) * x + .984375; };
function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function shade(hex, p) { let n = parseInt(hex.slice(1), 16); let r = n >> 16, g = n >> 8 & 255, b = n & 255;
  const f = p < 0 ? 0 : 255; p = Math.abs(p); r = Math.round((f - r) * p + r); g = Math.round((f - g) * p + g); b = Math.round((f - b) * p + b); return `rgb(${r},${g},${b})`; }
function star(x, y, R1, R2, n) { ctx.beginPath(); for (let i = 0; i < n * 2; i++) { const r = i % 2 ? R2 : R1, a = i * Math.PI / n - Math.PI / 2; ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); } ctx.closePath(); }
function hexPath(x, y, r, rot = 0) { ctx.beginPath(); for (let i = 0; i < 6; i++) { const a = rot + i * Math.PI / 3; ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); } ctx.closePath(); }
const RAINBOW = ['#FF5A5F', '#FFB400', '#FFE14D', '#3DDC84', '#3BA7FF', '#A66BFF', '#FF6FB5'];

// ---------- text ----------
function text(str, x, y, o = {}) {
  const size = o.size || 60, font = o.font || 'Baloo', weight = o.weight || 800;
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  ctx.font = `${weight} ${size}px ${font}`; ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'middle';
  if (o.shadow !== false) { ctx.shadowColor = 'rgba(0,0,0,.35)'; ctx.shadowBlur = size * .22; ctx.shadowOffsetY = size * .07; }
  if (o.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = o.sw || size * .14; ctx.strokeStyle = o.stroke; ctx.strokeText(str, x, y); ctx.shadowColor = 'transparent'; }
  ctx.fillStyle = o.color || '#fff'; ctx.fillText(str, x, y); ctx.restore();
}
function measure(str, size, font = 'Baloo', weight = 800) { ctx.save(); ctx.font = `${weight} ${size}px ${font}`; const w = ctx.measureText(str).width; ctx.restore(); return w; }
// letters pop in one by one
function popText(str, cx, y, t, o = {}) {
  if (t <= 0) return;
  const size = o.size || 100, font = o.font || 'Baloo', weight = o.weight || 800;
  ctx.save(); ctx.font = `${weight} ${size}px ${font}`;
  const chars = [...str]; const ws = chars.map(ch => ctx.measureText(ch).width); const total = ws.reduce((a, b) => a + b, 0);
  let x = o.align === 'left' ? cx : cx - total / 2; const st = o.stagger ?? 0.04;
  chars.forEach((ch, i) => {
    const p = clamp((t - i * st) / 0.45);
    if (p > 0 && ch !== ' ') {
      const s = eOutBack(p); ctx.save(); ctx.translate(x + ws[i] / 2, y - (1 - eOutCubic(p)) * size * .5); ctx.scale(s, s); ctx.rotate((1 - eOutCubic(p)) * 0.35);
      const col = o.colors ? o.colors[i % o.colors.length] : o.color;
      text(ch, 0, 0, { ...o, size, font, weight, color: col, align: 'center' }); ctx.restore();
    }
    x += ws[i];
  });
  ctx.restore();
}

// ---------- particles ----------
function burst(x, y, dt, seed, colors, o = {}) {
  const life = o.life || 1.0; if (dt < 0 || dt > life) return;
  const n = o.n || 24, spd = o.spd || 420, size = o.size || 10; const R = rng(seed); const p = dt / life;
  for (let i = 0; i < n; i++) {
    const a = R() * Math.PI * 2, v = spd * (0.35 + R() * 0.8), c = colors[Math.floor(R() * colors.length)], s = size * (0.5 + R());
    const px = x + Math.cos(a) * v * dt * (1 - p * .4), py = y + Math.sin(a) * v * dt * (1 - p * .4) + 380 * dt * dt;
    ctx.save(); ctx.globalAlpha = 1 - eInCubic(p); ctx.translate(px, py); ctx.rotate(dt * 7 + i); ctx.fillStyle = c;
    if (i % 3 === 0) { star(0, 0, s, s * .45, 5); ctx.fill(); } else if (i % 3 === 1) { ctx.fillRect(-s / 2, -s / 4, s, s / 2); } else { ctx.beginPath(); ctx.arc(0, 0, s * .4, 0, 7); ctx.fill(); }
    ctx.restore();
  }
  if (o.ring !== false) { ctx.save(); ctx.globalAlpha = (1 - p) * .85; ctx.strokeStyle = '#fff'; ctx.lineWidth = 7 * (1 - p); ctx.beginPath(); ctx.arc(x, y, 15 + eOutCubic(p) * 12 * size, 0, 7); ctx.stroke(); ctx.restore(); }
}

// ---------- backgrounds ----------
function bgGrad(c1, c2, t, o = {}) {
  const g = ctx.createLinearGradient(0, 0, W * .35, H); g.addColorStop(0, c1); g.addColorStop(1, c2); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(o.rx ?? W * .5, o.ry ?? H * .5); ctx.rotate(t * 0.06); ctx.globalAlpha = o.rayAlpha ?? 0.06; ctx.fillStyle = '#fff';
  const n = 18; for (let i = 0; i < n; i++) { const a0 = i / n * Math.PI * 2, a1 = a0 + Math.PI / n; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a0) * 2600, Math.sin(a0) * 2600); ctx.lineTo(Math.cos(a1) * 2600, Math.sin(a1) * 2600); ctx.fill(); }
  ctx.restore();
  const R = rng(o.seed || 7); const n2 = o.n || 28;
  for (let i = 0; i < n2; i++) {
    const bx = R() * W, by = R() * H, r = 8 + R() * 38, sp = 12 + R() * 30, ph = R() * 6.28, al = 0.07 + 0.1 * R(), rot = R() * 6;
    const y = ((by - t * sp) % (H + 200) + H + 200) % (H + 200) - 100, x = bx + Math.sin(t * .5 + ph) * 30;
    ctx.save(); ctx.globalAlpha = al; ctx.fillStyle = o.multi ? RAINBOW[i % RAINBOW.length] : '#fff'; ctx.translate(x, y); ctx.rotate(rot + t * .3 * (i % 2 ? 1 : -1));
    const sh = o.shape || 'circle';
    if (sh === 'hex') { hexPath(0, 0, r, 0); ctx.fill(); ctx.globalCompositeOperation = 'destination-out'; ctx.beginPath(); ctx.arc(0, 0, r * .45, 0, 7); ctx.fill(); }
    else if (sh === 'leaf') { ctx.beginPath(); ctx.ellipse(0, 0, r * .45, r, 0, 0, 7); ctx.fill(); }
    else if (sh === 'rect') { rr(-r * .5, -r * .8, r, r * 1.6, r * .3); ctx.fill(); }
    else if (sh === 'star') { star(0, 0, r, r * .45, 5); ctx.fill(); }
    else { ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill(); }
    ctx.restore();
  }
  const v = ctx.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * 1.05); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,.38)'); ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
}

// ---------- icons / badge ----------
function drawIcon(key, cx, cy, size, o = {}) {
  if (size <= 1) return; const img = IMG[key]; ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1); ctx.translate(cx, cy); ctx.rotate(o.rot || 0);
  const r = size * .235;
  if (o.glow) { ctx.save(); ctx.shadowColor = o.glowColor || 'rgba(255,255,255,.9)'; ctx.shadowBlur = size * .35 * o.glow; rr(-size / 2, -size / 2, size, size, r); ctx.fillStyle = '#fff'; ctx.fill(); ctx.restore(); }
  ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = size * .14; ctx.shadowOffsetY = size * .06; rr(-size / 2, -size / 2, size, size, r); ctx.fillStyle = '#fff'; ctx.fill(); ctx.restore();
  ctx.save(); rr(-size / 2, -size / 2, size, size, r); ctx.clip(); ctx.drawImage(img, -size * .52, -size * .52, size * 1.04, size * 1.04);
  const g = ctx.createLinearGradient(0, -size / 2, 0, size / 2); g.addColorStop(0, 'rgba(255,255,255,.22)'); g.addColorStop(.45, 'rgba(255,255,255,0)'); ctx.fillStyle = g; ctx.fillRect(-size / 2, -size / 2, size, size);
  // moving shine
  if (o.shine !== undefined && o.shine > 0 && o.shine < 1) { const sx = lerp(-size * 1.2, size * 1.2, o.shine); const sg = ctx.createLinearGradient(sx - size * .3, 0, sx + size * .3, 0); sg.addColorStop(0, 'rgba(255,255,255,0)'); sg.addColorStop(.5, 'rgba(255,255,255,.5)'); sg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = sg; ctx.fillRect(-size / 2, -size / 2, size, size); }
  ctx.restore();
  ctx.lineWidth = Math.max(2, size * .016); ctx.strokeStyle = 'rgba(255,255,255,.75)'; rr(-size / 2, -size / 2, size, size, r); ctx.stroke();
  ctx.restore();
}
function drawBadge(cx, cy, w, alpha = 1) { const img = IMG.badge; const h = w * img.height / img.width; ctx.save(); ctx.globalAlpha *= alpha; ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 30; ctx.shadowOffsetY = 10; ctx.drawImage(img, cx - w / 2, cy - h / 2, w, h); ctx.restore(); }

// ---------- phone ----------
const PW = 470, PHh = 960;
function drawPhone(x, y, scale, rot, drawScreen) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(scale, scale);
  ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.55)'; ctx.shadowBlur = 70; ctx.shadowOffsetY = 35; rr(-PW / 2, -PHh / 2, PW, PHh, 72); ctx.fillStyle = '#0d0d12'; ctx.fill(); ctx.restore();
  const eg = ctx.createLinearGradient(-PW / 2, 0, PW / 2, 0); eg.addColorStop(0, '#6b6f7d'); eg.addColorStop(.5, '#2b2d35'); eg.addColorStop(1, '#6b6f7d');
  ctx.lineWidth = 7; ctx.strokeStyle = eg; rr(-PW / 2, -PHh / 2, PW, PHh, 72); ctx.stroke();
  const sw = PW - 30, sh = PHh - 30; ctx.save(); rr(-sw / 2, -sh / 2, sw, sh, 58); ctx.clip(); ctx.translate(-sw / 2, -sh / 2); drawScreen(sw, sh); ctx.restore();
  rr(-62, -PHh / 2 + 30, 124, 36, 18); ctx.fillStyle = '#000'; ctx.fill();
  // glass reflection
  ctx.save(); rr(-sw / 2, -sh / 2, sw, sh, 58); ctx.clip(); const gg = ctx.createLinearGradient(-sw / 2, -sh / 2, sw / 2, sh / 2); gg.addColorStop(0, 'rgba(255,255,255,.10)'); gg.addColorStop(.35, 'rgba(255,255,255,0)'); ctx.fillStyle = gg; ctx.fillRect(-sw / 2, -sh / 2, sw, sh); ctx.restore();
  ctx.restore();
}

// ---------- shared game HUD / banners ----------
function hudPill(w, label, col = 'rgba(0,0,0,.28)') { rr(w / 2 - 95, 66, 190, 50, 25); ctx.fillStyle = col; ctx.fill(); text(label, w / 2, 92, { size: 30, font: 'Fredoka', weight: 700, shadow: false });
  ctx.beginPath(); ctx.arc(46, 91, 24, 0, 7); ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fill(); text('II', 46, 92, { size: 22, font: 'Fredoka', weight: 700, shadow: false });
  ctx.beginPath(); ctx.arc(w - 46, 91, 24, 0, 7); ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fill(); text('↻', w - 46, 92, { size: 30, font: 'DejaVu Sans', weight: 700, shadow: false }); }
function completeBanner(w, h, dt, accent, seed) {
  if (dt < 0) return; const a = clamp(dt * 3) * (1 - seg(dt, 1.85, 2.15));
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(10,10,40,.45)'; ctx.fillRect(0, 0, w, h);
  const p = eOutBack(seg(dt, 0, .45)); ctx.translate(w / 2, h / 2); ctx.scale(p, p);
  rr(-180, -110, 360, 220, 36); ctx.fillStyle = '#fff'; ctx.shadowColor = 'rgba(0,0,0,.4)'; ctx.shadowBlur = 30; ctx.fill(); ctx.shadowColor = 'transparent';
  rr(-180, -110, 360, 70, [36, 36, 0, 0]); ctx.fillStyle = accent; ctx.fill();
  text('LEVEL COMPLETE!', 0, -74, { size: 38, color: '#fff', stroke: 'rgba(0,0,0,.25)', sw: 6, shadow: false });
  for (let i = 0; i < 3; i++) { const sp = eOutBack(seg(dt, .3 + i * .15, .7 + i * .15)); ctx.save(); ctx.translate((i - 1) * 95, 22 - (i === 1 ? 14 : 0)); ctx.scale(sp, sp); star(0, 0, 40, 18, 5); ctx.fillStyle = '#FFC107'; ctx.fill(); ctx.lineWidth = 5; ctx.strokeStyle = '#E08E00'; ctx.stroke(); ctx.restore(); }
  text('+50', 0, 82, { size: 30, font: 'Fredoka', weight: 700, color: '#555', shadow: false, alpha: seg(dt, .8, 1.1) });
  ctx.restore();
  ctx.save(); ctx.globalAlpha = a; burst(w / 2, h / 2 - 40, dt - .2, seed, RAINBOW, { n: 50, spd: 650, life: 1.5, size: 12, ring: false }); ctx.restore();
}

// ---------- sort-stack engine (used by Feather Pop, Park Pop, Nut Pop) ----------
function solveSort(stacks, cap) {
  const key = s => s.map(x => x.join('')).join('|');
  const solved = s => s.every(x => x.length === 0 || (x.length === cap && x.every(c => c === x[0])));
  const start = stacks.map(s => s.slice()); const q = [[start, null, null]]; const seen = new Set([key(start)]); let qi = 0;
  while (qi < q.length) {
    const node = q[qi++]; const s = node[0];
    if (solved(s)) { const path = []; let n = node; while (n[1]) { path.unshift(n[2]); n = n[1]; } return path; }
    if (q.length > 400000) return null;
    for (let i = 0; i < s.length; i++) {
      const a = s[i]; if (!a.length) continue; const top = a[a.length - 1]; let run = 1; while (run < a.length && a[a.length - 1 - run] === top) run++;
      if (run === a.length && a.length === cap) continue;
      for (let j = 0; j < s.length; j++) {
        if (i === j) continue; const b = s[j]; if (b.length >= cap) continue; if (b.length && b[b.length - 1] !== top) continue; if (!b.length && run === a.length) continue;
        const k = Math.min(run, cap - b.length); const ns = s.map(x => x.slice()); const mv = ns[i].splice(ns[i].length - k, k); ns[j].push(...mv);
        const kk = key(ns); if (seen.has(kk)) continue; seen.add(kk); q.push([ns, node, [i, j, k]]);
      }
    }
  }
  return null;
}
function makePuzzle(seed, colors, nStacks, cap, minLen, maxLen) {
  for (let s = seed; s < seed + 400; s++) {
    const R = rng(s); const items = []; for (const c of colors) for (let i = 0; i < cap; i++) items.push(c);
    for (let i = items.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [items[i], items[j]] = [items[j], items[i]]; }
    const st = []; for (let i = 0; i < nStacks; i++) st.push([]); for (let i = 0; i < colors.length; i++) st[i] = items.slice(i * cap, (i + 1) * cap);
    // spread empties: rotate so empty stacks are not all at the end
    if (st.some(x => x.length && x.every(c => c === x[0]))) continue;
    const sol = solveSort(st, cap); if (sol && sol.length >= minLen && sol.length <= maxLen) return { stacks: st, sol };
  }
  throw new Error('no puzzle');
}
function buildSortLevel(p, cap, T0, T1, moveDur, stagger, sceneT0) {
  let id = 0; const st = p.stacks.map(s => s.map(c => ({ id: id++, c })));
  const items = []; st.forEach((s, si) => s.forEach((it, ii) => { items[it.id] = { c: it.c, moves: [], home: { s: si, i: ii }, id: it.id }; }));
  const n = p.sol.length; const dt = (T1 - T0) / n; const completes = [];
  p.sol.forEach(([a, b, k], m) => {
    const t = T0 + m * dt;
    for (let q = 0; q < k; q++) {
      const it = st[a].pop(); const fromIdx = st[a].length; const toIdx = st[b].length; st[b].push(it);
      const ts = t + q * stagger; items[it.id].moves.push({ t0: ts, t1: ts + moveDur, from: { s: a, i: fromIdx }, to: { s: b, i: toIdx } });
      ev(sceneT0 + ts + 0.02, 'lift'); ev(sceneT0 + ts + moveDur, 'pop');
    }
    if (st[b].length === cap && st[b].every(x => x.c === st[b][0].c)) { const tc = t + (k - 1) * stagger + moveDur; completes.push({ t: tc, s: b, ids: st[b].map(x => x.id), c: st[b][0].c }); ev(sceneT0 + tc + .05, 'chime'); }
  });
  return { items, completes, end: T0 + n * dt };
}
function itemState(it, t) {
  let pos = it.home, mv = null, p = 0;
  for (const m of it.moves) { if (t >= m.t1) pos = m.to; else if (t >= m.t0) { mv = m; p = (t - m.t0) / (m.t1 - m.t0); break; } else break; }
  return { pos, mv, p };
}
// level windows helper
function makeLevels(windows, factory) { return windows.map(([a, b], i) => factory(a, b, i)); }
function levelAt(levels, t) { for (let i = levels.length - 1; i >= 0; i--) if (t >= levels[i].wa) return levels[i]; return levels[0]; }

// ================= FEATHER POP =================
const BIRDC = { r: '#EF4444', b: '#3B82F6', y: '#FBBF24', p: '#F472B6', g: '#22C55E' };
function drawBird(x, y, col, face, flap, sc = 1, blink = false) {
  ctx.save(); ctx.translate(x, y); ctx.scale(face * sc, sc);
  ctx.strokeStyle = '#F59E0B'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-6, 20); ctx.lineTo(-8, 29); ctx.moveTo(6, 20); ctx.lineTo(5, 29); ctx.stroke();
  ctx.fillStyle = shade(col, -0.3); ctx.beginPath(); ctx.moveTo(-18, 6); ctx.lineTo(-38, -2); ctx.lineTo(-35, 16); ctx.closePath(); ctx.fill();
  const g = ctx.createRadialGradient(-6, -10, 4, 0, 0, 32); g.addColorStop(0, shade(col, 0.4)); g.addColorStop(1, col); ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(0, 0, 25, 24, 0, 0, 7); ctx.fill();
  ctx.fillStyle = shade(col, 0.6); ctx.beginPath(); ctx.ellipse(9, 9, 13, 12, 0, 0, 7); ctx.fill();
  ctx.fillStyle = col; ctx.beginPath(); ctx.ellipse(-3, -24, 4, 9, -0.35, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(3, -25, 3.5, 8, 0.25, 0, 7); ctx.fill();
  ctx.save(); ctx.translate(-6, 2); ctx.rotate(-0.25 + flap * 0.9); ctx.fillStyle = shade(col, -0.22); ctx.beginPath(); ctx.ellipse(-6, 0, 16, 9, 0, 0, 7); ctx.fill(); ctx.restore();
  ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(10, -6, 8.5, blink ? 1.6 : 9.5, 0, 0, 7); ctx.fill();
  if (!blink) { ctx.fillStyle = '#1a1a1a'; ctx.beginPath(); ctx.arc(12, -5, 4.8, 0, 7); ctx.fill(); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(13.6, -7.2, 1.7, 0, 7); ctx.fill(); }
  ctx.fillStyle = '#FFA726'; ctx.beginPath(); ctx.moveTo(20, -3); ctx.lineTo(33, 2); ctx.lineTo(20, 7); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,110,150,.55)'; ctx.beginPath(); ctx.arc(14, 7, 4, 0, 7); ctx.fill();
  ctx.restore();
}
function featherGame(sceneT0) {
  const cap = 4, BR = [{ side: -1, y: 270 }, { side: 1, y: 395 }, { side: -1, y: 520 }, { side: 1, y: 645 }, { side: -1, y: 770 }, { side: 1, y: 875 }];
  const levels = makeLevels([[2.4, 13]], (wa, wb, li) => {
    const P = makePuzzle(1011 + li * 77, ['r', 'b', 'y', 'p'], 6, cap, 6, 9);
    const L = buildSortLevel(P, cap, wa + 0.7, wb - 3.7, 0.55, 0.07, sceneT0); L.wa = wa; L.wb = wb; L.num = 24 + li; FANFARES.push(sceneT0 + L.end + .5); return L;
  });
  const slot = (s, i) => { const b = BR[s]; return { x: b.side < 0 ? 52 + i * 58 : 440 - 52 - i * 58, y: b.y - 30, face: -b.side }; };
  return (w, h, t) => {
    const sky = ctx.createLinearGradient(0, 0, 0, h); sky.addColorStop(0, '#9FE0FF'); sky.addColorStop(1, '#5BB8F0'); ctx.fillStyle = sky; ctx.fillRect(0, 0, w, h);
    for (let i = 0; i < 4; i++) { const cx = ((i * 160 + t * 12) % 620) - 90, cy = 150 + i * 190; ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.beginPath(); ctx.arc(cx, cy, 30, 0, 7); ctx.arc(cx + 34, cy - 12, 38, 0, 7); ctx.arc(cx + 72, cy, 28, 0, 7); ctx.fill(); }
    ctx.fillStyle = '#7CCB6B'; ctx.beginPath(); ctx.ellipse(110, h + 30, 260, 110, 0, 0, 7); ctx.fill(); ctx.fillStyle = '#5DB35A'; ctx.beginPath(); ctx.ellipse(380, h + 40, 240, 100, 0, 0, 7); ctx.fill();
    const L = levelAt(levels, t); const lt = t;
    hudPill(w, 'LEVEL ' + L.num);
    const appear = eOutBack(seg(lt, L.wa, L.wa + .5));
    BR.forEach((b, bi) => { ctx.save(); const x0 = b.side < 0 ? -10 : 450, x1 = b.side < 0 ? 292 : 148; const xx1 = lerp(x0, x1, appear);
      ctx.strokeStyle = '#7A4A22'; ctx.lineWidth = 18; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0, b.y + 4); ctx.lineTo(xx1, b.y); ctx.stroke();
      ctx.strokeStyle = '#A26A36'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x0, b.y - 3); ctx.lineTo(xx1, b.y - 5); ctx.stroke();
      ctx.fillStyle = '#43A047'; ctx.beginPath(); ctx.ellipse(xx1 - b.side * 4, b.y + 12, 9, 17, b.side * .8, 0, 7); ctx.fill(); ctx.fillStyle = '#66BB6A'; ctx.beginPath(); ctx.ellipse(xx1 + b.side * 12, b.y - 8, 8, 15, -b.side * .9, 0, 7); ctx.fill();
      ctx.restore(); });
    // completion glow + bursts
    L.completes.forEach(c => { const b = BR[c.s]; const d = lt - c.t; if (d > 0 && d < .8) { ctx.save(); ctx.globalAlpha = (1 - d / .8) * .6; ctx.fillStyle = BIRDC[c.c]; rr(b.side < 0 ? 10 : 150, b.y - 70, 280, 90, 40); ctx.fill(); ctx.restore(); }
      burst(b.side < 0 ? 140 : 300, b.y - 30, d, c.s * 13 + 5, [BIRDC[c.c], '#fff', '#FFD54F'], { n: 26, spd: 380, life: 1.1, size: 10 }); });
    const flyMap = {}; L.completes.forEach(c => c.ids.forEach((id, k) => flyMap[id] = { t: c.t + .35 + (3 - k) * .08 }));
    const draws = [];
    L.items.forEach(it => {
      const st = itemState(it, lt); let x, y, face, flap = 0, sc = 1;
      if (st.mv) { const A = slot(st.mv.from.s, st.mv.from.i), B = slot(st.mv.to.s, st.mv.to.i); const e = eInOut(st.p); x = lerp(A.x, B.x, e); y = lerp(A.y, B.y, e) - Math.sin(Math.PI * st.p) * (80 + Math.abs(B.y - A.y) * .3 + Math.abs(B.x - A.x) * .2); face = Math.sign(B.x - A.x) || A.face; flap = Math.sin(lt * 42); sc = 1.08; }
      else { const P = slot(st.pos.s, st.pos.i); x = P.x; y = P.y + Math.sin(lt * 3 + it.id) * 1.2; face = P.face; const lastLand = it.moves.length ? it.moves.filter(m => m.t1 <= lt).map(m => m.t1).pop() : null; if (lastLand && lt - lastLand < .25) { sc = 1 + Math.sin((lt - lastLand) / .25 * Math.PI) * .12; } }
      const fm = flyMap[it.id]; if (fm && lt > fm.t) { const q = (lt - fm.t) / 1.3; if (q > 1) return; x += face * q * 220; y -= eInCubic(q) * 900 + q * 80; flap = Math.sin(lt * 50); sc = 1.05; }
      const appearB = seg(lt, L.wa + .2 + it.id * .02, L.wa + .6 + it.id * .02); if (appearB <= 0) return;
      const blink = ((lt * 1.3 + it.id * .37) % 3.1) < .12;
      draws.push([y, () => drawBird(x, y, BIRDC[it.c], face, flap, sc * eOutBack(appearB), blink)]);
    });
    draws.sort((a, b) => a[0] - b[0]).forEach(d => d[1]());
    // tap hint finger on first move of a level
    completeBanner(w, h, lt - (L.end + .5), '#29B6F6', 77 + L.num);
  };
}

// ================= PARK POP =================
const CARC = { r: '#EF3B3B', b: '#2E7BFF', g: '#2DBE4E', y: '#FFC31A' };
function drawCar(x, y, head, col, sc = 1) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(head); ctx.scale(sc, sc);
  ctx.fillStyle = 'rgba(0,0,0,.3)'; rr(-24, -42, 52, 92, 14); ctx.fill();
  const g = ctx.createLinearGradient(-26, 0, 26, 0); g.addColorStop(0, shade(col, -0.15)); g.addColorStop(.5, shade(col, 0.15)); g.addColorStop(1, shade(col, -0.15));
  ctx.fillStyle = g; rr(-26, -46, 52, 92, 15); ctx.fill();
  ctx.fillStyle = '#9FD8FF'; ctx.beginPath(); ctx.moveTo(-19, -24); ctx.lineTo(19, -24); ctx.lineTo(15, -12); ctx.lineTo(-15, -12); ctx.closePath(); ctx.fill();
  ctx.fillStyle = shade(col, -0.25); rr(-17, -12, 34, 34, 7); ctx.fill(); ctx.fillStyle = shade(col, 0.1); rr(-13, -8, 26, 24, 5); ctx.fill();
  ctx.fillStyle = '#7FC2EE'; rr(-16, 24, 32, 10, 4); ctx.fill();
  ctx.fillStyle = '#FFF3B0'; rr(-21, -45, 11, 6, 3); ctx.fill(); rr(10, -45, 11, 6, 3); ctx.fill();
  ctx.fillStyle = '#B71C1C'; rr(-21, 40, 10, 5, 2); ctx.fill(); rr(11, 40, 10, 5, 2); ctx.fill();
  ctx.restore();
}
function parkGame(sceneT0) {
  const cap = 4; const laneX = i => 45 + i * 70; const slotY = i => 300 + (3 - i) * 112; const roadY = 182;
  const levels = makeLevels([[2.4, 13]], (wa, wb, li) => {
    const P = makePuzzle(2203 + li * 91, ['r', 'b', 'g', 'y'], 6, cap, 6, 9);
    const L = buildSortLevel(P, cap, wa + .7, wb - 3.7, 0.6, 0.08, sceneT0); L.wa = wa; L.wb = wb; L.num = 17 + li; FANFARES.push(sceneT0 + L.end + .6); return L;
  });
  const bez = (A, B, p) => { const P1 = { x: A.x, y: roadY - 70 }, P2 = { x: B.x, y: roadY - 70 }; const u = 1 - p;
    const x = u * u * u * A.x + 3 * u * u * p * P1.x + 3 * u * p * p * P2.x + p * p * p * B.x; const y = u * u * u * A.y + 3 * u * u * p * P1.y + 3 * u * p * p * P2.y + p * p * p * B.y; return { x, y }; };
  return (w, h, t) => {
    ctx.fillStyle = '#3C4150'; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = '#2B2F3A'; ctx.fillRect(0, 130, w, 110); ctx.strokeStyle = '#FFD54F'; ctx.lineWidth = 4; ctx.setLineDash([26, 20]); ctx.lineDashOffset = -t * 60; ctx.beginPath(); ctx.moveTo(0, 185); ctx.lineTo(w, 185); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = '#E9E3D3'; ctx.fillRect(0, 238, w, 8);
    const L = levelAt(levels, t); const lt = t;
    for (let i = 0; i < 6; i++) { const x = laneX(i); ctx.fillStyle = 'rgba(255,255,255,.04)'; ctx.fillRect(x - 33, 246, 66, 455); ctx.strokeStyle = 'rgba(255,255,255,.75)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x - 35, 250); ctx.lineTo(x - 35, 700); ctx.stroke(); }
    ctx.beginPath(); ctx.moveTo(laneX(5) + 35, 250); ctx.lineTo(laneX(5) + 35, 700); ctx.stroke(); ctx.beginPath(); ctx.moveTo(10, 700); ctx.lineTo(430, 700); ctx.stroke();
    // grass + trees
    ctx.fillStyle = '#4CAF50'; ctx.fillRect(0, 712, w, h - 712); for (let i = 0; i < 5; i++) { ctx.fillStyle = '#2E7D32'; ctx.beginPath(); ctx.arc(45 + i * 88, 800 + (i % 2) * 40, 34, 0, 7); ctx.fill(); ctx.fillStyle = '#43A047'; ctx.beginPath(); ctx.arc(38 + i * 88, 792 + (i % 2) * 40, 22, 0, 7); ctx.fill(); }
    hudPill(w, 'LEVEL ' + L.num);
    L.completes.forEach(c => { const d = lt - c.t; if (d > 0 && d < 1) { ctx.save(); ctx.globalAlpha = (1 - d) * .55; ctx.fillStyle = CARC[c.c]; ctx.fillRect(laneX(c.s) - 33, 246, 66, 455); ctx.restore(); }
      burst(laneX(c.s), 470, d, c.s * 7 + 3, [CARC[c.c], '#fff', '#FFE082'], { n: 28, spd: 420, life: 1.1, size: 11 });
      if (d > 0 && d < 1.1) { const pp = eOutBack(seg(d, 0, .35)); ctx.save(); ctx.globalAlpha = 1 - seg(d, .8, 1.1); ctx.translate(laneX(c.s), 450); ctx.scale(pp, pp); text('POP!', 0, 0, { size: 46, color: '#fff', stroke: shade(CARC[c.c], -0.35), sw: 9 }); ctx.restore(); } });
    const exitMap = {}; L.completes.forEach(c => c.ids.forEach((id, k) => exitMap[id] = { t: c.t + .35 + (3 - k) * .1 }));
    L.items.forEach(it => {
      const st = itemState(it, lt); let x, y, head = 0, sc = 1;
      if (st.mv) { const A = { x: laneX(st.mv.from.s), y: slotY(st.mv.from.i) }, B = { x: laneX(st.mv.to.s), y: slotY(st.mv.to.i) }; const e = eInOut(st.p); const P = bez(A, B, e), P2 = bez(A, B, Math.min(1, e + .02)), P0 = bez(A, B, Math.max(0, e - .02)); x = P.x; y = P.y; head = Math.atan2(P2.x - P0.x, -(P2.y - P0.y)); sc = 1.05; }
      else { x = laneX(st.pos.s); y = slotY(st.pos.i); head = it.moves.length && it.moves[0].t1 <= lt ? Math.PI : 0; }
      const em = exitMap[it.id]; if (em && lt > em.t) { const q = (lt - em.t) / .9; if (q > 1) return; head = lerp(head, head > 1 ? 2 * Math.PI : 0, eOutCubic(seg(q, 0, .3))); y -= eInCubic(q) * 900; }
      const ap = seg(lt, L.wa + .15 + it.id * .02, L.wa + .55 + it.id * .02); if (ap <= 0) return;
      drawCar(x, y, head, CARC[it.c], sc * eOutBack(ap));
    });
    completeBanner(w, h, lt - (L.end + .6), '#EF3B3B', 51 + L.num);
  };
}


// ================= PARK POP — real store screenshots =================
function parkShots(sceneT0, pre = 'pp', ripples = true, winIdx = 5) {
  const N = 6, T0 = 2.4, DT = 1.6, TR = .38;
  for (let i = 1; i < N; i++) ev(sceneT0 + T0 + i * DT, 'whooshS');
  if (winIdx >= 0) ev(sceneT0 + T0 + winIdx * DT + .2, 'fanfare');
  const cover = (img, w, h, z, dx) => { const sc = Math.max(w / img.width, h / img.height) * z; const iw = img.width * sc, ih = img.height * sc; ctx.drawImage(img, dx + (w - iw) / 2, (h - ih) / 2, iw, ih); };
  return (w, h, t) => {
    ctx.fillStyle = '#3C4150'; ctx.fillRect(0, 0, w, h);
    if (t < T0) return;
    const k = Math.min(N - 1, Math.floor((t - T0) / DT)); const lt = t - T0 - k * DT;
    const p = k > 0 ? eInOut(clamp(lt / TR)) : 1;
    if (k > 0 && p < 1) cover(IMG[pre + (k - 1)], w, h, 1.03 + .03, -p * w * .35);
    ctx.save(); if (k > 0 && p < 1) { ctx.translate((1 - p) * w, 0); ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 30; }
    const z = 1.03 + .03 * clamp(lt / DT); cover(IMG[pre + k], w, h, z, 0); ctx.restore();
    if (k === 0) { const a = 1 - seg(t, T0, T0 + .35); if (a > 0) { ctx.fillStyle = `rgba(60,65,80,${a})`; ctx.fillRect(0, 0, w, h); } }
    // tap ripple hint on gameplay shots
    if (ripples && k < N - 1) { const rt = (lt - .55) / .5; if (rt > 0 && rt < 1) { const px = [.25, .55, .4, .7, .3][k] * w, py = [.5, .4, .55, .45, .5][k] * h; ctx.save(); ctx.globalAlpha = 1 - rt; ctx.strokeStyle = '#fff'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(px, py, 14 + rt * 40, 0, 7); ctx.stroke(); ctx.fillStyle = 'rgba(255,255,255,.5)'; ctx.beginPath(); ctx.arc(px, py, 14, 0, 7); ctx.fill(); ctx.restore(); } }
  };
}
// ================= NUT POP =================
const NUTC = { r: '#F0443A', b: '#3A86FF', g: '#36C24F', y: '#FFC21A', p: '#FF5DB1' };
function drawNut(x, y, col, spin, sc = 1, glow = 0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc);
  if (glow > 0) { ctx.shadowColor = '#FFF59D'; ctx.shadowBlur = 25 * glow; }
  rr(-32, -17, 64, 34, 7); ctx.fillStyle = shade(col, -0.25); ctx.fill(); ctx.shadowColor = 'transparent';
  ctx.save(); rr(-32, -17, 64, 34, 7); ctx.clip();
  const off = ((spin % 1) + 1) % 1 * 42;
  for (let k = -2; k <= 2; k++) { const xa = -53 + off + k * 42; const g = ctx.createLinearGradient(xa, 0, xa + 42, 0); g.addColorStop(0, shade(col, -0.18)); g.addColorStop(.5, shade(col, 0.28)); g.addColorStop(1, shade(col, -0.18)); ctx.fillStyle = g; ctx.fillRect(xa, -17, 42, 34); ctx.fillStyle = 'rgba(0,0,0,.18)'; ctx.fillRect(xa + 40, -17, 2, 34); }
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.fillRect(-32, -17, 64, 6); ctx.fillStyle = 'rgba(0,0,0,.18)'; ctx.fillRect(-32, 11, 64, 6);
  ctx.restore(); ctx.restore();
}
function nutGame(sceneT0) {
  const cap = 4; const boltX = i => 40 + i * 72; const slotY = i => 610 - i * 40; const lift = 330;
  const levels = makeLevels([[2.4, 13]], (wa, wb, li) => {
    const P = makePuzzle(3301 + li * 57, ['r', 'b', 'g', 'y'], 6, cap, 6, 9);
    const L = buildSortLevel(P, cap, wa + .7, wb - 3.7, 0.6, 0.08, sceneT0); L.wa = wa; L.wb = wb; L.num = 31 + li; FANFARES.push(sceneT0 + L.end + .5); return L;
  });
  return (w, h, t) => {
    const g = ctx.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#1B2C6B'); g.addColorStop(1, '#0E1638'); ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(255,255,255,.05)'; ctx.lineWidth = 1; for (let x = 0; x < w; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); } for (let y = 0; y < h; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
    const L = levelAt(levels, t); const lt = t;
    hudPill(w, 'LEVEL ' + L.num, 'rgba(255,255,255,.12)');
    // board
    rr(8, 632, 424, 58, 22); ctx.fillStyle = '#2F57C9'; ctx.fill(); rr(8, 632, 424, 18, [22, 22, 0, 0]); ctx.fillStyle = '#4C78F0'; ctx.fill();
    for (const sx of [30, 410]) { ctx.beginPath(); ctx.arc(sx, 670, 7, 0, 7); ctx.fillStyle = '#9DB5F5'; ctx.fill(); }
    const doneMap = {}; L.completes.forEach(c => doneMap[c.s] = c);
    for (let i = 0; i < 6; i++) { const x = boltX(i); const rg = ctx.createLinearGradient(x - 8, 0, x + 8, 0); rg.addColorStop(0, '#8E99AE'); rg.addColorStop(.5, '#F1F4FA'); rg.addColorStop(1, '#8E99AE'); ctx.fillStyle = rg; rr(x - 8, 420, 16, 220, 6); ctx.fill();
      ctx.strokeStyle = 'rgba(80,90,110,.55)'; ctx.lineWidth = 2; for (let y = 430; y < 630; y += 12) { ctx.beginPath(); ctx.moveTo(x - 8, y + 4); ctx.lineTo(x + 8, y); ctx.stroke(); }
      const c = doneMap[i]; if (c && lt > c.t) { const d = lt - c.t; const cp = eOutBack(seg(d, .1, .5)); ctx.save(); ctx.translate(x, 408); ctx.scale(cp, cp); ctx.beginPath(); ctx.arc(0, 0, 20, 0, 7); ctx.fillStyle = '#2DBE4E'; ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = '#fff'; ctx.stroke(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(-8, 0); ctx.lineTo(-2, 7); ctx.lineTo(9, -7); ctx.stroke(); ctx.restore(); }
    }
    L.completes.forEach(c => { burst(boltX(c.s), 520, lt - c.t, c.s * 11 + 1, [NUTC[c.c], '#FFF59D', '#fff'], { n: 26, spd: 380, life: 1.1, size: 10 });
      const d = lt - c.t; if (d > 0 && d < 1.1) { const pp = eOutBack(seg(d, 0, .35)); ctx.save(); ctx.globalAlpha = 1 - seg(d, .8, 1.1); ctx.translate(clamp(boltX(c.s), 80, 360), 350); ctx.scale(pp, pp); text('POP!', 0, 0, { size: 46, color: '#FFD54F', stroke: '#5A2A00', sw: 9 }); ctx.restore(); } });
    const draws = [];
    L.items.forEach(it => {
      const st = itemState(it, lt); let x, y, spin = 0, sc = 1, glow = 0;
      if (st.mv) { const A = { x: boltX(st.mv.from.s), y: slotY(st.mv.from.i) }, B = { x: boltX(st.mv.to.s), y: slotY(st.mv.to.i) }; const p = st.p;
        if (p < .32) { const q = eOutCubic(p / .32); x = A.x; y = lerp(A.y, lift, q); spin = q * 2; }
        else if (p < .64) { const q = (p - .32) / .32; x = lerp(A.x, B.x, eInOut(q)); y = lift - Math.sin(Math.PI * q) * 24; spin = 2; }
        else { const q = (p - .64) / .36; x = B.x; y = lerp(lift, B.y, eInCubic(q)); spin = 2 - q * 2; }
        sc = 1.06; }
      else { x = boltX(st.pos.s); y = slotY(st.pos.i); const c = doneMap[st.pos.s]; if (c && lt > c.t) glow = Math.max(0, 1 - (lt - c.t) / 1.2); }
      const ap = seg(lt, L.wa + .15 + it.id * .02, L.wa + .55 + it.id * .02); if (ap <= 0) return;
      draws.push([st.mv ? 1 : 0, () => drawNut(x, y, NUTC[it.c], spin, sc * eOutBack(ap), glow)]);
    });
    draws.sort((a, b) => a[0] - b[0]).forEach(d => d[1]());
    completeBanner(w, h, lt - (L.end + .5), '#FFB300', 33 + L.num);
  };
}

// ================= TERMINAL TANGLE =================
const PAXC = { r: '#EF4444', b: '#3B82F6', g: '#22C55E', y: '#FACC15', p: '#A855F7' };
const qpos = k => { const row = Math.floor(k / 6), col = k % 6; return { x: row % 2 === 0 ? 70 + col * 60 : 370 - col * 60, y: 705 + row * 62 }; };
const bayY = b => 178 + b * 122; const benchPos = k => ({ x: 70 + k * 75, y: 588 }); const doorPos = b => ({ x: 70 + 243, y: bayY(b) + 26 });
function simTerminal(seed, busSeq, T0, step, sceneT0) {
  const counts = {}; busSeq.forEach(c => counts[c] = (counts[c] || 0) + 4);
  const R = rng(seed); const q = []; for (const c in counts) for (let i = 0; i < counts[c]; i++) q.push(c);
  for (let i = q.length - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [q[i], q[j]] = [q[j], q[i]]; }
  const pax = q.map((c, i) => ({ c, segs: [], start: qpos(i), board: Infinity, id: i }));
  const buses = busSeq.map(c => ({ c, bay: -1, arr0: 0, arr1: 0, dep0: Infinity, dep1: Infinity, seats: [] }));
  for (let i = 0; i < 3; i++) { buses[i].bay = i; buses[i].arr0 = T0 - 1.2; buses[i].arr1 = T0 - .4; }
  let nextBus = 3; const bench = [0, 1, 2, 3, 4].map(() => ({ pi: null, freeAt: -1, at: 0 })); const evs = [];
  function fillBus(b) { let tt = b.arr1 + .1;
    for (let k = 0; k < bench.length && b.seats.length < 4; k++) { const s = bench[k]; if (s.pi === null) continue; const p = pax[s.pi]; if (p.c !== b.c) continue;
      tt = Math.max(tt, s.at + .05); p.segs.push({ t0: tt, t1: tt + .55, a: benchPos(k), b: doorPos(b.bay) }); p.board = tt + .55; b.seats.push(tt + .55); evs.push([tt + .55, 'pop']); bench[k] = { pi: null, freeAt: tt + .3, at: 0 }; tt += .18; }
    if (b.seats.length === 4) depart(b, Math.max(...b.seats) + .25); }
  function depart(b, t) { b.dep0 = t; b.dep1 = t + .8; evs.push([t, 'horn']); if (nextBus < buses.length) { const nb = buses[nextBus++]; nb.bay = b.bay; nb.arr0 = b.dep1 - .2; nb.arr1 = nb.arr0 + .8; evs.push([nb.arr0, 'whooshS']); fillBus(nb); } }
  let t = T0;
  for (let i = 0; i < q.length; i++) {
    const p = pax[i]; const from = qpos(0);
    const b = buses.find(b => b.bay >= 0 && b.dep0 === Infinity && b.seats.length < 4 && b.c === p.c);
    if (b) { const t1 = Math.max(t + .55, b.arr1 + .15); p.segs.push({ t0: t, t1, a: from, b: doorPos(b.bay) }); p.board = t1; b.seats.push(t1); evs.push([t1, 'pop']); if (b.seats.length === 4) depart(b, t1 + .25); }
    else { const k = bench.findIndex(s => s.pi === null && s.freeAt <= t + .3); if (k < 0) return null; p.segs.push({ t0: t, t1: t + .55, a: from, b: benchPos(k) }); bench[k] = { pi: i, freeAt: Infinity, at: t + .55 }; evs.push([t + .55, 'tick']); }
    for (let j = i + 1; j < q.length; j++) pax[j].segs.push({ t0: t + .05, t1: t + .33, a: qpos(j - i), b: qpos(j - i - 1) });
    t += step;
  }
  if (buses.some(b => b.dep0 === Infinity)) return null;
  const end = Math.max(...buses.map(b => b.dep1));
  evs.forEach(([tt, ty]) => ev(sceneT0 + tt, ty));
  return { pax, buses, end };
}
function drawPax(x, y, col, walk, sc = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc);
  ctx.fillStyle = 'rgba(0,0,0,.2)'; ctx.beginPath(); ctx.ellipse(0, 26, 14, 5, 0, 0, 7); ctx.fill();
  ctx.strokeStyle = shade(col, -0.2); ctx.lineWidth = 7; ctx.lineCap = 'round'; const sw = Math.sin(walk) * 6;
  ctx.beginPath(); ctx.moveTo(-4, 12); ctx.lineTo(-4 - sw, 25); ctx.moveTo(4, 12); ctx.lineTo(4 + sw, 25); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-9, -2); ctx.lineTo(-13 + sw * .6, 10); ctx.moveTo(9, -2); ctx.lineTo(13 - sw * .6, 10); ctx.stroke();
  ctx.fillStyle = col; rr(-10, -8, 20, 24, 9); ctx.fill();
  const g = ctx.createRadialGradient(-3, -22, 2, 0, -18, 12); g.addColorStop(0, shade(col, .45)); g.addColorStop(1, col); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, -18, 10, 0, 7); ctx.fill();
  ctx.restore();
}
function drawBus(x, y, col, seatsShown, bounce) {
  ctx.save(); ctx.translate(x, y); ctx.scale(1, 1 - bounce * .04);
  ctx.fillStyle = 'rgba(0,0,0,.25)'; rr(6, -36, 300, 86, 18); ctx.fill();
  const g = ctx.createLinearGradient(0, -43, 0, 43); g.addColorStop(0, shade(col, .2)); g.addColorStop(1, shade(col, -0.12)); ctx.fillStyle = g; rr(0, -43, 300, 86, 18); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.fillRect(8, 14, 284, 5);
  for (let k = 0; k < 4; k++) { const wx = 22 + k * 52; ctx.fillStyle = '#BDE6FF'; rr(wx, -32, 42, 34, 7); ctx.fill();
    if (k < seatsShown.length && seatsShown[k]) { ctx.save(); rr(wx, -32, 42, 34, 7); ctx.clip(); ctx.fillStyle = shade(col, -0.05); ctx.beginPath(); ctx.arc(wx + 21, -10, 9, 0, 7); ctx.fill(); rr(wx + 11, -2, 20, 12, 6); ctx.fill(); ctx.restore(); } }
  ctx.fillStyle = shade(col, -0.3); rr(232, -30, 20, 58, 5); ctx.fill();
  ctx.fillStyle = '#BDE6FF'; rr(258, -32, 36, 40, [6, 14, 6, 6]); ctx.fill(); ctx.fillStyle = '#F2C59B'; ctx.beginPath(); ctx.arc(276, -14, 7, 0, 7); ctx.fill(); ctx.fillStyle = '#1E3A8A'; ctx.fillRect(268, -24, 16, 5);
  ctx.fillStyle = '#FFF59D'; rr(292, 16, 8, 12, 3); ctx.fill();
  for (const wx of [62, 240]) { ctx.fillStyle = '#222'; ctx.beginPath(); ctx.arc(wx, 43, 15, 0, 7); ctx.fill(); ctx.fillStyle = '#AAA'; ctx.beginPath(); ctx.arc(wx, 43, 6, 0, 7); ctx.fill(); }
  ctx.restore();
}
function terminalGame(sceneT0) {
  const seqs = [['r', 'b', 'g', 'y']]; const wins = [[2.4, 13]];
  const levels = wins.map(([wa, wb], li) => { let L = null; for (let s = 500 + li * 1000; s < 1500 + li * 1000 && !L; s++) { EVENTS.length; const mark = EVENTS.length; L = simTerminal(s, seqs[li], wa + .7, .4, sceneT0); if (!L) EVENTS.length = mark; } L.wa = wa; L.wb = wb; L.num = 9 + li; FANFARES.push(sceneT0 + L.end + .3); return L; });
  return (w, h, t) => {
    const g = ctx.createLinearGradient(0, 0, 0, 130); g.addColorStop(0, '#8ED8FF'); g.addColorStop(1, '#C9EEFF'); ctx.fillStyle = g; ctx.fillRect(0, 0, w, 130);
    ctx.fillStyle = '#9CB8D6'; for (let i = 0; i < 7; i++) { const bh = 30 + (i * 37 % 50); ctx.fillRect(i * 66, 130 - bh, 52, bh); }
    ctx.fillStyle = '#4A4F5C'; ctx.fillRect(0, 118, w, 400);
    ctx.strokeStyle = 'rgba(255,255,255,.6)'; ctx.lineWidth = 4; ctx.setLineDash([24, 18]); for (let b = 0; b < 2; b++) { ctx.beginPath(); ctx.moveTo(0, bayY(b) + 61); ctx.lineTo(w, bayY(b) + 61); ctx.stroke(); } ctx.setLineDash([]);
    ctx.fillStyle = '#E8E1D0'; ctx.fillRect(0, 518, w, h - 518); ctx.fillStyle = '#FACC15'; ctx.fillRect(0, 518, w, 8);
    ctx.fillStyle = '#C9BFA8'; rr(30, 560, 380, 58, 16); ctx.fill();
    for (let k = 0; k < 5; k++) { const p = benchPos(k); ctx.fillStyle = '#B3A98F'; rr(p.x - 26, 592, 52, 18, 6); ctx.fill(); }
    ctx.strokeStyle = '#B0A58C'; ctx.lineWidth = 4; for (let r = 0; r < 3; r++) { const y = 736 + r * 62; ctx.beginPath(); ctx.moveTo(r % 2 ? 40 : 100, y); ctx.lineTo(r % 2 ? 340 : 400, y); ctx.stroke(); }
    const L = levelAt(levels, t); const lt = t;
    hudPill(w, 'LEVEL ' + L.num, 'rgba(0,0,0,.35)');
    for (let b = 0; b < 3; b++) { ctx.fillStyle = 'rgba(255,255,255,.12)'; rr(14, bayY(b) - 50, 40, 100, 10); ctx.fill(); text(String(b + 1), 34, bayY(b), { size: 30, font: 'Fredoka', weight: 700, shadow: false, alpha: .7 }); }
    L.buses.forEach(b => { if (b.bay < 0 || lt < b.arr0 || lt > b.dep1) return; let x = 70; if (lt < b.arr1) x = lerp(-340, 70, eOutCubic(seg(lt, b.arr0, b.arr1))); if (lt > b.dep0) x = lerp(70, 520, eInCubic(seg(lt, b.dep0, b.dep1)));
      const shown = b.seats.map(st => lt >= st); let bounce = 0; b.seats.forEach(st => { const d = lt - st; if (d > 0 && d < .25) bounce = Math.sin(d / .25 * Math.PI); });
      if (lt < L.wa) return; drawBus(x, bayY(b.bay), PAXC[b.c], shown, bounce);
      if (lt > b.dep0 - .25 && lt < b.dep0 + .6) { const pp = eOutBack(seg(lt, b.dep0 - .25, b.dep0)); ctx.save(); ctx.globalAlpha = 1 - seg(lt, b.dep0 + .3, b.dep0 + .6); ctx.translate(220, bayY(b.bay) - 52); ctx.scale(pp, pp); rr(-58, -22, 116, 44, 22); ctx.fillStyle = '#fff'; ctx.fill(); text('FULL!', 0, 1, { size: 30, color: PAXC[b.c], shadow: false }); ctx.restore(); } });
    L.pax.forEach(p => {
      if (lt >= p.board) return; let pos = p.start, moving = false;
      for (const s of p.segs) { if (lt >= s.t1) pos = s.b; else if (lt >= s.t0) { const e = eInOut((lt - s.t0) / (s.t1 - s.t0)); pos = { x: lerp(s.a.x, s.b.x, e), y: lerp(s.a.y, s.b.y, e) - Math.sin(e * Math.PI) * 10 }; moving = true; break; } else break; }
      const ap = seg(lt, L.wa + .1 + p.id * .015, L.wa + .45 + p.id * .015); if (ap <= 0) return;
      drawPax(pos.x, pos.y, PAXC[p.c], moving ? lt * 22 : 0, eOutBack(ap));
    });
    completeBanner(w, h, lt - (L.end + .3), '#7C4DFF', 91 + L.num);
  };
}

// ================= SCENES =================
const GAMES = {
  feather: { key: 'feather', name: 'Feather Pop', sub: 'Bird Sort Puzzle', c1: '#7FD3FF', c2: '#1565C0', accent: '#FFD54F', dark: '#0D3B66', shape: 'leaf', seed: 21,
    caps: [[3.0, 'Group the birds by kind'], [5.2, 'Four of a kind fly away!']], endT: 8.0, tag: 'No timers • No lives • Just relax', card: true },
  park: { key: 'park', name: 'Park Pop', sub: 'Car Colour Sort', c1: '#FF7A6B', c2: '#A3122A', accent: '#FFE14D', dark: '#5A0B16', shape: 'rect', seed: 33,
    caps: [[3.0, 'Unjam the car park'], [4.9, 'Park them by colour — POP!']], endT: 8.0, tag: 'Perfect for a quick break' },
  nut: { key: 'nut', name: 'Nut Pop', sub: 'Bolts & Colors', c1: '#2A4BB8', c2: '#0A1030', accent: '#FFC107', dark: '#0A1030', shape: 'hex', seed: 45,
    caps: [[3.0, 'Lift & stack the nuts'], [5.0, 'Every bolt clicks — POP!']], endT: 8.0, tag: 'No timers. No stress.', card: true },
  terminal: { key: 'terminal', name: 'Terminal Tangle', sub: 'Bus Sorting & Parking', c1: '#9A6BFF', c2: '#3A1A8C', accent: '#FFD600', dark: '#24104F', shape: 'circle', seed: 57,
    caps: [[3.0, 'Match passengers by colour'], [5.4, 'Clear the blocked routes']], endT: 8.0, tag: 'Busy, bright & brain-teasing' },
};
const ORDER = ['feather', 'park', 'nut', 'terminal'];
const SCENES = [
  { id: 'intro', t0: 0, t1: 5.5 },
  { id: 'feather', t0: 5.5, t1: 17.5 },
  { id: 'park', t0: 17.5, t1: 29.5 },
  { id: 'nut', t0: 29.5, t1: 41.5 },
  { id: 'terminal', t0: 41.5, t1: 53.5 },
  { id: 'outro', t0: 53.5, t1: 60 },
];
const SIMS = {}; const FANFARES = [];

function chip(str, x, y, p, accent) {
  if (p <= 0) return; const e = eOutBack(clamp(p)); const size = 40; const tw = measure(str, size, 'Fredoka', 600);
  ctx.save(); ctx.globalAlpha *= clamp(p * 2.5); ctx.translate(x + (1 - eOutCubic(clamp(p))) * -90, y); ctx.scale(e, e);
  rr(0, -34, tw + 108, 68, 34); ctx.fillStyle = 'rgba(255,255,255,.16)'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.stroke();
  ctx.beginPath(); ctx.arc(34, 0, 22, 0, 7); ctx.fillStyle = accent; ctx.fill();
  ctx.strokeStyle = '#1b1b2e'; ctx.lineWidth = 5; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(24, 1); ctx.lineTo(31, 8); ctx.lineTo(44, -7); ctx.stroke();
  text(str, 72, 2, { size, font: 'Fredoka', weight: 600, align: 'left', shadow: true });
  ctx.restore();
}

function gameScene(id, u) {
  const g = GAMES[id];
  bgGrad(g.c1, g.c2, u, { seed: g.seed, shape: g.shape, rx: W * .5, ry: H * .45 });
  const pMove = eInOut(seg(u, 1.6, 2.4));
  // ---- icon ----
  const ip = seg(u, 0.15, 0.75);
  const iconS = lerp(400, 210, pMove) * eOutBack(ip);
  const ix = lerp(960, 275, pMove), iy = lerp(395, 262, pMove);
  if (pMove < 1 && ip > 0) { ctx.save(); ctx.globalAlpha = (1 - pMove) * .55 * ip; const rg = ctx.createRadialGradient(ix, iy, 0, ix, iy, 560); rg.addColorStop(0, 'rgba(255,255,255,.95)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H); ctx.restore(); }
  const wob = Math.sin(u * 2.2) * 0.035 * (1 - pMove) + Math.sin(u * 1.4) * .015 * pMove;
  drawIcon(g.key, ix, iy + Math.sin(u * 1.6) * 5 * pMove, iconS, { rot: (1 - eOutCubic(ip)) * -0.6 + wob, shine: seg(u, .8, 1.6), glow: (1 - pMove) * .8 });
  burst(960, 395, u - .5, g.seed + 1, [g.accent, '#fff', ...RAINBOW.slice(0, 3)], { n: 46, spd: 820, life: 1.5, size: 17 });
  // ---- title ----
  const tSizeA = 128, tSizeB = 92; const tSize = lerp(tSizeA, tSizeB, pMove);
  const twB = measure(g.name, tSizeB); const tx = lerp(960, 160 + twB / 2, pMove), ty = lerp(705, 470, pMove);
  if (u < 1.6) popText(g.name, 960, 705, u - .45, { size: tSizeA, stroke: g.dark, sw: 16, stagger: .03 });
  else text(g.name, tx, ty, { size: tSize, stroke: g.dark, sw: lerp(16, 13, pMove) });
  // ---- subtitle pill ----
  const sp = eOutBack(seg(u, .9, 1.3)); if (sp > 0) { const ss = lerp(46, 38, pMove); const sw = measure(g.sub, ss, 'Fredoka', 700) + 56; const sx = lerp(960, 160 + sw / 2, pMove), sy = lerp(825, 562, pMove);
    ctx.save(); ctx.translate(sx, sy); ctx.scale(sp, sp); rr(-sw / 2, -ss * .78, sw, ss * 1.56, ss * .78); ctx.fillStyle = g.accent; ctx.shadowColor = 'rgba(0,0,0,.3)'; ctx.shadowBlur = 18; ctx.shadowOffsetY = 6; ctx.fill(); ctx.shadowColor = 'transparent';
    text(g.sub, 0, 2, { size: ss, font: 'Fredoka', weight: 700, color: g.dark, shadow: false }); ctx.restore(); }
  // ---- caption chips ----
  const endP = eInOut(seg(u, g.endT, g.endT + .6));
  ctx.save(); ctx.globalAlpha = 1 - endP; ctx.translate(-endP * 160, 0);
  g.caps.forEach(([ct, str], i) => chip(str, 160, 680 + i * 88, (u - ct) / .5, g.accent));
  ctx.restore();
  // ---- end card ----
  if (u > g.endT) { const e1 = seg(u, g.endT + .3, g.endT + .9); popText(g.tag, 160, 690, u - (g.endT + .2), { size: 50, font: 'Fredoka', weight: 700, align: 'left', stagger: .02, stroke: g.dark, sw: 8 });
    const bp = eOutBack(e1); if (bp > 0) { ctx.save(); ctx.translate(160 + 200, 815); ctx.scale(bp * (1 + Math.sin(u * 4) * .015), bp * (1 + Math.sin(u * 4) * .015)); drawBadge(0, 0, 400); ctx.restore(); }
    text('Search “' + g.name + '” on the App Store', 160, 925, { size: 32, font: 'Fredoka', weight: 500, align: 'left', alpha: seg(u, g.endT + .9, g.endT + 1.4) }); }
  // ---- phone ----
  const php = seg(u, 1.8, 2.8); if (php > 0) {
    const px = lerp(2350, 1420, eOutBack(php)), py = 540 + Math.sin(u * 1.1) * 8; const rot = (1 - eOutCubic(php)) * .25 + Math.sin(u * .8) * .012;
    // glow behind phone
    ctx.save(); ctx.globalAlpha = .5 * php; const rg = ctx.createRadialGradient(px, py, 50, px, py, 620); rg.addColorStop(0, 'rgba(255,255,255,.45)'); rg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = rg; ctx.fillRect(px - 700, 0, 1400, H); ctx.restore();
    if (g.card) { ctx.save(); ctx.translate(px, py); ctx.rotate(rot); const cw = 444, chh = 960;
      ctx.save(); ctx.shadowColor = 'rgba(0,0,0,.5)'; ctx.shadowBlur = 60; ctx.shadowOffsetY = 30; rr(-cw / 2, -chh / 2, cw, chh, 40); ctx.fillStyle = '#fff'; ctx.fill(); ctx.restore();
      ctx.save(); rr(-cw / 2, -chh / 2, cw, chh, 40); ctx.clip(); ctx.translate(-cw / 2, -chh / 2); SIMS[id](cw, chh, u); ctx.restore();
      ctx.lineWidth = 8; ctx.strokeStyle = 'rgba(255,255,255,.9)'; rr(-cw / 2, -chh / 2, cw, chh, 40); ctx.stroke(); ctx.restore(); }
    else drawPhone(px, py, 1.0, rot, (sw, sh) => SIMS[id](sw, sh, u));
  }
}

function introScene(t) {
  bgGrad('#3A1C8C', '#0B0A2E', t, { seed: 3, rayAlpha: .07, n: 34, multi: true, shape: 'star' });
  const z = 1 + eInCubic(seg(t, 4.5, 5.7)) * 1.2;
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
  const fl = 1 - seg(t, 0, .5); if (fl > 0) { ctx.fillStyle = `rgba(255,255,255,${fl * .6})`; ctx.fillRect(0, 0, W, H); }
  const outA = eInCubic(seg(t, 1.8, 2.2));
  if (outA < 1) { ctx.save(); ctx.globalAlpha = 1 - outA; ctx.translate(0, -outA * 140);
    popText('READY FOR MORE', W / 2, 410, t - 0.2, { size: 116, stroke: '#1B0F4A', sw: 16, stagger: .025 });
    popText('COLOUR?', W / 2, 600, t - 0.65, { size: 220, colors: RAINBOW, stroke: '#1B0F4A', sw: 22, stagger: .05 });
    ctx.restore(); }
  burst(W / 2, 600, t - 1.05, 11, RAINBOW, { n: 70, spd: 1000, life: 1.5, size: 20 });
  if (t > 1.9) {
    popText('4 BRAND-NEW PUZZLE GAMES', W / 2, 200, t - 2.0, { size: 86, stagger: .018, stroke: '#1B0F4A', sw: 13 });
    ORDER.forEach((k, i) => { const g = GAMES[k]; const ti = 2.3 + i * .22; const p = seg(t, ti, ti + .65); if (p <= 0) return;
      const x = W / 2 + (i - 1.5) * 410; let y = lerp(-300, 560, eOutBounce(p)); y += Math.sin(t * 2.4 + i) * 7 * seg(t, ti + .65, ti + 1.2);
      drawIcon(g.key, x, y, 300, { rot: (1 - p) * .6 * (i % 2 ? 1 : -1), shine: seg(t, 3.4 + i * .12, 4.1 + i * .12) });
      text(g.name, x, 770, { size: 46, font: 'Fredoka', weight: 700, alpha: seg(t, ti + .35, ti + .7) });
      burst(x, 560, t - (ti + .45), 20 + i, [g.accent, '#fff'], { n: 22, spd: 520, life: 1, size: 12 }); });
  }
  ctx.restore();
  // GRKN Studios logo: pops in top-centre, then tucks into the top-left corner
  const lp = seg(t, 0.1, 0.65); if (lp > 0) {
    const mv = eInOut(seg(t, 1.7, 2.3)); const hgt = lerp(210, 140, mv) * eOutBack(lp);
    const lx = lerp(W / 2, 150, mv), ly = lerp(170, 105, mv) + Math.sin(t * 2.5) * 3;
    const img = IMG.logo; const wd = hgt * img.width / img.height;
    ctx.save(); ctx.globalAlpha = 1 - seg(t, 4.5, 5.0); ctx.translate(lx, ly); ctx.rotate((1 - eOutCubic(lp)) * -.3);
    ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8; ctx.drawImage(img, -wd / 2, -hgt / 2, wd, hgt); ctx.restore();
  }
}

function outroScene(t) {
  bgGrad('#3A1C8C', '#0B0A2E', t + 30, { seed: 5, rayAlpha: .07, n: 34, multi: true, shape: 'star' });
  const times = [0.3, 0.6, 0.9, 1.2];
  ORDER.forEach((k, i) => { const g = GAMES[k]; const p = seg(t, times[i], times[i] + .55); if (p <= 0) return; const x = W / 2 + (i - 1.5) * 410, y = 430 + Math.sin(t * 2 + i) * 6;
    drawIcon(g.key, x, y, 270 * eOutBack(p), { rot: (1 - p) * .5 * (i % 2 ? 1 : -1), glow: .35 * Math.max(0, 1 - (t - times[i]) / 1.2), shine: seg(t, 3.6 + i * .12, 4.4 + i * .12) });
    text(g.name, x, 612, { size: 44, font: 'Fredoka', weight: 700, alpha: seg(t, times[i] + .3, times[i] + .7) });
    burst(x, 430, t - (times[i] + .3), 60 + i, [g.accent, '#fff', ...RAINBOW], { n: 26, spd: 560, life: 1.1, size: 13 }); });
  popText('4 GAMES • 1 COLOURFUL WORLD', W / 2, 165, t - 0.8, { size: 84, stagger: .02, colors: RAINBOW, stroke: '#1B0F4A', sw: 13 });
  const pb = seg(t, 2.9, 3.5); if (pb > 0) { const s = eOutBack(pb) * (1 + Math.sin(t * 4) * .02); ctx.save(); ctx.translate(W / 2, 800); ctx.scale(s, s); drawBadge(0, 0, 470); ctx.restore(); burst(W / 2, 800, t - 3.1, 99, RAINBOW, { n: 60, spd: 900, life: 1.6, size: 16 }); }
  popText('Start sorting today!', W / 2, 960, t - 4.0, { size: 64, font: 'Fredoka', weight: 700, stagger: .02, color: '#FFD54F', stroke: '#1B0F4A', sw: 9 });
  const f = seg(t, 6.0, 6.5); if (f > 0) { ctx.fillStyle = `rgba(0,0,0,${f})`; ctx.fillRect(0, 0, W, H); }
}

function drawScene(s, u) {
  if (s.id === 'intro') introScene(u); else if (s.id === 'outro') outroScene(u); else gameScene(s.id, u);
}
function renderFrame(T) {
  let idx = SCENES.findIndex(s => T >= s.t0 && T < s.t1); if (idx < 0) idx = SCENES.length - 1; const s = SCENES[idx]; const u = T - s.t0;
  const wipe = .85;
  ctx.save();
  if (idx > 0 && u < wipe) {
    const ps = SCENES[idx - 1]; drawScene(ps, T - ps.t0);
    const p = eInOut(u / wipe); const r = p * 1150; const acc = GAMES[s.id] ? GAMES[s.id].accent : '#FFD54F';
    ctx.save(); ctx.beginPath(); ctx.arc(W / 2, H / 2, r, 0, 7); ctx.clip(); drawScene(s, u); ctx.restore();
    ctx.save(); ctx.lineWidth = 50 * (1 - p) + 6; ctx.strokeStyle = acc; ctx.beginPath(); ctx.arc(W / 2, H / 2, r, 0, 7); ctx.stroke(); ctx.lineWidth = 8; ctx.strokeStyle = '#fff'; ctx.beginPath(); ctx.arc(W / 2, H / 2, r + 30 * (1 - p), 0, 7); ctx.stroke(); ctx.restore();
  } else drawScene(s, u);
  ctx.restore();
}

// ---------- scene-level sound events ----------
function sceneEvents() {
  ev(0.0, 'boom'); ev(0.3, 'riser'); ev(1.1, 'sparkle');
  for (let i = 0; i < 4; i++) ev(2.3 + i * .22 + .45, 'pop');
  ev(1.9, 'swoosh'); ev(4.2, 'riser');
  SCENES.forEach((s, i) => {
    if (i > 0) ev(s.t0, 'whoosh');
    const g = GAMES[s.id]; if (!g) return;
    ev(s.t0 + .5, 'sparkle'); ev(s.t0 + .9, 'pop'); ev(s.t0 + 1.6, 'swoosh'); ev(s.t0 + 1.9, 'whooshS');
    g.caps.forEach(([ct]) => ev(s.t0 + ct, 'tick'));
    ev(s.t0 + g.endT + .4, 'sparkle');
  });
  const o = 53.5; [0.3, 0.6, 0.9, 1.2].forEach(x => ev(o + x + .3, 'pop')); ev(o + 3.1, 'sparkle'); ev(o + 3.0, 'boom');
}

// ---------- boot ----------
(async () => {
  await Promise.all(['feather', 'park', 'nut', 'terminal', 'badge', 'logo', ...['pp', 'fp', 'np', 'tt'].flatMap(p => [0, 1, 2, 3, 4, 5].map(i => p + '/s' + i))].map(k => new Promise(r => { const i = new Image(); i.onload = () => { IMG[k.replace('/s', '')] = i; r(); }; i.src = k + (k.includes('/s') ? '.jpg' : '.png'); })));
  await document.fonts.load('800 100px Baloo'); await document.fonts.load('700 100px Fredoka'); await document.fonts.load('500 100px Fredoka');
  SIMS.feather = parkShots(5.5, 'fp', false, -1); SIMS.park = parkShots(17.5); SIMS.nut = parkShots(29.5, 'np', false, 1); SIMS.terminal = parkShots(41.5, 'tt', true, -1);
  FANFARES.forEach(x => ev(x, 'fanfare'));
  sceneEvents();
  // level-complete chimes
  window.renderFrame = renderFrame; window.getEvents = () => EVENTS.slice().sort((a, b) => a.t - b.t);
  window.READY = true;
})().catch(e => { window.ERR = String(e && e.stack || e); });
