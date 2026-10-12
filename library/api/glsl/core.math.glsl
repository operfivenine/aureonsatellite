// core.math; dependencies: 
float aur_sat(float x) { return clamp(x, 0.0, 1.0); }
vec2 aur_sat(vec2 x) { return clamp(x, 0.0, 1.0); }
vec3 aur_sat(vec3 x) { return clamp(x, 0.0, 1.0); }
float aur_remap(float x, float a, float b, float c, float d) {
    return mix(c, d, clamp((x-a) / max(1e-6, b-a), 0.0, 1.0));
}
mat2 aur_rot2(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}
float aur_smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5*(b-a)/max(1e-6,k), 0.0, 1.0);
    return mix(b, a, h) - k*h*(1.0-h);
}
float aur_repeat1(float x, float spacing) {
    return mod(x + 0.5*spacing, spacing) - 0.5*spacing;
}
vec2 aur_repeat2(vec2 p, vec2 spacing) {
    return mod(p + 0.5*spacing, spacing) - 0.5*spacing;
}
