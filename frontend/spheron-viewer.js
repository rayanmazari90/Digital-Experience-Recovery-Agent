/**
 * spheron-viewer.js
 * Extreme high-contrast lighting to ensure deep shadows at all times.
 * Removed front lights, darkened base material, and using strong side/rim lighting.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/* ─────────────────────────────────────────────────────────────
   HELPER — create a renderer for a given canvas + size
───────────────────────────────────────────────────────────── */
function makeRenderer(canvas, size) {
  const r = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  r.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  r.setSize(size, size);
  r.outputColorSpace = THREE.SRGBColorSpace;
  r.toneMapping = THREE.ACESFilmicToneMapping;
  r.toneMappingExposure = 1.8;
  return r;
}

function makeCamera() {
  const cam = new THREE.PerspectiveCamera(38, 1, 0.01, 100);
  cam.position.set(0, 0, 3.6);
  return cam;
}

/* ─────────────────────────────────────────────────────────────
   SCENE 1: OVERLAY (Large)
   Deep shadows: zero ambient, strong side lighting only.
───────────────────────────────────────────────────────────── */
const overlayScene = new THREE.Scene();

// Zero ambient light ensures absolute black shadows in unlit areas
overlayScene.add(new THREE.AmbientLight(0xffffff, 0.02));

// Right side: Sharp white rim light (slightly behind)
const overlayKey = new THREE.DirectionalLight(0xffffff, 6.0);
overlayKey.position.set(4, 1, -2);
overlayScene.add(overlayKey);

// Left side: Intense electric blue
const overlayFill = new THREE.DirectionalLight(0x0A84FF, 7.0);
overlayFill.position.set(-4, -1, 1);
overlayScene.add(overlayFill);

// Top/Front-Left: Subtle cyan to catch top edges
const overlayTop = new THREE.DirectionalLight(0x5AC8FA, 2.0);
overlayTop.position.set(-1, 5, 2);
overlayScene.add(overlayTop);

/* ─────────────────────────────────────────────────────────────
   SCENE 2: LOGO (Small)
   Even higher contrast for readability at 52px
───────────────────────────────────────────────────────────── */
const logoScene = new THREE.Scene();
logoScene.add(new THREE.AmbientLight(0xffffff, 0.05));

const logoBlue = new THREE.DirectionalLight(0x0A84FF, 10.0);
logoBlue.position.set(-4, 0, 1);
logoScene.add(logoBlue);

const logoWhite = new THREE.DirectionalLight(0xffffff, 8.0);
logoWhite.position.set(4, 2, -1);
logoScene.add(logoWhite);

const logoRim = new THREE.DirectionalLight(0xBF5AF2, 4.0);
logoRim.position.set(0, -4, 1);
logoScene.add(logoRim);

/* ─────────────────────────────────────────────────────────────
   RENDERERS
───────────────────────────────────────────────────────────── */
const logoCanvas    = document.getElementById('logoCanvas');
const overlayCanvas = document.getElementById('spheronCanvas');

const logoRenderer    = logoCanvas    ? makeRenderer(logoCanvas,    52)  : null;
const overlayRenderer = overlayCanvas ? makeRenderer(overlayCanvas, 110) : null;

const logoCamera    = makeCamera();
const overlayCamera = makeCamera();

/* ─────────────────────────────────────────────────────────────
   LOAD MODEL
───────────────────────────────────────────────────────────── */
let overlayModel = null;
let logoModel    = null;
let _mixerOverlay = null;
let _mixerLogo    = null;

new GLTFLoader().load(
  './spheron.glb',
  (gltf) => {
    const baseModel = gltf.scene;

    // Darken the base material so it doesn't blow out to white!
    // It will rely entirely on the lights to paint it white/blue.
    baseModel.traverse((node) => {
      if (node.isMesh) {
        const mats = Array.isArray(node.material) ? node.material : [node.material];
        mats.forEach((mat) => {
          mat.color?.setHex(0x555555); // Medium-dark gray base
          mat.roughness  = 0.5;        // Matte enough to show shadows
          mat.metalness  = 0.2;
          mat.emissive?.setHex(0x000000);
          mat.needsUpdate = true;
        });
      }
    });

    // Center & scale
    const box    = new THREE.Box3().setFromObject(baseModel);
    const center = box.getCenter(new THREE.Vector3());
    const size   = box.getSize(new THREE.Vector3());
    const s      = 1.8 / Math.max(size.x, size.y, size.z);
    baseModel.scale.setScalar(s);
    baseModel.position.sub(center.multiplyScalar(s));

    // OVERLAY MODEL
    overlayModel = baseModel;
    overlayScene.add(overlayModel);

    // LOGO MODEL (Clone)
    logoModel = baseModel.clone();
    logoScene.add(logoModel);

    // Animations
    if (gltf.animations?.length) {
      _mixerOverlay = new THREE.AnimationMixer(overlayModel);
      _mixerLogo    = new THREE.AnimationMixer(logoModel);
      gltf.animations.forEach((clip) => {
        _mixerOverlay.clipAction(clip).play();
        _mixerLogo.clipAction(clip).play();
      });
    }
  },
  undefined,
  (err) => console.error('spheron load error:', err),
);

/* ─────────────────────────────────────────────────────────────
   RENDER LOOP
───────────────────────────────────────────────────────────── */
const clock = new THREE.Clock();

(function animate() {
  requestAnimationFrame(animate);
  const dt = clock.getDelta();

  // Slow, steady rotation
  if (overlayModel) overlayModel.rotation.y += 0.003;
  if (logoModel)    logoModel.rotation.y += 0.002;

  if (_mixerOverlay) _mixerOverlay.update(dt);
  if (_mixerLogo)    _mixerLogo.update(dt);

  if (logoRenderer)    logoRenderer.render(logoScene, logoCamera);
  if (overlayRenderer) overlayRenderer.render(overlayScene, overlayCamera);
})();

/* ─────────────────────────────────────────────────────────────
   SYNC voice state from hidden #voiceBubble → visible #voicePod
   app.js sets data-voice-state on #voiceBubble;
   we mirror it to #voicePod so CSS transitions work.
───────────────────────────────────────────────────────────── */
const voiceBubble = document.getElementById('voiceBubble');
const voicePod    = document.getElementById('voicePod');

if (voiceBubble && voicePod) {
  new MutationObserver(() => {
    const state = voiceBubble.dataset.voiceState || 'idle';
    voicePod.dataset.voiceState = state;
  }).observe(voiceBubble, { attributes: true, attributeFilter: ['data-voice-state'] });
}

