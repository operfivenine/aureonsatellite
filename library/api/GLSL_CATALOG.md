# GLSL Catalog — Stable API 1.1 and Opt-in Experimental Modules

Signatures/structures/dependencies are preserved from the native module index. Import `aurs.standard` through the descriptor; do not paste the resolved library into the shader. Read each module source for its exact formula and edge cases. A function here does not automatically create a render pass.

## core.math

Clamping, scalar remapping, rotations, smooth distance blending and repetition.

**Status:** stable implementation / compatibility. **Dependencies:** none.

[Exact implementation](glsl/core.math.glsl).

- `float aur_sat(float x)` — stable API 1.1.
- `vec2 aur_sat(vec2 x)` — stable API 1.1.
- `vec3 aur_sat(vec3 x)` — stable API 1.1.
- `float aur_remap(float x, float a, float b, float c, float d)` — stable API 1.1.
- `mat2 aur_rot2(float a)` — stable API 1.1.
- `float aur_smin(float a, float b, float k)` — stable API 1.1.
- `float aur_repeat1(float x, float spacing)` — stable API 1.1.
- `vec2 aur_repeat2(vec2 p, vec2 spacing)` — stable API 1.1.


## core.noise

Deterministic hashes, noise and fractal fields for procedural variation.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.noise.glsl).

- `float aur_hash11(float p)` — stable API 1.1.
- `float aur_hash21(vec2 p)` — stable API 1.1.
- `vec2 aur_hash22(vec2 p)` — stable API 1.1.
- `float aur_hash31(vec3 p)` — stable API 1.1.
- `float aur_noise2(vec2 p)` — stable API 1.1.
- `float aur_noise3(vec3 p)` — stable API 1.1.
- `float aur_fbm2(vec2 p)` — stable API 1.1.
- `float aur_fbm3(vec3 p)` — stable API 1.1.


## core.sdf

Signed-distance primitives and constructive field operations. The author performs ray traversal.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.sdf.glsl).

- `float aur_sdSphere(vec3 p, float r)` — stable API 1.1.
- `float aur_sdBox(vec3 p, vec3 b)` — stable API 1.1.
- `float aur_sdRoundBox(vec3 p, vec3 b, float r)` — stable API 1.1.
- `float aur_sdCylinderY(vec3 p, vec2 h)` — stable API 1.1.
- `float aur_sdCapsule(vec3 p, vec3 a, vec3 b, float r)` — stable API 1.1.
- `float aur_sdTorus(vec3 p, vec2 t)` — stable API 1.1.
- `float aur_opUnion(float a, float b)` — stable API 1.1.
- `float aur_opIntersect(float a, float b)` — stable API 1.1.
- `float aur_opSubtract(float a, float b)` — stable API 1.1.
- `float aur_opSmoothUnion(float a, float b, float k)` — stable API 1.1.


## core.lighting

Local lighting terms, attenuation and material-independent response approximations.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.lighting.glsl).

- `float aur_diffuse(vec3 n, vec3 l)` — stable API 1.1.
- `float aur_fresnel(vec3 n, vec3 v, float power)` — stable API 1.1.
- `float aur_rim(vec3 n, vec3 v, float width, float power)` — stable API 1.1.
- `float aur_specular(vec3 n, vec3 l, vec3 v, float roughness)` — stable API 1.1.
- `float aur_attenuation(float distanceToLight, float radius)` — stable API 1.1.
- `float aur_shadowTerm(float currentShadow, float fieldDistance, float travel, float softness)` — stable API 1.1.
- `vec3 aur_lit(vec3 baseColor, vec3 n, vec3 l, vec3 v, vec3 lightColor, float diffuseGain, float specularGain, float roughness)` — stable API 1.1.


## core.environment

Distance/height fog and depth fades; these helpers do not add geometry or passes.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.environment.glsl).

- `float aur_fogExp(float distanceValue, float density)` — stable API 1.1.
- `float aur_fogExp2(float distanceValue, float density)` — stable API 1.1.
- `float aur_depthFade(float distanceValue, float nearDistance, float farDistance)` — stable API 1.1.
- `float aur_heightFog(float worldY, float baseHeight, float falloff)` — stable API 1.1.
- `vec3 aur_applyFog(vec3 color, vec3 fogColor, float fogAmount)` — stable API 1.1.


## core.color

Palette, saturation, contrast and tone-mapping transforms.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.color.glsl).

- `vec3 aur_palette(float t, vec3 a, vec3 b, vec3 c, vec3 d)` — stable API 1.1.
- `vec3 aur_tonemapReinhard(vec3 c)` — stable API 1.1.
- `vec3 aur_tonemapAces(vec3 x)` — stable API 1.1.
- `vec3 aur_saturation(vec3 c, float amount)` — stable API 1.1.
- `vec3 aur_contrast(vec3 c, float amount)` — stable API 1.1.


## core.composition

Glow/masks/compositing and vignette calculations inside the fragment shader.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.composition.glsl).

- `float aur_glow(float signedDistance, float width, float intensity)` — stable API 1.1.
- `float aur_lineMask(float distanceValue, float width, float softness)` — stable API 1.1.
- `float aur_vignette(vec2 centeredUv, float strength)` — stable API 1.1.
- `vec3 aur_screen(vec3 base, vec3 layer)` — stable API 1.1.


## core.camera

Camera orientation and ray construction from authored camera inputs.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.camera.glsl).

- `mat3 aur_lookAt(vec3 ro, vec3 target, float roll)` — stable API 1.1.
- `vec3 aur_cameraRay(vec2 centeredUv, float aspect, vec3 ro, vec3 target, float fovDeg, float roll)` — stable API 1.1.


## core.geometry

Point transforms and procedural geometry utilities; these are not mesh-host calls.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.sdf.

[Exact implementation](glsl/core.geometry.glsl).

- `vec3 aur_rotateX(vec3 p, float a)` — stable API 1.1.
- `vec3 aur_rotateY(vec3 p, float a)` — stable API 1.1.
- `vec3 aur_rotateZ(vec3 p, float a)` — stable API 1.1.
- `vec3 aur_twistY(vec3 p, float amount)` — stable API 1.1.
- `vec3 aur_bendX(vec3 p, float amount)` — stable API 1.1.
- `vec3 aur_repeat3(vec3 p, vec3 spacing)` — stable API 1.1.
- `vec2 aur_polarRepeat(vec2 p, float count)` — stable API 1.1.
- `float aur_opOnion(float d, float thickness)` — stable API 1.1.
- `float aur_opRound(float d, float radius)` — stable API 1.1.
- `float aur_opChamferUnion(float a, float b, float radius)` — stable API 1.1.
- `float aur_sdPlane(vec3 p, vec3 normal, float offset)` — stable API 1.1.


## core.materials

Material descriptors and lighting response calculations; no implicit texture/FBO allocation.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.lighting.

[Exact implementation](glsl/core.materials.glsl).

```glsl
struct AurMaterial { vec3 baseColor; vec3 emission; float roughness; float metalness; float ao; };
```

- `AurMaterial aur_material(vec3 baseColor, float roughness, float metalness, vec3 emission, float ao)` — stable API 1.1.
- `vec3 aur_materialVariation(vec3 baseColor, float variation, float amount)` — stable API 1.1.
- `vec3 aur_shadeMaterial(AurMaterial m, vec3 n, vec3 l, vec3 v, vec3 lightColor, float lightStrength, float shadow)` — stable API 1.1.
- `vec3 aur_addRim(vec3 color, vec3 rimColor, vec3 n, vec3 v, float power, float strength)` — stable API 1.1.


## core.scene_lighting

Trusted GLSL helpers for scene lighting. See the linked implementation for field semantics and exact formulas.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.lighting, core.materials.

[Exact implementation](glsl/core.scene_lighting.glsl).

```glsl
struct AurLightRig { vec3 ambientColor; float ambientStrength; vec3 keyDirection; vec3 keyColor; float keyIntensity; vec3 fillDirection; vec3 fillColor; float fillIntensity; vec3 rimDirection; vec3 rimColor; float rimIntensity; };
```

- `AurLightRig aur_lightRig( vec3 ambientColor, float ambientStrength, vec3 keyDirection, vec3 keyColor, float keyIntensity, vec3 fillDirection, vec3 fillColor, float fillIntensity, vec3 rimDirection, vec3 rimColor, float rimIntensity)` — stable API 1.1.
- `vec3 aur_fresnelSchlick(float cosTheta, vec3 f0)` — stable API 1.1.
- `float aur_distributionGGX(vec3 n, vec3 h, float roughness)` — stable API 1.1.
- `float aur_geometrySchlickGGX(float ndv, float roughness)` — stable API 1.1.
- `float aur_geometrySmith(vec3 n, vec3 v, vec3 l, float roughness)` — stable API 1.1.
- `vec3 aur_brdfLight(AurMaterial m, vec3 n, vec3 v, vec3 l, vec3 lightColor, float intensity, float shadow)` — stable API 1.1.
- `vec3 aur_ambientMaterial(AurMaterial m, vec3 ambientColor, float strength)` — stable API 1.1.
- `vec3 aur_rimLight(vec3 n, vec3 v, vec3 lightDirection, vec3 color, float intensity)` — stable API 1.1.
- `vec3 aur_shadeLightRig(AurMaterial m, vec3 n, vec3 v, AurLightRig rig, float keyShadow)` — stable API 1.1.
- `vec3 aur_pointLight(AurMaterial m, vec3 n, vec3 v, vec3 p, vec3 lightPosition, vec3 lightColor, float intensity, float radius, float shadow)` — stable API 1.1.
- `float aur_spotCone(vec3 fromLightToPoint, vec3 lightForward, float innerCos, float outerCos)` — stable API 1.1.
- `vec3 aur_spotLight(AurMaterial m, vec3 n, vec3 v, vec3 p, vec3 lightPosition, vec3 lightForward, vec3 lightColor, float intensity, float radius, float innerCos, float outerCos, float shadow)` — stable API 1.1.
- `vec3 aur_emissiveSpill(vec3 p, vec3 sourcePosition, vec3 sourceColor, float intensity, float radius)` — stable API 1.1.


## core.atmosphere

Trusted GLSL helpers for atmosphere. See the linked implementation for field semantics and exact formulas.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.noise, core.environment, core.composition.

[Exact implementation](glsl/core.atmosphere.glsl).

- `float aur_phaseHG(float cosTheta, float g)` — stable API 1.1.
- `float aur_layerBand(float worldY, float centerY, float halfWidth, float feather)` — stable API 1.1.
- `float aur_heightFogDensity(vec3 p, float baseHeight, float density, float falloff)` — stable API 1.1.
- `float aur_hazeDensity(float travel, float startDistance, float endDistance, float density)` — stable API 1.1.
- `float aur_segmentDistance(vec3 p, vec3 a, vec3 b)` — stable API 1.1.
- `float aur_beamTube(vec3 p, vec3 a, vec3 b, float radius, float feather)` — stable API 1.1.
- `float aur_beamCone(vec3 p, vec3 origin, vec3 direction, float lengthValue, float radiusNear, float radiusFar, float feather)` — stable API 1.1.
- `vec3 aur_hash33(vec3 p)` — stable API 1.1.
- `float aur_dustField(vec3 p, float cellSize, float particleRadius, float density, float seed)` — stable API 1.1.
- `float aur_fogNoise(vec3 p, float scale, float amount)` — stable API 1.1.
- `void aur_scatterStep(inout vec3 scatter, inout float transmittance, vec3 sourceColor, float density, float stepLength)` — implementation helper.
- `float aur_softBloomMask(float luminanceValue, float threshold, float knee)` — stable API 1.1.
- `vec3 aur_bloomContribution(vec3 emissionColor, float mask, float strength)` — stable API 1.1.


## core.motion

Trusted GLSL helpers for motion. See the linked implementation for field semantics and exact formulas.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.geometry.

[Exact implementation](glsl/core.motion.glsl).

- `float aur_motionSine(float t, float speed, float phase)` — stable API 1.1.
- `float aur_motionCycle(float t, float speed, float phase)` — stable API 1.1.
- `float aur_motionTriangle(float t, float speed, float phase)` — stable API 1.1.
- `float aur_motionPingPong(float t, float speed, float phase)` — stable API 1.1.
- `float aur_motionSmoothCycle(float t, float speed, float phase)` — stable API 1.1.
- `float aur_sequenceWindow(float t, float period, float start, float duration, float feather)` — stable API 1.1.
- `float aur_easeInOut(float x)` — stable API 1.1.
- `float aur_easeSmoother(float x)` — stable API 1.1.
- `vec3 aur_pivotRotateX(vec3 p, vec3 pivot, float angle)` — stable API 1.1.
- `vec3 aur_pivotRotateY(vec3 p, vec3 pivot, float angle)` — stable API 1.1.
- `vec3 aur_pivotRotateZ(vec3 p, vec3 pivot, float angle)` — stable API 1.1.
- `vec3 aur_slideTransform(vec3 p, vec3 direction, float distanceValue, float amount)` — stable API 1.1.
- `float aur_secondarySway(float t, float speed, float primary, float lag, float amplitude)` — stable API 1.1.
- `float aur_followMix(float currentLike, float targetLike, float amount)` — stable API 1.1.
- `float aur_eventActive(vec4 e)` — stable API 1.1.
- `float aur_eventProgress(vec4 e)` — stable API 1.1.
- `float aur_eventStrength(vec4 e)` — stable API 1.1.
- `float aur_eventSeed(vec4 e)` — stable API 1.1.
- `float aur_eventGroup(vec4 e)` — stable API 1.1.
- `float aur_eventEaseOut(vec4 e, float powerValue)` — stable API 1.1.
- `float aur_eventPulse(vec4 e, float attackFraction, float decayPower)` — stable API 1.1.
- `float aur_eventRing(vec4 e, float phase, float width)` — stable API 1.1.
- `float aur_eventVariant(vec4 e, float count)` — stable API 1.1.
- `float aur_eventSigned(vec4 e)` — stable API 1.1.


## core.presentation

Trusted GLSL helpers for presentation. See the linked implementation for field semantics and exact formulas.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.noise, core.color, core.composition, core.atmosphere.

[Exact implementation](glsl/core.presentation.glsl).

```glsl
struct AurPresentation { float exposure; float contrast; float saturation; float vignette; float bloomThreshold; float bloomKnee; float bloomStrength; float grain; float dither; vec3 tint; };
```

- `float aur_luminance(vec3 c)` — stable API 1.1.
- `float aur_qualityLevel()` — stable API 1.1.
- `float aur_qualitySelect(float lowValue, float mediumValue, float highValue)` — stable API 1.1.
- `vec3 aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue)` — stable API 1.1.
- `float aur_qualitySelect(float lowValue, float mediumValue, float highValue, float extremeValue)` — stable API 1.1.
- `vec3 aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue, vec3 extremeValue)` — stable API 1.1.
- `float aur_detailScale(float lowValue, float mediumValue, float highValue)` — stable API 1.1.
- `float aur_aaCoverage(float signedDistance)` — stable API 1.1.
- `float aur_aaLine(float signedDistance, float halfWidth)` — stable API 1.1.
- `vec2 aur_subpixelOffset(int sampleIndex)` — stable API 1.1.
- `vec3 aur_exposure(vec3 color, float stops)` — stable API 1.1.
- `vec3 aur_liftGammaGain(vec3 color, vec3 lift, vec3 gammaValue, vec3 gain)` — stable API 1.1.
- `vec3 aur_grade(vec3 color, float contrastValue, float saturationValue, vec3 tint)` — stable API 1.1.
- `vec3 aur_softClip(vec3 color, float shoulder)` — stable API 1.1.
- `float aur_filmGrain(vec2 pixel, float timeValue, float amount)` — stable API 1.1.
- `vec3 aur_dither(vec3 color, vec2 pixel, float amount)` — stable API 1.1.
- `AurPresentation aur_presentation(float exposureValue, float contrastValue, float saturationValue, float vignetteValue, float bloomThreshold, float bloomKnee, float bloomStrength, float grainValue, float ditherValue, vec3 tintValue)` — stable API 1.1.
- `vec3 aur_present(vec3 hdrColor, vec2 centeredUv, vec2 fragCoord, float timeValue, AurPresentation p)` — stable API 1.1.


## core.object

Trusted GLSL helpers for object. See the linked implementation for field semantics and exact formulas.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.noise, core.sdf, core.geometry, core.lighting, core.materials.

[Exact implementation](glsl/core.object.glsl).



## core.world

Trusted GLSL helpers for world. See the linked implementation for field semantics and exact formulas.

**Status:** stable implementation / compatibility. **Dependencies:** core.math, core.noise, core.sdf, core.lighting, core.environment, core.color, core.composition, core.camera.

[Exact implementation](glsl/core.world.glsl).



## core.object_motion

Procedural poses and local/world point transforms; +Y-up and radian conventions apply.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.object_motion.glsl).

```glsl
struct AurPathSample { vec3 position; vec3 velocity; };
```

```glsl
struct AurObjectPose { vec3 position; mat3 rotation; float scale; };
```

- `vec3 aur_objectUnit(vec3 v, vec3 fallbackValue)` — stable API 1.1.
- `mat3 aur_objectFrame(vec3 forwardValue, vec3 upHint)` — stable API 1.1.
- `mat3 aur_objectEuler(vec3 angles)` — stable API 1.1.
- `AurObjectPose aur_objectPose(vec3 positionValue, vec3 angles, float scaleValue)` — stable API 1.1.
- `AurObjectPose aur_objectFollow(AurPathSample path, vec3 upHint, vec3 fallbackForward, float scaleValue)` — stable API 1.1.
- `vec3 aur_objectToLocal(AurObjectPose o,vec3 worldPosition)` — stable API 1.1.
- `vec3 aur_objectToWorld(AurObjectPose o,vec3 localPosition)` — stable API 1.1.
- `vec3 aur_objectNormal(AurObjectPose o,vec3 localNormal)` — stable API 1.1.
- `float aur_objectDistance(AurObjectPose o,float localDistance)` — stable API 1.1.
- `AurPathSample aur_pathLine(vec3 origin,vec3 velocity,float timeValue)` — stable API 1.1.
- `AurPathSample aur_pathOrbit(vec3 center,vec3 axis,float radius,float angularSpeed,float phase,float timeValue)` — stable API 1.1.
- `AurPathSample aur_pathShuttle(vec3 a,vec3 b,float period,float phase,float timeValue)` — stable API 1.1.
- `vec3 aur_shuttleHeading(vec3 a,vec3 b,vec3 upHint,float period,float phase,float timeValue,float turnFraction)` — stable API 1.1.


## core.attachments

Attach procedural parts/points to a parent pose within GLSL calculations.

**Status:** stable implementation / compatibility. **Dependencies:** core.object_motion.

[Exact implementation](glsl/core.attachments.glsl).

- `AurObjectPose aur_objectCompose(AurObjectPose parent, AurObjectPose child)` — stable API 1.1.
- `AurObjectPose aur_objectSocket(AurObjectPose parent,vec3 localPosition,vec3 localAngles)` — stable API 1.1.
- `vec3 aur_objectDirection(AurObjectPose pose,vec3 direction)` — stable API 1.1.
- `float aur_attachmentJet(vec3 worldPoint,AurObjectPose socket,float lengthValue,float radius,float timeValue,float strength)` — stable API 1.1.
- `float aur_attachmentBeacon(vec3 worldPoint,AurObjectPose socket,float radius,float timeValue,float frequency,float phase)` — stable API 1.1.


## core.instances

Deterministic procedural copy layouts; distinct from native GPU-instanced mesh graph nodes.

**Status:** stable implementation / compatibility. **Dependencies:** core.noise, core.object_motion.

[Exact implementation](glsl/core.instances.glsl).

```glsl
struct AurInstance { float seed; float phase; float speed; float scale; float gain; int band; };
```

- `AurInstance aur_instance(int index,float groupSeed,vec2 speedRange,vec2 scaleRange,vec2 gainRange)` — stable API 1.1.
- `float aur_instanceReaction(AurInstance instance,float bandValue,float broadValue,float broadMix)` — stable API 1.1.
- `vec3 aur_instanceRing(int index,int count,float radius,float phase)` — stable API 1.1.


## core.trails_lod

Procedural trail/LOD helpers; no persistent world-object history or automatic mesh simplification.

**Status:** stable implementation / compatibility. **Dependencies:** core.math.

[Exact implementation](glsl/core.trails_lod.glsl).

- `float aur_lodWeight(float distanceValue,float nearDistance,float farDistance)` — stable API 1.1.
- `float aur_trailFade(float age,float lifetime)` — stable API 1.1.
- `float aur_trailSegment(vec3 ro,vec3 rd,float depth,vec3 a,vec3 b,float radius)` — stable API 1.1.


## aurs.standard

Trusted GLSL helpers for standard. See the linked implementation for field semantics and exact formulas.

**Status:** stable implementation / compatibility. **Dependencies:** core.world, core.object, core.scene_lighting, core.atmosphere, core.motion, core.presentation, core.object_motion, core.attachments, core.instances, core.trails_lod.

[Exact implementation](glsl/aurs.standard.glsl).



## experimental.texture_materials

Interpret sampled texture channels as material parameters; authored samplers/resources remain required.

**Status:** experimental. **Dependencies:** core.materials.

[Exact implementation](glsl/experimental.texture_materials.glsl).

- `AurMaterial aur_textureMaterial(vec3 colorSample, vec3 ormSample, vec3 emissionSample, vec3 tint, float roughnessScale, float metalnessScale, float aoStrength, float emissionStrength)` — experimental.
- `vec3 aur_packORM(float occlusion, float roughness, float metalness)` — experimental.
- `vec2 aur_textureUV(vec2 uv, vec2 tiling, vec2 offset)` — experimental.


## experimental.normal_mapping

Decode and transform tangent-space normal samples; no silhouette/depth modification.

**Status:** experimental. **Dependencies:** none.

[Exact implementation](glsl/experimental.normal_mapping.glsl).

- `vec3 aur_decodeNormal(vec3 sampleValue, float strength, float greenSign)` — experimental.
- `vec3 aur_normalMap(vec3 geometricNormal, vec3 tangentU, vec3 tangentV, vec3 sampleValue, float strength, float greenSign)` — experimental.


## experimental.triplanar

Axis-projected sampling coordinates/weights and sample blending.

**Status:** experimental. **Dependencies:** experimental.normal_mapping.

[Exact implementation](glsl/experimental.triplanar.glsl).

```glsl
struct AurTriplanar { vec2 uvX; vec2 uvY; vec2 uvZ; vec3 weights; vec3 signs; vec3 normal; };
```

- `AurTriplanar aur_triplanar(vec3 position, vec3 normal, float scale, float sharpness)` — experimental.
- `vec3 aur_triplanarBlend(AurTriplanar p, vec3 x, vec3 y, vec3 z)` — experimental.
- `vec3 aur_triplanarNormal(AurTriplanar p, vec3 x, vec3 y, vec3 z, float strength, float greenSign)` — experimental.


## experimental.scene_lights

Scene-light descriptors, attachment/gain and material response; visibility is supplied by the author.

**Status:** experimental. **Dependencies:** core.scene_lighting, core.object_motion.

[Exact implementation](glsl/experimental.scene_lights.glsl).

```glsl
struct AurSceneLight { int kind; vec3 position; vec3 direction; vec3 color; float intensity; float radius; float innerCos; float outerCos; };
```

- `AurSceneLight aur_sceneDirectional(vec3 direction, vec3 color, float intensity)` — experimental.
- `AurSceneLight aur_scenePoint(vec3 position, vec3 color, float intensity, float radius)` — experimental.
- `AurSceneLight aur_sceneSpot(vec3 position, vec3 direction, vec3 color, float intensity, float radius, float innerDegrees, float outerDegrees)` — experimental.
- `AurSceneLight aur_sceneLightAttach(AurSceneLight l, AurObjectPose pose)` — experimental.
- `AurSceneLight aur_sceneLightGain(AurSceneLight l, float gain)` — experimental.
- `vec3 aur_sceneLightShade(AurSceneLight l, AurMaterial material, vec3 position, vec3 normal, vec3 viewDirection, float visibility)` — experimental.


## experimental.normal_filtering

Estimate normal variance and broaden roughness to reduce noisy specular response.

**Status:** experimental. **Dependencies:** experimental.normal_mapping, core.materials.

[Exact implementation](glsl/experimental.normal_filtering.glsl).

- `float aur_normalVariance5(vec3 centerSample, vec3 plusU, vec3 minusU, vec3 plusV, vec3 minusV, float strength, float greenSign)` — experimental.
- `float aur_filteredRoughness(float roughness, float normalVariance)` — experimental.
- `AurMaterial aur_filterNormalMaterial(AurMaterial material, float normalVariance)` — experimental.

