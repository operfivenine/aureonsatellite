// core.materials; dependencies: core.math, core.lighting
struct AurMaterial {
    vec3 baseColor;
    vec3 emission;
    float roughness;
    float metalness;
    float ao;
};
AurMaterial aur_material(vec3 baseColor, float roughness, float metalness, vec3 emission, float ao) {
    AurMaterial m;
    m.baseColor=max(baseColor,vec3(0.0));
    m.emission=max(emission,vec3(0.0));
    m.roughness=clamp(roughness,0.02,1.0);
    m.metalness=clamp(metalness,0.0,1.0);
    m.ao=clamp(ao,0.0,1.0);
    return m;
}
vec3 aur_materialVariation(vec3 baseColor, float variation, float amount) {
    float v=(clamp(variation,0.0,1.0)-0.5)*2.0;
    return max(vec3(0.0),baseColor*(1.0+v*amount));
}
vec3 aur_shadeMaterial(AurMaterial m, vec3 n, vec3 l, vec3 v, vec3 lightColor,
                       float lightStrength, float shadow) {
    float ndl=aur_diffuse(n,l);
    float spec=aur_specular(n,l,v,m.roughness);
    vec3 f0=mix(vec3(0.04),m.baseColor,m.metalness);
    vec3 diffuse=m.baseColor*(1.0-m.metalness)*ndl;
    vec3 reflected=f0*spec*(0.30+1.70*(1.0-m.roughness));
    vec3 ambient=m.baseColor*(0.035+0.075*m.ao);
    return (ambient+(diffuse+reflected)*lightColor*max(0.0,lightStrength))*clamp(shadow,0.0,1.0)+m.emission;
}
vec3 aur_addRim(vec3 color, vec3 rimColor, vec3 n, vec3 v, float power, float strength) {
    return color+rimColor*aur_fresnel(n,v,power)*max(0.0,strength);
}
