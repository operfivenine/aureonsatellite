// experimental.normal_filtering; dependencies: experimental.normal_mapping, core.materials
// Inputs are five filtered RGB normal samples in the same tangent frame:
// center and +/- half-pixel UV offsets on U and V. Texture reads stay in the scene.
float aur_normalVariance5(vec3 centerSample, vec3 plusU, vec3 minusU,
    vec3 plusV, vec3 minusV, float strength, float greenSign) {
    if(strength<=0.0)return 0.0;
    vec3 mean=(aur_decodeNormal(centerSample,strength,greenSign)
        +aur_decodeNormal(plusU,strength,greenSign)
        +aur_decodeNormal(minusU,strength,greenSign)
        +aur_decodeNormal(plusV,strength,greenSign)
        +aur_decodeNormal(minusV,strength,greenSign))*0.2;
    float lost=max(0.0,1.0-length(centerSample*2.0-1.0)-0.008)*strength*strength;
    return clamp(1.0-dot(mean,mean)+lost,0.0,0.25);
}
float aur_filteredRoughness(float roughness, float normalVariance) {
    float r=clamp(roughness,0.02,1.0);
    return clamp(pow(pow(r,4.0)+clamp(normalVariance,0.0,0.25),0.25),0.02,1.0);
}
AurMaterial aur_filterNormalMaterial(AurMaterial material, float normalVariance) {
    material.roughness=aur_filteredRoughness(material.roughness,normalVariance);
    return material;
}
