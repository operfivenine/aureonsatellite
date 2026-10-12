// core.noise; dependencies: core.math
float aur_hash11(float p) {
    p = fract(p * 0.1031);
    p *= p + 33.33;
    p *= p + p;
    return fract(p);
}
float aur_hash21(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
vec2 aur_hash22(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031,0.1030,0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx+p3.yz)*p3.zy);
}
float aur_hash31(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 33.33);
    return fract((p.x + p.y) * p.z);
}
float aur_noise2(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f*f*(3.0-2.0*f);
    float a = aur_hash21(i);
    float b = aur_hash21(i + vec2(1.0,0.0));
    float c = aur_hash21(i + vec2(0.0,1.0));
    float d = aur_hash21(i + vec2(1.0,1.0));
    return mix(mix(a,b,u.x), mix(c,d,u.x), u.y);
}
float aur_noise3(vec3 p) {
    vec3 i = floor(p), f = fract(p);
    vec3 u = f*f*(3.0-2.0*f);
    float n000 = aur_hash31(i + vec3(0,0,0));
    float n100 = aur_hash31(i + vec3(1,0,0));
    float n010 = aur_hash31(i + vec3(0,1,0));
    float n110 = aur_hash31(i + vec3(1,1,0));
    float n001 = aur_hash31(i + vec3(0,0,1));
    float n101 = aur_hash31(i + vec3(1,0,1));
    float n011 = aur_hash31(i + vec3(0,1,1));
    float n111 = aur_hash31(i + vec3(1,1,1));
    float x00 = mix(n000,n100,u.x), x10 = mix(n010,n110,u.x);
    float x01 = mix(n001,n101,u.x), x11 = mix(n011,n111,u.x);
    return mix(mix(x00,x10,u.y), mix(x01,x11,u.y), u.z);
}
float aur_fbm2(vec2 p) {
    float s=0.0, a=0.5;
    mat2 m=mat2(0.80,-0.60,0.60,0.80);
    for (int i=0; i<5; i++) { s += a*aur_noise2(p); p=m*p*2.03+17.1; a*=0.5; }
    return s;
}
float aur_fbm3(vec3 p) {
    float s=0.0, a=0.5;
    for (int i=0; i<5; i++) { s += a*aur_noise3(p); p=p*2.03+vec3(17.1,9.2,13.7); a*=0.5; }
    return s;
}
