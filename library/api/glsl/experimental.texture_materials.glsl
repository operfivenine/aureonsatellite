// experimental.texture_materials; dependencies: core.materials
// Inputs are sampled linear values. Hardware decodes sRGB color/emission maps.
// ORM: R=ambient occlusion, G=roughness, B=metalness.
AurMaterial aur_textureMaterial(vec3 colorSample, vec3 ormSample,
    vec3 emissionSample, vec3 tint, float roughnessScale,
    float metalnessScale, float aoStrength, float emissionStrength) {
    return aur_material(colorSample*max(tint,vec3(0.0)),
        ormSample.g*max(roughnessScale,0.0),
        ormSample.b*max(metalnessScale,0.0),
        emissionSample*max(emissionStrength,0.0),
        mix(1.0,clamp(ormSample.r,0.0,1.0),clamp(aoStrength,0.0,1.0)));
}
// Separate map channels can be assembled without requiring extra samplers.
vec3 aur_packORM(float occlusion, float roughness, float metalness) {
    return clamp(vec3(occlusion,roughness,metalness),0.0,1.0);
}
vec2 aur_textureUV(vec2 uv, vec2 tiling, vec2 offset) {
    return uv*tiling+offset;
}
