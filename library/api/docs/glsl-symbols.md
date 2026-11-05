# GLSL functions and structures

[← API](../README.md) · [Русский](glsl-symbols.ru.md)

Signatures and structure fields are extracted from the November API declarations. Function bodies and host implementation are not included. Optional modules are not loaded automatically: account for dependencies and the renderer profile. Behavioral semantics are covered in the topic guides; this is an interface index.

## core.math

Dependencies: none.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_sat(float x)` |
| `vec2` | `aur_sat(vec2 x)` |
| `vec3` | `aur_sat(vec3 x)` |
| `float` | `aur_remap(float x, float a, float b, float c, float d)` |
| `mat2` | `aur_rot2(float a)` |
| `float` | `aur_smin(float a, float b, float k)` |
| `float` | `aur_repeat1(float x, float spacing)` |
| `vec2` | `aur_repeat2(vec2 p, vec2 spacing)` |

## core.noise

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_hash11(float p)` |
| `float` | `aur_hash21(vec2 p)` |
| `vec2` | `aur_hash22(vec2 p)` |
| `float` | `aur_hash31(vec3 p)` |
| `float` | `aur_noise2(vec2 p)` |
| `float` | `aur_noise3(vec3 p)` |
| `float` | `aur_fbm2(vec2 p)` |
| `float` | `aur_fbm3(vec3 p)` |

## core.sdf

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_sdSphere(vec3 p, float r)` |
| `float` | `aur_sdBox(vec3 p, vec3 b)` |
| `float` | `aur_sdRoundBox(vec3 p, vec3 b, float r)` |
| `float` | `aur_sdCylinderY(vec3 p, vec2 h)` |
| `float` | `aur_sdCapsule(vec3 p, vec3 a, vec3 b, float r)` |
| `float` | `aur_sdTorus(vec3 p, vec2 t)` |
| `float` | `aur_opUnion(float a, float b)` |
| `float` | `aur_opIntersect(float a, float b)` |
| `float` | `aur_opSubtract(float a, float b)` |
| `float` | `aur_opSmoothUnion(float a, float b, float k)` |

## core.lighting

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_diffuse(vec3 n, vec3 l)` |
| `float` | `aur_fresnel(vec3 n, vec3 v, float power)` |
| `float` | `aur_rim(vec3 n, vec3 v, float width, float power)` |
| `float` | `aur_specular(vec3 n, vec3 l, vec3 v, float roughness)` |
| `float` | `aur_attenuation(float distanceToLight, float radius)` |
| `float` | `aur_shadowTerm(float currentShadow, float fieldDistance, float travel, float softness)` |
| `vec3` | `aur_lit(vec3 baseColor, vec3 n, vec3 l, vec3 v, vec3 lightColor, float diffuseGain, float specularGain, float roughness)` |

## core.environment

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_fogExp(float distanceValue, float density)` |
| `float` | `aur_fogExp2(float distanceValue, float density)` |
| `float` | `aur_depthFade(float distanceValue, float nearDistance, float farDistance)` |
| `float` | `aur_heightFog(float worldY, float baseHeight, float falloff)` |
| `vec3` | `aur_applyFog(vec3 color, vec3 fogColor, float fogAmount)` |

## core.color

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `vec3` | `aur_palette(float t, vec3 a, vec3 b, vec3 c, vec3 d)` |
| `vec3` | `aur_tonemapReinhard(vec3 c)` |
| `vec3` | `aur_tonemapAces(vec3 x)` |
| `vec3` | `aur_saturation(vec3 c, float amount)` |
| `vec3` | `aur_contrast(vec3 c, float amount)` |

## core.composition

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_glow(float signedDistance, float width, float intensity)` |
| `float` | `aur_lineMask(float distanceValue, float width, float softness)` |
| `float` | `aur_vignette(vec2 centeredUv, float strength)` |
| `vec3` | `aur_screen(vec3 base, vec3 layer)` |

## core.camera

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `mat3` | `aur_lookAt(vec3 ro, vec3 target, float roll)` |
| `vec3` | `aur_cameraRay(vec2 centeredUv, float aspect, vec3 ro, vec3 target, float fovDeg, float roll)` |

## core.geometry

Dependencies: `core.math`, `core.sdf`.

| Return type | Function and arguments |
| --- | --- |
| `vec3` | `aur_rotateX(vec3 p, float a)` |
| `vec3` | `aur_rotateY(vec3 p, float a)` |
| `vec3` | `aur_rotateZ(vec3 p, float a)` |
| `vec3` | `aur_twistY(vec3 p, float amount)` |
| `vec3` | `aur_bendX(vec3 p, float amount)` |
| `vec3` | `aur_repeat3(vec3 p, vec3 spacing)` |
| `vec2` | `aur_polarRepeat(vec2 p, float count)` |
| `float` | `aur_opOnion(float d, float thickness)` |
| `float` | `aur_opRound(float d, float radius)` |
| `float` | `aur_opChamferUnion(float a, float b, float radius)` |
| `float` | `aur_sdPlane(vec3 p, vec3 normal, float offset)` |

## core.materials

Dependencies: `core.math`, `core.lighting`.

| Return type | Function and arguments |
| --- | --- |
| `AurMaterial` | `aur_material(vec3 baseColor, float roughness, float metalness, vec3 emission, float ao)` |
| `vec3` | `aur_materialVariation(vec3 baseColor, float variation, float amount)` |
| `vec3` | `aur_shadeMaterial(AurMaterial m, vec3 n, vec3 l, vec3 v, vec3 lightColor, float lightStrength, float shadow)` |
| `vec3` | `aur_addRim(vec3 color, vec3 rimColor, vec3 n, vec3 v, float power, float strength)` |

**AurMaterial**

```glsl
struct AurMaterial {
    vec3 baseColor;
    vec3 emission;
    float roughness;
    float metalness;
    float ao;
};
```

## core.scene_lighting

Dependencies: `core.math`, `core.lighting`, `core.materials`.

| Return type | Function and arguments |
| --- | --- |
| `AurLightRig` | `aur_lightRig(vec3 ambientColor, float ambientStrength, vec3 keyDirection, vec3 keyColor, float keyIntensity, vec3 fillDirection, vec3 fillColor, float fillIntensity, vec3 rimDirection, vec3 rimColor, float rimIntensity)` |
| `vec3` | `aur_fresnelSchlick(float cosTheta, vec3 f0)` |
| `float` | `aur_distributionGGX(vec3 n, vec3 h, float roughness)` |
| `float` | `aur_geometrySchlickGGX(float ndv, float roughness)` |
| `float` | `aur_geometrySmith(vec3 n, vec3 v, vec3 l, float roughness)` |
| `vec3` | `aur_brdfLight(AurMaterial m, vec3 n, vec3 v, vec3 l, vec3 lightColor, float intensity, float shadow)` |
| `vec3` | `aur_ambientMaterial(AurMaterial m, vec3 ambientColor, float strength)` |
| `vec3` | `aur_rimLight(vec3 n, vec3 v, vec3 lightDirection, vec3 color, float intensity)` |
| `vec3` | `aur_shadeLightRig(AurMaterial m, vec3 n, vec3 v, AurLightRig rig, float keyShadow)` |
| `vec3` | `aur_pointLight(AurMaterial m, vec3 n, vec3 v, vec3 p, vec3 lightPosition, vec3 lightColor, float intensity, float radius, float shadow)` |
| `float` | `aur_spotCone(vec3 fromLightToPoint, vec3 lightForward, float innerCos, float outerCos)` |
| `vec3` | `aur_spotLight(AurMaterial m, vec3 n, vec3 v, vec3 p, vec3 lightPosition, vec3 lightForward, vec3 lightColor, float intensity, float radius, float innerCos, float outerCos, float shadow)` |
| `vec3` | `aur_emissiveSpill(vec3 p, vec3 sourcePosition, vec3 sourceColor, float intensity, float radius)` |

**AurLightRig**

```glsl
struct AurLightRig {
    vec3 ambientColor;
    float ambientStrength;
    vec3 keyDirection;
    vec3 keyColor;
    float keyIntensity;
    vec3 fillDirection;
    vec3 fillColor;
    float fillIntensity;
    vec3 rimDirection;
    vec3 rimColor;
    float rimIntensity;
};
```

## core.atmosphere

Dependencies: `core.math`, `core.noise`, `core.environment`, `core.composition`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_phaseHG(float cosTheta, float g)` |
| `float` | `aur_layerBand(float worldY, float centerY, float halfWidth, float feather)` |
| `float` | `aur_heightFogDensity(vec3 p, float baseHeight, float density, float falloff)` |
| `float` | `aur_hazeDensity(float travel, float startDistance, float endDistance, float density)` |
| `float` | `aur_segmentDistance(vec3 p, vec3 a, vec3 b)` |
| `float` | `aur_beamTube(vec3 p, vec3 a, vec3 b, float radius, float feather)` |
| `float` | `aur_beamCone(vec3 p, vec3 origin, vec3 direction, float lengthValue, float radiusNear, float radiusFar, float feather)` |
| `vec3` | `aur_hash33(vec3 p)` |
| `float` | `aur_dustField(vec3 p, float cellSize, float particleRadius, float density, float seed)` |
| `float` | `aur_fogNoise(vec3 p, float scale, float amount)` |
| `float` | `aur_softBloomMask(float luminanceValue, float threshold, float knee)` |
| `vec3` | `aur_bloomContribution(vec3 emissionColor, float mask, float strength)` |

## core.motion

Dependencies: `core.math`, `core.geometry`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_motionSine(float t, float speed, float phase)` |
| `float` | `aur_motionCycle(float t, float speed, float phase)` |
| `float` | `aur_motionTriangle(float t, float speed, float phase)` |
| `float` | `aur_motionPingPong(float t, float speed, float phase)` |
| `float` | `aur_motionSmoothCycle(float t, float speed, float phase)` |
| `float` | `aur_sequenceWindow(float t, float period, float start, float duration, float feather)` |
| `float` | `aur_easeInOut(float x)` |
| `float` | `aur_easeSmoother(float x)` |
| `vec3` | `aur_pivotRotateX(vec3 p, vec3 pivot, float angle)` |
| `vec3` | `aur_pivotRotateY(vec3 p, vec3 pivot, float angle)` |
| `vec3` | `aur_pivotRotateZ(vec3 p, vec3 pivot, float angle)` |
| `vec3` | `aur_slideTransform(vec3 p, vec3 direction, float distanceValue, float amount)` |
| `float` | `aur_secondarySway(float t, float speed, float primary, float lag, float amplitude)` |
| `float` | `aur_followMix(float currentLike, float targetLike, float amount)` |
| `float` | `aur_eventActive(vec4 e)` |
| `float` | `aur_eventProgress(vec4 e)` |
| `float` | `aur_eventStrength(vec4 e)` |
| `float` | `aur_eventSeed(vec4 e)` |
| `float` | `aur_eventGroup(vec4 e)` |
| `float` | `aur_eventEaseOut(vec4 e, float powerValue)` |
| `float` | `aur_eventPulse(vec4 e, float attackFraction, float decayPower)` |
| `float` | `aur_eventRing(vec4 e, float phase, float width)` |
| `float` | `aur_eventVariant(vec4 e, float count)` |
| `float` | `aur_eventSigned(vec4 e)` |

## core.presentation

Dependencies: `core.math`, `core.noise`, `core.color`, `core.composition`, `core.atmosphere`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_luminance(vec3 c)` |
| `float` | `aur_qualityLevel()` |
| `float` | `aur_qualitySelect(float lowValue, float mediumValue, float highValue)` |
| `vec3` | `aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue)` |
| `float` | `aur_qualitySelect(float lowValue, float mediumValue, float highValue, float extremeValue)` |
| `vec3` | `aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue, vec3 extremeValue)` |
| `float` | `aur_detailScale(float lowValue, float mediumValue, float highValue)` |
| `float` | `aur_aaCoverage(float signedDistance)` |
| `float` | `aur_aaLine(float signedDistance, float halfWidth)` |
| `vec2` | `aur_subpixelOffset(int sampleIndex)` |
| `vec3` | `aur_exposure(vec3 color, float stops)` |
| `vec3` | `aur_liftGammaGain(vec3 color, vec3 lift, vec3 gammaValue, vec3 gain)` |
| `vec3` | `aur_grade(vec3 color, float contrastValue, float saturationValue, vec3 tint)` |
| `vec3` | `aur_softClip(vec3 color, float shoulder)` |
| `float` | `aur_filmGrain(vec2 pixel, float timeValue, float amount)` |
| `vec3` | `aur_dither(vec3 color, vec2 pixel, float amount)` |
| `AurPresentation` | `aur_presentation(float exposureValue, float contrastValue, float saturationValue, float vignetteValue, float bloomThreshold, float bloomKnee, float bloomStrength, float grainValue, float ditherValue, vec3 tintValue)` |
| `vec3` | `aur_present(vec3 hdrColor, vec2 centeredUv, vec2 fragCoord, float timeValue, AurPresentation p)` |

**AurPresentation**

```glsl
struct AurPresentation {
    float exposure;
    float contrast;
    float saturation;
    float vignette;
    float bloomThreshold;
    float bloomKnee;
    float bloomStrength;
    float grain;
    float dither;
    vec3 tint;
};
```

## core.object

Dependencies: `core.math`, `core.noise`, `core.sdf`, `core.geometry`, `core.lighting`, `core.materials`.

## core.world

Dependencies: `core.math`, `core.noise`, `core.sdf`, `core.lighting`, `core.environment`, `core.color`, `core.composition`, `core.camera`.

## core.object_motion

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `vec3` | `aur_objectUnit(vec3 v, vec3 fallbackValue)` |
| `mat3` | `aur_objectFrame(vec3 forwardValue, vec3 upHint)` |
| `mat3` | `aur_objectEuler(vec3 angles)` |
| `AurObjectPose` | `aur_objectPose(vec3 positionValue, vec3 angles, float scaleValue)` |
| `AurObjectPose` | `aur_objectFollow(AurPathSample path, vec3 upHint, vec3 fallbackForward, float scaleValue)` |
| `vec3` | `aur_objectToLocal(AurObjectPose o,vec3 worldPosition)` |
| `vec3` | `aur_objectToWorld(AurObjectPose o,vec3 localPosition)` |
| `vec3` | `aur_objectNormal(AurObjectPose o,vec3 localNormal)` |
| `float` | `aur_objectDistance(AurObjectPose o,float localDistance)` |
| `AurPathSample` | `aur_pathLine(vec3 origin,vec3 velocity,float timeValue)` |
| `AurPathSample` | `aur_pathOrbit(vec3 center,vec3 axis,float radius,float angularSpeed,float phase,float timeValue)` |
| `AurPathSample` | `aur_pathShuttle(vec3 a,vec3 b,float period,float phase,float timeValue)` |
| `vec3` | `aur_shuttleHeading(vec3 a,vec3 b,vec3 upHint,float period,float phase,float timeValue,float turnFraction)` |

**AurPathSample**

```glsl
struct AurPathSample {
    vec3 position;
    vec3 velocity;
};
```

**AurObjectPose**

```glsl
struct AurObjectPose {
    vec3 position;
    mat3 rotation;
    float scale;
};
```

## core.attachments

Dependencies: `core.object_motion`.

| Return type | Function and arguments |
| --- | --- |
| `AurObjectPose` | `aur_objectCompose(AurObjectPose parent, AurObjectPose child)` |
| `AurObjectPose` | `aur_objectSocket(AurObjectPose parent,vec3 localPosition,vec3 localAngles)` |
| `vec3` | `aur_objectDirection(AurObjectPose pose,vec3 direction)` |
| `float` | `aur_attachmentJet(vec3 worldPoint,AurObjectPose socket,float lengthValue,float radius,float timeValue,float strength)` |
| `float` | `aur_attachmentBeacon(vec3 worldPoint,AurObjectPose socket,float radius,float timeValue,float frequency,float phase)` |

## core.instances

Dependencies: `core.noise`, `core.object_motion`.

| Return type | Function and arguments |
| --- | --- |
| `AurInstance` | `aur_instance(int index,float groupSeed,vec2 speedRange,vec2 scaleRange,vec2 gainRange)` |
| `float` | `aur_instanceReaction(AurInstance instance,float bandValue,float broadValue,float broadMix)` |
| `vec3` | `aur_instanceRing(int index,int count,float radius,float phase)` |

**AurInstance**

```glsl
struct AurInstance {
    float seed;
    float phase;
    float speed;
    float scale;
    float gain;
    int band;
};
```

## core.trails_lod

Dependencies: `core.math`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_lodWeight(float distanceValue,float nearDistance,float farDistance)` |
| `float` | `aur_trailFade(float age,float lifetime)` |
| `float` | `aur_trailSegment(vec3 ro,vec3 rd,float depth,vec3 a,vec3 b,float radius)` |

## aurs.standard

Dependencies: `core.world`, `core.object`, `core.scene_lighting`, `core.atmosphere`, `core.motion`, `core.presentation`, `core.object_motion`, `core.attachments`, `core.instances`, `core.trails_lod`.

## experimental.texture_materials

Dependencies: `core.materials`.

| Return type | Function and arguments |
| --- | --- |
| `AurMaterial` | `aur_textureMaterial(vec3 colorSample, vec3 ormSample, vec3 emissionSample, vec3 tint, float roughnessScale, float metalnessScale, float aoStrength, float emissionStrength)` |
| `vec3` | `aur_packORM(float occlusion, float roughness, float metalness)` |
| `vec2` | `aur_textureUV(vec2 uv, vec2 tiling, vec2 offset)` |

## experimental.normal_mapping

Dependencies: none.

| Return type | Function and arguments |
| --- | --- |
| `vec3` | `aur_decodeNormal(vec3 sampleValue, float strength, float greenSign)` |
| `vec3` | `aur_normalMap(vec3 geometricNormal, vec3 tangentU, vec3 tangentV, vec3 sampleValue, float strength, float greenSign)` |

## experimental.triplanar

Dependencies: `experimental.normal_mapping`.

| Return type | Function and arguments |
| --- | --- |
| `AurTriplanar` | `aur_triplanar(vec3 position, vec3 normal, float scale, float sharpness)` |
| `vec3` | `aur_triplanarBlend(AurTriplanar p, vec3 x, vec3 y, vec3 z)` |
| `vec3` | `aur_triplanarNormal(AurTriplanar p, vec3 x, vec3 y, vec3 z, float strength, float greenSign)` |

**AurTriplanar**

```glsl
struct AurTriplanar {
    vec2 uvX;
    vec2 uvY;
    vec2 uvZ;
    vec3 weights;
    vec3 signs;
    vec3 normal;
};
```

## experimental.scene_lights

Dependencies: `core.scene_lighting`, `core.object_motion`.

| Return type | Function and arguments |
| --- | --- |
| `AurSceneLight` | `aur_sceneDirectional(vec3 direction, vec3 color, float intensity)` |
| `AurSceneLight` | `aur_scenePoint(vec3 position, vec3 color, float intensity, float radius)` |
| `AurSceneLight` | `aur_sceneSpot(vec3 position, vec3 direction, vec3 color, float intensity, float radius, float innerDegrees, float outerDegrees)` |
| `AurSceneLight` | `aur_sceneLightAttach(AurSceneLight l, AurObjectPose pose)` |
| `AurSceneLight` | `aur_sceneLightGain(AurSceneLight l, float gain)` |
| `vec3` | `aur_sceneLightShade(AurSceneLight l, AurMaterial material, vec3 position, vec3 normal, vec3 viewDirection, float visibility)` |

**AurSceneLight**

```glsl
struct AurSceneLight {
    int kind;
    vec3 position;
    vec3 direction;
    vec3 color;
    float intensity;
    float radius;
    float innerCos;
    float outerCos;
};
```

## experimental.normal_filtering

Dependencies: `experimental.normal_mapping`, `core.materials`.

| Return type | Function and arguments |
| --- | --- |
| `float` | `aur_normalVariance5(vec3 centerSample, vec3 plusU, vec3 minusU, vec3 plusV, vec3 minusV, float strength, float greenSign)` |
| `float` | `aur_filteredRoughness(float roughness, float normalVariance)` |
| `AurMaterial` | `aur_filterNormalMaterial(AurMaterial material, float normalVariance)` |

