/* ═══════════════════════════════════════════════════════════
   SIH26082 · ClusterAir · Unified Dashboard JavaScript
   Powers all pages: topbar, animations, map, counters
   Author: Aditya Tanzal | Reg: 12410040 | Roll: 15
   ═══════════════════════════════════════════════════════════ */

'use strict';

// ── Station data ────────────────────────────────────────────
const STATIONS = [
  { id:1,  name:"Anand Vihar",          city:"Delhi",      lat:28.6469, lon:77.3152, zone:"Traffic-Industrial",  cluster:1, pm25:312, aqi:435 },
  { id:2,  name:"RK Puram",             city:"Delhi",      lat:28.5640, lon:77.1855, zone:"Residential",         cluster:0, pm25:138, aqi:264 },
  { id:3,  name:"Punjabi Bagh",         city:"Delhi",      lat:28.6745, lon:77.1296, zone:"Residential-Traffic", cluster:0, pm25:155, aqi:287 },
  { id:4,  name:"Dwarka Sector 8",      city:"Delhi",      lat:28.5795, lon:77.0601, zone:"Residential",         cluster:0, pm25:118, aqi:238 },
  { id:5,  name:"Nehru Nagar",          city:"Delhi",      lat:28.5669, lon:77.2536, zone:"Industrial",          cluster:1, pm25:298, aqi:418 },
  { id:6,  name:"Okhla Phase 2",        city:"Delhi",      lat:28.5305, lon:77.2729, zone:"Industrial",          cluster:1, pm25:287, aqi:406 },
  { id:7,  name:"Noida Sector 62",      city:"Noida",      lat:28.6254, lon:77.3650, zone:"IT-Residential",      cluster:0, pm25:122, aqi:245 },
  { id:8,  name:"Noida Sector 125",     city:"Noida",      lat:28.5386, lon:77.3252, zone:"Mixed",               cluster:0, pm25:140, aqi:270 },
  { id:9,  name:"Ghaziabad Loni",       city:"Ghaziabad",  lat:28.7464, lon:77.2862, zone:"Industrial",          cluster:1, pm25:335, aqi:460 },
  { id:10, name:"Ghaziabad Vasundhra", city:"Ghaziabad",   lat:28.6615, lon:77.3612, zone:"Residential",         cluster:0, pm25:148, aqi:278 },
  { id:11, name:"Faridabad Sector 16", city:"Faridabad",   lat:28.4089, lon:77.3178, zone:"Industrial",          cluster:1, pm25:308, aqi:428 },
  { id:12, name:"Faridabad NIT",       city:"Faridabad",   lat:28.3837, lon:77.3090, zone:"Residential",         cluster:0, pm25:132, aqi:257 },
  { id:13, name:"Gurugram Sector 51",  city:"Gurugram",    lat:28.4595, lon:77.0266, zone:"IT-Commercial",       cluster:0, pm25:126, aqi:249 },
  { id:14, name:"Gurugram Manesar",    city:"Gurugram",    lat:28.3590, lon:76.9399, zone:"Industrial",          cluster:1, pm25:318, aqi:441 },
  { id:15, name:"Sonepat Town",        city:"Sonepat",     lat:28.9931, lon:77.0151, zone:"Mixed",               cluster:0, pm25:144, aqi:273 },
  { id:16, name:"Bahadurgarh",         city:"Bahadurgarh", lat:28.6942, lon:76.9211, zone:"Industrial",          cluster:1, pm25:305, aqi:424 },
  { id:17, name:"Ballabhgarh",         city:"Faridabad",   lat:28.3407, lon:77.3176, zone:"Residential",         cluster:0, pm25:130, aqi:253 },
  { id:18, name:"Greater Noida",       city:"Greater Noida",lat:28.4744, lon:77.5040, zone:"Mixed",              cluster:0, pm25:135, aqi:261 },
];

const C_COLORS = ['#E74C3C','#9B59B6'];
const C_NAMES  = ['Cluster 0 – Broad NCR Zone','Cluster 1 – Winter Severe Hotspot'];

// ════════════════════════════════════════════════════════════
// TOPBAR: scroll effect + hamburger
// ════════════════════════════════════════════════════════════
function initTopbar() {
  const topbar    = document.getElementById('topbar');
  const hamburger = document.getElementById('hamburger');
  const mainNav   = document.getElementById('mainNav');
  if (!topbar) return;

  window.addEventListener('scroll', () => {
    topbar.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });

  if (hamburger && mainNav) {
    hamburger.addEventListener('click', () => {
      mainNav.classList.toggle('open');
      const spans = hamburger.querySelectorAll('span');
      const isOpen = mainNav.classList.contains('open');
      spans[0].style.transform = isOpen ? 'rotate(45deg) translate(5px,5px)' : '';
      spans[1].style.opacity   = isOpen ? '0' : '1';
      spans[2].style.transform = isOpen ? 'rotate(-45deg) translate(5px,-5px)' : '';
    });
    // Close nav when link clicked
    mainNav.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => { mainNav.classList.remove('open'); });
    });
  }
}

// ════════════════════════════════════════════════════════════
// COUNTER ANIMATION
// ════════════════════════════════════════════════════════════
function animateCounters() {
  const els = document.querySelectorAll('[data-count],[data-decimal]');
  if (!els.length) return;

  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;

      if (el.dataset.decimal) {
        // Float counter (e.g., Silhouette 0.702)
        const target  = parseFloat(el.dataset.decimal);
        const dur     = 2000;
        const start   = performance.now();
        const tick = t => {
          const p = Math.min((t - start) / dur, 1);
          const e = 1 - Math.pow(1 - p, 3);
          el.textContent = (target * e).toFixed(3);
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      } else {
        // Integer counter
        const target  = parseInt(el.dataset.count);
        const dur     = 1800;
        const start   = performance.now();
        const tick = t => {
          const p = Math.min((t - start) / dur, 1);
          const e = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * e).toLocaleString();
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }
      obs.unobserve(el);
    });
  }, { threshold: 0.5 });

  els.forEach(el => obs.observe(el));
}

// ════════════════════════════════════════════════════════════
// CANVAS PARTICLE BACKGROUND
// ════════════════════════════════════════════════════════════
function initParticles() {
  const container = document.getElementById('heroParticles');
  if (!container) return;

  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;';
  container.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  let W, H, particles = [];

  const resize = () => {
    W = canvas.width  = container.offsetWidth;
    H = canvas.height = container.offsetHeight;
  };
  resize();
  window.addEventListener('resize', resize, { passive: true });

  for (let i = 0; i < 70; i++) {
    particles.push({
      x:  Math.random() * 1200,
      y:  Math.random() * 800,
      r:  Math.random() * 1.8 + 0.4,
      dx: (Math.random() - 0.5) * 0.35,
      dy: (Math.random() - 0.5) * 0.35,
      a:  Math.random() * 0.5 + 0.1,
      c:  Math.random() > 0.55 ? '#3b82f6' : '#8b5cf6',
    });
  }

  const draw = () => {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      p.x += p.dx; p.y += p.dy;
      if (p.x < 0 || p.x > W) p.dx *= -1;
      if (p.y < 0 || p.y > H) p.dy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.c;
      ctx.globalAlpha = p.a;
      ctx.fill();
    });
    // Lines
    ctx.globalAlpha = 1;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d  = Math.sqrt(dx*dx + dy*dy);
        if (d < 90) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(59,130,246,${0.08*(1-d/90)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  };
  draw();
}

// ════════════════════════════════════════════════════════════
// SCROLL REVEAL
// ════════════════════════════════════════════════════════════
function initScrollReveal() {
  const selectors = '.reveal,.reveal-left,.reveal-right,.reveal-img';
  const els = document.querySelectorAll(selectors);

  const obs = new IntersectionObserver(entries => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => entry.target.classList.add('visible'), i * 60);
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

  els.forEach(el => obs.observe(el));
}

// ════════════════════════════════════════════════════════════
// METRIC BAR ANIMATION
// ════════════════════════════════════════════════════════════
function initMetricBars() {
  const bars = document.querySelectorAll('.mc-fill, .feat-fill, .mr-bar');
  if (!bars.length) return;

  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const w  = el.style.width;
        el.style.width = '0';
        setTimeout(() => { el.style.width = w; }, 150);
        obs.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  bars.forEach(b => obs.observe(b));
}

// ════════════════════════════════════════════════════════════
// SVG STATION MAP (used on both index.html and map.html)
// ════════════════════════════════════════════════════════════
function initStationMap() {
  const container = document.getElementById('station-map');
  if (!container) return;

  const LAT_MIN = 28.28, LAT_MAX = 29.08;
  const LON_MIN = 76.82, LON_MAX = 77.58;
  const W = container.offsetWidth || 800;
  const H = 500;

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.style.cssText = 'width:100%;height:100%;display:block;';
  container.appendChild(svg);

  const tooltip = document.getElementById('mapTooltip') ||
    (() => { const t = document.createElement('div'); t.className='map-tooltip'; t.id='mapTooltip'; container.appendChild(t); return t; })();

  const toX = lon => ((lon - LON_MIN)/(LON_MAX - LON_MIN)) * W;
  const toY = lat => H - ((lat - LAT_MIN)/(LAT_MAX - LAT_MIN)) * H;

  // Grid background
  const defs = document.createElementNS(SVG_NS,'defs');
  const pat  = document.createElementNS(SVG_NS,'pattern');
  pat.setAttribute('id','grid-pat');
  pat.setAttribute('width','50');pat.setAttribute('height','50');
  pat.setAttribute('patternUnits','userSpaceOnUse');
  const gLine = document.createElementNS(SVG_NS,'path');
  gLine.setAttribute('d','M 50 0 L 0 0 0 50');
  gLine.setAttribute('fill','none');
  gLine.setAttribute('stroke','rgba(59,130,246,0.06)');
  gLine.setAttribute('stroke-width','1');
  pat.appendChild(gLine);
  defs.appendChild(pat);
  svg.appendChild(defs);

  const bgRect = document.createElementNS(SVG_NS,'rect');
  bgRect.setAttribute('width',W);bgRect.setAttribute('height',H);
  bgRect.setAttribute('fill','url(#grid-pat)');
  svg.appendChild(bgRect);

  // City labels
  const cities = [
    { name:'NEW DELHI', lat:28.614, lon:77.209 },
    { name:'NOIDA',     lat:28.535, lon:77.395 },
    { name:'GHAZIABAD', lat:28.670, lon:77.433 },
    { name:'GURUGRAM',  lat:28.420, lon:77.020 },
    { name:'FARIDABAD', lat:28.380, lon:77.310 },
    { name:'SONEPAT',   lat:29.000, lon:77.010 },
  ];
  cities.forEach(c => {
    const el = document.createElementNS(SVG_NS,'text');
    el.setAttribute('x', toX(c.lon)); el.setAttribute('y', toY(c.lat));
    el.setAttribute('text-anchor','middle');
    el.setAttribute('fill','rgba(255,255,255,0.12)');
    el.setAttribute('font-size','11');
    el.setAttribute('font-family','Space Grotesk, sans-serif');
    el.setAttribute('font-weight','600');
    el.textContent = c.name;
    svg.appendChild(el);
  });

  // Delhi boundary circle (rough)
  const delhiCX = toX(77.209), delhiCY = toY(28.614);
  const delBound = document.createElementNS(SVG_NS,'circle');
  delBound.setAttribute('cx',delhiCX);delBound.setAttribute('cy',delhiCY);
  delBound.setAttribute('r','90');
  delBound.setAttribute('fill','none');
  delBound.setAttribute('stroke','rgba(255,255,255,0.04)');
  delBound.setAttribute('stroke-width','1');
  delBound.setAttribute('stroke-dasharray','6,4');
  svg.appendChild(delBound);

  // Station dots
  STATIONS.forEach(st => {
    const x = toX(st.lon), y = toY(st.lat);
    const color = C_COLORS[st.cluster];

    // Pulse animation ring
    const ring = document.createElementNS(SVG_NS,'circle');
    ring.setAttribute('cx',x);ring.setAttribute('cy',y);ring.setAttribute('r','16');
    ring.setAttribute('fill','none');ring.setAttribute('stroke',color);
    ring.setAttribute('stroke-width','1');ring.setAttribute('opacity','0.25');
    svg.appendChild(ring);

    // Cluster zone indicator (large translucent)
    const zone = document.createElementNS(SVG_NS,'circle');
    zone.setAttribute('cx',x);zone.setAttribute('cy',y);zone.setAttribute('r','22');
    zone.setAttribute('fill',color);zone.setAttribute('opacity','0.07');
    svg.appendChild(zone);

    // Main dot
    const dot = document.createElementNS(SVG_NS,'circle');
    dot.setAttribute('cx',x);dot.setAttribute('cy',y);dot.setAttribute('r','8');
    dot.setAttribute('fill',color);dot.setAttribute('stroke','rgba(255,255,255,0.4)');
    dot.setAttribute('stroke-width','2');
    dot.style.cursor = 'pointer';
    dot.style.transition = 'r 0.2s';
    svg.appendChild(dot);

    // Station number
    const num = document.createElementNS(SVG_NS,'text');
    num.setAttribute('x',x);num.setAttribute('y',y+4);
    num.setAttribute('text-anchor','middle');
    num.setAttribute('fill','#fff');num.setAttribute('font-size','8');
    num.setAttribute('font-weight','700');num.setAttribute('pointer-events','none');
    num.textContent = st.id;
    svg.appendChild(num);

    // Hover events
    dot.addEventListener('mouseenter', e => {
      dot.setAttribute('r','12');
      ring.setAttribute('opacity','0.5');
      tooltip.style.display = 'block';
      tooltip.innerHTML = `
        <strong style="color:${color};display:block;margin-bottom:4px">${st.name}</strong>
        <span style="color:#94a3c0">City: ${st.city}</span><br/>
        <span style="color:#94a3c0">Zone: ${st.zone}</span><br/>
        <span style="color:${color};font-weight:700">${C_NAMES[st.cluster]}</span><br/>
        <span style="color:#94a3c0;font-size:11px">PM2.5: ${st.pm25} μg/m³ | AQI: ${st.aqi}</span>
      `;
    });
    dot.addEventListener('mousemove', e => {
      const rect = container.getBoundingClientRect();
      tooltip.style.left = Math.min(e.clientX - rect.left + 14, W - 220) + 'px';
      tooltip.style.top  = (e.clientY - rect.top - 10) + 'px';
    });
    dot.addEventListener('mouseleave', () => {
      dot.setAttribute('r','8');
      ring.setAttribute('opacity','0.25');
      tooltip.style.display = 'none';
    });
  });

  // Legend
  const legY = H - 36;
  [0,1].forEach((c,i) => {
    const lx = 20 + i * 220;
    const lcirc = document.createElementNS(SVG_NS,'circle');
    lcirc.setAttribute('cx',lx);lcirc.setAttribute('cy',legY);lcirc.setAttribute('r','6');
    lcirc.setAttribute('fill',C_COLORS[c]);
    svg.appendChild(lcirc);
    const ltxt = document.createElementNS(SVG_NS,'text');
    ltxt.setAttribute('x',lx+12);ltxt.setAttribute('y',legY+4);
    ltxt.setAttribute('fill','rgba(255,255,255,0.5)');ltxt.setAttribute('font-size','11');
    ltxt.textContent = C_NAMES[c];
    svg.appendChild(ltxt);
  });

  // Title
  const title = document.createElementNS(SVG_NS,'text');
  title.setAttribute('x','10');title.setAttribute('y','18');
  title.setAttribute('fill','rgba(255,255,255,0.2)');
  title.setAttribute('font-size','11');title.setAttribute('font-family','Space Grotesk,sans-serif');
  title.textContent = 'Delhi NCR CAAQMS Monitoring Stations · K-Means Cluster Assignments';
  svg.appendChild(title);
}

// ════════════════════════════════════════════════════════════
// STATION TABLE (map.html)
// ════════════════════════════════════════════════════════════
function initStationTable() {
  const tbody = document.getElementById('stationTableBody');
  if (!tbody) return;

  STATIONS.forEach(st => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${st.id}</td>
      <td><strong>${st.name}</strong></td>
      <td>${st.city}</td>
      <td>${st.zone}</td>
      <td>${st.lat}°N</td>
      <td>${st.lon}°E</td>
      <td>${st.cluster === 0
        ? '<span class="badge-c0">Cluster 0</span>'
        : '<span class="badge-c1">Cluster 1</span>'
      }</td>
    `;
    tbody.appendChild(tr);
  });
}

// ════════════════════════════════════════════════════════════
// SMOOTH SCROLL for hero anchor
// ════════════════════════════════════════════════════════════
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

// ════════════════════════════════════════════════════════════
// ACTIVE NAV HIGHLIGHT (on scroll)
// ════════════════════════════════════════════════════════════
function initNavHighlight() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-item');
  if (!sections.length) return;

  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        navLinks.forEach(l => {
          const href = l.getAttribute('href');
          if (href && href.includes('#' + e.target.id)) {
            l.classList.add('active');
          } else if (!l.classList.contains('active') && href && href.includes('#')) {
            // only remove if it's an anchor link
          }
        });
      }
    });
  }, { threshold: 0.4 });
  sections.forEach(s => obs.observe(s));
}

// ════════════════════════════════════════════════════════════
// PIPELINE STEP INTERACTION
// ════════════════════════════════════════════════════════════
function initPipelineSteps() {
  const steps = document.querySelectorAll('.pipe-step');
  if (!steps.length) return;

  steps.forEach(step => {
    step.addEventListener('click', () => {
      steps.forEach(s => s.classList.remove('active'));
      step.classList.add('active');
    });
  });
}

// ════════════════════════════════════════════════════════════
// CHART IMAGE LIGHTBOX (simple full-screen view)
// ════════════════════════════════════════════════════════════
function initLightbox() {
  const lightbox = document.createElement('div');
  lightbox.id = 'lightbox';
  lightbox.style.cssText = `
    display:none;position:fixed;inset:0;z-index:9999;
    background:rgba(0,0,0,0.92);cursor:zoom-out;
    align-items:center;justify-content:center;
  `;
  const lbImg = document.createElement('img');
  lbImg.style.cssText = 'max-width:92vw;max-height:90vh;border-radius:12px;box-shadow:0 24px 80px rgba(0,0,0,0.8)';
  lightbox.appendChild(lbImg);
  document.body.appendChild(lightbox);

  document.querySelectorAll('.cs-main img, .cs-thumb img, .glass-card img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', () => {
      lbImg.src = img.src;
      lightbox.style.display = 'flex';
    });
  });
  lightbox.addEventListener('click', () => { lightbox.style.display = 'none'; });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') lightbox.style.display = 'none';
  });
}

// ════════════════════════════════════════════════════════════
// INITIALISE ALL
// ════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  initTopbar();
  initParticles();
  animateCounters();
  initScrollReveal();
  initMetricBars();
  initStationMap();
  initStationTable();
  initSmoothScroll();
  initNavHighlight();
  initPipelineSteps();
  initLightbox();

  console.log('%c SIH26082 · Delhi NCR ClusterAir ', 'background:linear-gradient(135deg,#3b82f6,#8b5cf6);color:#fff;font-size:14px;font-weight:bold;padding:6px 14px;border-radius:6px');
  console.log('%c Author: Aditya Tanzal | Reg: 12410040 | Roll: 15', 'color:#8b5cf6;font-size:12px');
});
