import * as THREE from "three";
import { BVHLoader } from "three/addons/loaders/BVHLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

export function showSkeleton(text, motion, { viewport, play, scrubber, timestamp, reset, onUnavailable }) {
  const { calibrationFrames, firstUsableFrame, frameCount, frameInterval } = motion;
  const { skeleton, clip } = new BVHLoader().parse(text);
  const lastFrame = frameCount - 1;
  const duration = lastFrame * frameInterval;
  if (Math.abs(clip.duration - (duration + calibrationFrames * frameInterval)) > frameInterval / 2) {
    throw new Error("BVH duration differs from catalog timing");
  }

  const root = skeleton.bones[0];
  const point = new THREE.Vector3();
  const bounds = new THREE.Box3();
  root.updateMatrixWorld(true);
  for (const bone of skeleton.bones) {
    bounds.expandByPoint(bone.getWorldPosition(point));
  }
  const height = bounds.max.y - bounds.min.y;
  if (!Number.isFinite(height) || height <= 0) throw new Error("BVH has an invalid skeleton");

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x17221e);
  const rig = new THREE.Group();
  rig.scale.setScalar(1.7 / height);
  rig.add(root);
  scene.add(rig);
  const lines = new THREE.SkeletonHelper(root);
  lines.setColors(new THREE.Color(0xc8f382), new THREE.Color(0x8ee4df));
  scene.add(lines);
  const floor = new THREE.GridHelper(30, 30, 0x566b61, 0x31413a);
  scene.add(floor);

  const mix = new THREE.AnimationMixer(root);
  const pose = mix.clipAction(clip).setLoop(THREE.LoopOnce, 0).play();
  pose.paused = true;
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  const canvas = renderer.domElement;
  canvas.setAttribute("aria-label", "3D source skeleton. Drag to orbit and scroll to zoom.");
  canvas.tabIndex = 0;
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  viewport.append(canvas);
  const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 60);
  const orbit = new OrbitControls(camera, canvas);
  orbit.minDistance = 1;
  orbit.maxDistance = 12;
  orbit.enablePan = false;
  const cameraOffset = new THREE.Vector3(2.3, 1.15, 3.1);
  const previousTarget = new THREE.Vector3();
  const targetShift = new THREE.Vector3();
  const firstTime = (firstUsableFrame - 1) * frameInterval;
  let time = firstTime;
  let previousTick;
  let playing = false;

  const render = () => renderer.render(scene, camera);
  const showPose = () => {
    pose.time = Math.min(clip.duration, time + calibrationFrames * frameInterval);
    mix.update(0);
    root.getWorldPosition(point);
    // Follow travel with the camera while leaving the captured motion in world space.
    point.y = Math.max(point.y, 0.8);
    targetShift.subVectors(point, previousTarget);
    orbit.target.add(targetShift);
    camera.position.add(targetShift);
    previousTarget.copy(point);
    floor.position.set(Math.round(point.x), 0, Math.round(point.z));
    scrubber.value = Math.round(time / frameInterval);
    timestamp.textContent = `${time.toFixed(2)} / ${duration.toFixed(2)} s`;
    scrubber.setAttribute("aria-valuetext", `${time.toFixed(2)} seconds`);
  };
  const resetView = () => {
    orbit.target.copy(previousTarget);
    camera.position.copy(orbit.target).add(cameraOffset);
    orbit.update();
    render();
  };
  const resize = () => {
    const { clientWidth, clientHeight } = viewport;
    if (!clientWidth || !clientHeight) return;
    renderer.setSize(clientWidth, clientHeight, false);
    camera.aspect = clientWidth / clientHeight;
    camera.updateProjectionMatrix();
    render();
  };
  const animate = (now) => {
    if (previousTick !== undefined) {
      time += (now - previousTick) / 1000;
      if (time > duration) {
        const loopDuration = duration - firstTime + frameInterval;
        time = Math.min(duration, firstTime + (time - firstTime) % loopDuration);
      }
    }
    previousTick = now;
    showPose();
    render();
  };
  const togglePlay = () => {
    playing = !playing;
    previousTick = undefined;
    play.textContent = playing ? "Pause" : "Play";
    renderer.setAnimationLoop(playing ? animate : null);
  };
  const seek = () => {
    time = scrubber.valueAsNumber * frameInterval;
    previousTick = undefined;
    showPose();
    render();
  };

  scrubber.min = firstUsableFrame - 1;
  scrubber.max = lastFrame;
  play.textContent = "Play";
  showPose();
  resetView();
  resize();
  const sizeObserver = new ResizeObserver(resize);
  sizeObserver.observe(viewport);
  play.addEventListener("click", togglePlay);
  scrubber.addEventListener("input", seek);
  reset.addEventListener("click", resetView);
  orbit.addEventListener("change", render);
  canvas.addEventListener("webglcontextlost", onUnavailable);

  return () => {
    sizeObserver.disconnect();
    renderer.setAnimationLoop(null);
    play.removeEventListener("click", togglePlay);
    scrubber.removeEventListener("input", seek);
    reset.removeEventListener("click", resetView);
    orbit.removeEventListener("change", render);
    canvas.removeEventListener("webglcontextlost", onUnavailable);
    orbit.dispose();
    mix.stopAllAction();
    mix.uncacheRoot(root);
    lines.dispose();
    floor.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
    canvas.remove();
  };
}
