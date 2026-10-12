// core.color; dependencies: core.math
vec3 aur_palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a+b*cos(6.28318530718*(c*t+d));
}
vec3 aur_tonemapReinhard(vec3 c) { return c/(1.0+c); }
vec3 aur_tonemapAces(vec3 x) {
    const float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.0,1.0);
}
vec3 aur_saturation(vec3 c, float amount) {
    float l=dot(c,vec3(0.2126,0.7152,0.0722));
    return mix(vec3(l),c,amount);
}
vec3 aur_contrast(vec3 c, float amount) { return (c-0.5)*amount+0.5; }
