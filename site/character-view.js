import { Quaternion, Vector3 } from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

// The MotionBuilder BVH mapping and limb alignment used by Creator's CMUBVHMotion.
const JOINTS = [
  ["pelvis", "Hips"],
  ["spine_01", "LowerBack"], ["spine_02", "Spine"], ["spine_03", "Spine1"],
  ["neck_01", "Neck1"], ["head", "Head"],
  ["clavicle_l", "LeftShoulder"],
  ["upperarm_l", "LeftArm", "lowerarm_l"], ["lowerarm_l", "LeftForeArm", "hand_l"], ["hand_l", "LeftHand"],
  ["clavicle_r", "RightShoulder"],
  ["upperarm_r", "RightArm", "lowerarm_r"], ["lowerarm_r", "RightForeArm", "hand_r"], ["hand_r", "RightHand"],
  ["thigh_l", "LeftUpLeg", "calf_l"], ["calf_l", "LeftLeg", "foot_l"],
  ["foot_l", "LeftFoot", "ball_l"], ["ball_l", "LeftToeBase"],
  ["thigh_r", "RightUpLeg", "calf_r"], ["calf_r", "RightLeg", "foot_r"],
  ["foot_r", "RightFoot", "ball_r"], ["ball_r", "RightToeBase"],
];
const SOURCE_NAMES = new Map(JOINTS.map(([target, source]) => [target, source]));
const METERS_PER_CMU_UNIT = 0.0254 / 0.45;

export async function loadCharacter(skeleton, reference, signal) {
  const response = await fetch(new URL("./model.glb", import.meta.url), { signal });
  if (!response.ok) throw new Error(`Character request failed (${response.status})`);
  const { scene } = await new GLTFLoader().parseAsync(await response.arrayBuffer(), "");
  const meshes = [];
  scene.traverse((object) => {
    if (object.isSkinnedMesh) meshes.push(object);
  });
  const dispose = () => {
    scene.removeFromParent();
    for (const mesh of meshes) {
      mesh.geometry.dispose();
      mesh.material.dispose();
      mesh.skeleton.dispose();
    }
  };

  try {
    signal.throwIfAborted();
    const [mesh] = meshes;
    if (!mesh || meshes.length !== 1) throw new Error("Expected one skinned character mesh");
    mesh.frustumCulled = false;
    const { skinIndex, skinWeight, joints_1: extraJoints, weights_1: extraWeights } = mesh.geometry.attributes;
    if (extraJoints && extraWeights) {
      for (let vertex = 0; vertex < skinWeight.count; vertex++) {
        const extra = [0, 1, 2, 3].map((i) => extraWeights.getComponent(vertex, i));
        const extraTotal = extra.reduce((sum, weight) => sum + weight, 0);
        if (!extraTotal) continue;
        // GLTFLoader normalizes the primary four on load. Recover their share
        // of the original unit sum before comparing them with the second set.
        const influences = [];
        for (let slot = 0; slot < 4; slot++) {
          influences.push([skinIndex.getComponent(vertex, slot), skinWeight.getComponent(vertex, slot) * (1 - extraTotal)]);
          influences.push([extraJoints.getComponent(vertex, slot), extra[slot]]);
        }
        const strongest = influences.sort((a, b) => b[1] - a[1]).slice(0, 4);
        const sum = strongest.reduce((total, [, weight]) => total + weight, 0);
        for (let slot = 0; slot < 4; slot++) {
          const [joint, weight] = strongest[slot];
          skinIndex.setComponent(vertex, slot, joint);
          skinWeight.setComponent(vertex, slot, weight / sum);
        }
      }
      mesh.geometry.deleteAttribute("joints_1");
      mesh.geometry.deleteAttribute("weights_1");
    }

    scene.updateMatrixWorld(true);
    const targetByName = new Map(mesh.skeleton.bones.map((bone) => [bone.name, bone]));
    const sourceByName = new Map(skeleton.bones.map((bone) => [bone.name, bone]));
    const bindings = new Map();
    const targetDirection = new Vector3();
    const childPosition = new Vector3();
    const sourceDirection = new Vector3();
    const calibration = new Quaternion();
    for (const [targetName, sourceName, childName] of JOINTS) {
      const bone = targetByName.get(targetName);
      const source = sourceByName.get(sourceName);
      if (!bone || !source) throw new Error(`Missing character mapping for ${targetName}`);
      const rotation = bone.getWorldQuaternion(new Quaternion());
      if (childName) {
        const child = targetByName.get(childName);
        child.getWorldPosition(childPosition);
        bone.getWorldPosition(targetDirection);
        targetDirection.subVectors(childPosition, targetDirection);
        sourceDirection.subVectors(reference.get(SOURCE_NAMES.get(childName)).position, reference.get(sourceName).position);
        calibration.setFromUnitVectors(targetDirection.normalize(), sourceDirection.normalize());
        rotation.premultiply(calibration);
      }
      bindings.set(bone, { source, inverseReference: reference.get(sourceName).rotation.clone().invert(), rotation });
    }
    const joints = [];
    scene.traverse((bone) => {
      if (bone.isBone) joints.push(bone);
    });
    const worldRotations = new Map(joints.map((bone) => [bone, new Quaternion()]));
    const identity = new Quaternion();
    const parentInverse = new Quaternion();
    const sourceRotation = new Quaternion();
    const pelvis = targetByName.get("pelvis");
    const pelvisTranslation = pelvis.position.clone();
    const heightOffset = new Vector3();
    const toeHeight = Math.min(...["ball_l", "ball_r"].map((name) => targetByName.get(name).getWorldPosition(childPosition).y));
    const sourceFeet = Math.min(...["LeftToeBase", "RightToeBase"].map((name) => reference.get(name).position.y));
    const sourceLegHeight = reference.get("Hips").position.y - sourceFeet;
    const hips = sourceByName.get("Hips");

    return {
      scene,
      pelvis,
      dispose,
      poseAt(sourceScale) {
        scene.position.set(hips.position.x * sourceScale, 0, hips.position.z * sourceScale);
        heightOffset.set(0, (hips.position.y - sourceLegHeight) * METERS_PER_CMU_UNIT - toeHeight, 0);
        for (const bone of joints) {
          const parent = worldRotations.get(bone.parent) ?? identity;
          const binding = bindings.get(bone);
          if (binding) {
            binding.source.getWorldQuaternion(sourceRotation);
            parentInverse.copy(parent).invert();
            bone.quaternion.copy(parentInverse).multiply(sourceRotation)
              .multiply(binding.inverseReference).multiply(binding.rotation).normalize();
          }
          if (bone === pelvis) {
            bone.position.copy(pelvisTranslation).add(heightOffset.applyQuaternion(parentInverse));
          }
          worldRotations.get(bone).multiplyQuaternions(parent, bone.quaternion);
        }
      },
    };
  } catch (error) {
    dispose();
    throw error;
  }
}
