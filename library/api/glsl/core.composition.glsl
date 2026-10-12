// core.composition; dependencies: core.math
float aur_glow(float signedDistance, float width, float intensity) {
    return intensity*exp(-abs(signedDistance)/max(1e-4,width));
}
float aur_lineMask(float distanceValue, float width, float softness) {
    return 1.0-smoothstep(width,max(width+1e-5,width+softness),abs(distanceValue));
}
float aur_vignette(vec2 centeredUv, float strength) {
    float r=dot(centeredUv,centeredUv);
    return clamp(1.0-r*max(0.0,strength),0.0,1.0);
}
vec3 aur_screen(vec3 base, vec3 layer) { return 1.0-(1.0-base)*(1.0-layer); }
