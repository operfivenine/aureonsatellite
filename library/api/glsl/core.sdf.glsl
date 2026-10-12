// core.sdf; dependencies: core.math
float aur_sdSphere(vec3 p, float r) { return length(p)-r; }
float aur_sdBox(vec3 p, vec3 b) {
    vec3 q=abs(p)-b;
    return length(max(q,0.0))+min(max(q.x,max(q.y,q.z)),0.0);
}
float aur_sdRoundBox(vec3 p, vec3 b, float r) { return aur_sdBox(p,b)-r; }
float aur_sdCylinderY(vec3 p, vec2 h) {
    vec2 d=abs(vec2(length(p.xz),p.y))-h;
    return min(max(d.x,d.y),0.0)+length(max(d,0.0));
}
float aur_sdCapsule(vec3 p, vec3 a, vec3 b, float r) {
    vec3 pa=p-a, ba=b-a;
    float h=clamp(dot(pa,ba)/max(1e-6,dot(ba,ba)),0.0,1.0);
    return length(pa-ba*h)-r;
}
float aur_sdTorus(vec3 p, vec2 t) {
    vec2 q=vec2(length(p.xz)-t.x,p.y);
    return length(q)-t.y;
}
float aur_opUnion(float a, float b) { return min(a,b); }
float aur_opIntersect(float a, float b) { return max(a,b); }
float aur_opSubtract(float a, float b) { return max(a,-b); }
float aur_opSmoothUnion(float a, float b, float k) { return aur_smin(a,b,k); }
