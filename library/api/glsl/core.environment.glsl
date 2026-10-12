// core.environment; dependencies: core.math
float aur_fogExp(float distanceValue, float density) {
    return 1.0-exp(-max(0.0,distanceValue)*max(0.0,density));
}
float aur_fogExp2(float distanceValue, float density) {
    float x=max(0.0,distanceValue)*max(0.0,density);
    return 1.0-exp(-x*x);
}
float aur_depthFade(float distanceValue, float nearDistance, float farDistance) {
    return smoothstep(nearDistance, max(nearDistance+1e-4,farDistance), distanceValue);
}
float aur_heightFog(float worldY, float baseHeight, float falloff) {
    return exp(-max(0.0,worldY-baseHeight)*max(0.0,falloff));
}
vec3 aur_applyFog(vec3 color, vec3 fogColor, float fogAmount) {
    return mix(color,fogColor,clamp(fogAmount,0.0,1.0));
}
