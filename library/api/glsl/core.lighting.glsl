// core.lighting; dependencies: core.math
float aur_diffuse(vec3 n, vec3 l) { return max(dot(n,l),0.0); }
float aur_fresnel(vec3 n, vec3 v, float power) {
    return pow(1.0-max(dot(n,v),0.0), max(0.01,power));
}
float aur_rim(vec3 n, vec3 v, float width, float power) {
    float r=pow(1.0-max(dot(n,v),0.0),max(0.01,power));
    return smoothstep(max(0.0,1.0-width),1.0,r);
}
float aur_specular(vec3 n, vec3 l, vec3 v, float roughness) {
    vec3 h=normalize(l+v);
    float p=mix(96.0,4.0,clamp(roughness,0.0,1.0));
    return pow(max(dot(n,h),0.0),p);
}
float aur_attenuation(float distanceToLight, float radius) {
    float x=distanceToLight/max(1e-4,radius);
    return 1.0/(1.0+x*x);
}
float aur_shadowTerm(float currentShadow, float fieldDistance, float travel, float softness) {
    float penumbra=softness*fieldDistance/max(1e-4,travel);
    return min(currentShadow,clamp(penumbra,0.0,1.0));
}
vec3 aur_lit(vec3 baseColor, vec3 n, vec3 l, vec3 v, vec3 lightColor,
             float diffuseGain, float specularGain, float roughness) {
    float d=aur_diffuse(n,l)*diffuseGain;
    float s=aur_specular(n,l,v,roughness)*specularGain;
    return baseColor*(0.08+d)*lightColor + lightColor*s;
}
