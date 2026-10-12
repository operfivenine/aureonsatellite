// core.geometry; dependencies: core.math, core.sdf
vec3 aur_rotateX(vec3 p, float a) {
    float c=cos(a), s=sin(a);
    return vec3(p.x, c*p.y-s*p.z, s*p.y+c*p.z);
}
vec3 aur_rotateY(vec3 p, float a) {
    float c=cos(a), s=sin(a);
    return vec3(c*p.x+s*p.z, p.y, -s*p.x+c*p.z);
}
vec3 aur_rotateZ(vec3 p, float a) {
    float c=cos(a), s=sin(a);
    return vec3(c*p.x-s*p.y, s*p.x+c*p.y, p.z);
}
vec3 aur_twistY(vec3 p, float amount) {
    p.xz=aur_rot2(amount*p.y)*p.xz;
    return p;
}
vec3 aur_bendX(vec3 p, float amount) {
    p.yz=aur_rot2(amount*p.x)*p.yz;
    return p;
}
vec3 aur_repeat3(vec3 p, vec3 spacing) {
    vec3 s=max(abs(spacing),vec3(1e-5));
    return mod(p+0.5*s,s)-0.5*s;
}
vec2 aur_polarRepeat(vec2 p, float count) {
    float n=max(1.0,count);
    float sector=6.28318530718/n;
    float a=atan(p.y,p.x);
    a=mod(a+0.5*sector,sector)-0.5*sector;
    float r=length(p);
    return vec2(cos(a),sin(a))*r;
}
float aur_opOnion(float d, float thickness) { return abs(d)-max(0.0,thickness); }
float aur_opRound(float d, float radius) { return d-max(0.0,radius); }
float aur_opChamferUnion(float a, float b, float radius) {
    float r=max(0.0,radius);
    return min(min(a,b),(a-r+b)*0.70710678118);
}
float aur_sdPlane(vec3 p, vec3 normal, float offset) {
    return dot(p,normalize(normal))+offset;
}
