// core.motion; dependencies: core.math, core.geometry
// PASS 07 — theme-agnostic motion and event helpers.
float aur_motionSine(float t, float speed, float phase) {
    return sin(t*speed*6.28318530718 + phase);
}
float aur_motionCycle(float t, float speed, float phase) {
    return fract(t*speed + phase/6.28318530718);
}
float aur_motionTriangle(float t, float speed, float phase) {
    float x=aur_motionCycle(t,speed,phase);
    return 1.0-abs(x*2.0-1.0);
}
float aur_motionPingPong(float t, float speed, float phase) {
    return aur_motionTriangle(t,speed,phase);
}
float aur_motionSmoothCycle(float t, float speed, float phase) {
    float x=aur_motionTriangle(t,speed,phase);
    return x*x*(3.0-2.0*x);
}
float aur_sequenceWindow(float t, float period, float start, float duration, float feather) {
    float p=max(period,1e-4);
    float x=mod(t,p);
    float s=mod(start,p);
    float d=clamp(duration,0.0,p);
    float f=max(feather,1e-4);
    float rel=mod(x-s+p,p);
    float on=smoothstep(0.0,f,rel);
    float off=1.0-smoothstep(max(0.0,d-f),d,rel);
    return (rel<=d) ? on*off : 0.0;
}
float aur_easeInOut(float x) {
    x=clamp(x,0.0,1.0);
    return x*x*(3.0-2.0*x);
}
float aur_easeSmoother(float x) {
    x=clamp(x,0.0,1.0);
    return x*x*x*(x*(x*6.0-15.0)+10.0);
}
vec3 aur_pivotRotateX(vec3 p, vec3 pivot, float angle) {
    return aur_rotateX(p-pivot,-angle)+pivot;
}
vec3 aur_pivotRotateY(vec3 p, vec3 pivot, float angle) {
    return aur_rotateY(p-pivot,-angle)+pivot;
}
vec3 aur_pivotRotateZ(vec3 p, vec3 pivot, float angle) {
    return aur_rotateZ(p-pivot,-angle)+pivot;
}
vec3 aur_slideTransform(vec3 p, vec3 direction, float distanceValue, float amount) {
    vec3 d=length(direction)>1e-5 ? normalize(direction) : vec3(1.0,0.0,0.0);
    return p-d*distanceValue*clamp(amount,0.0,1.0);
}
float aur_secondarySway(float t, float speed, float primary, float lag, float amplitude) {
    return aur_motionSine(t,max(0.0,speed),lag+primary*0.35)*amplitude;
}
float aur_followMix(float currentLike, float targetLike, float amount) {
    return mix(currentLike,targetLike,clamp(amount,0.0,1.0));
}

// Event packing is owned by AURS v2: x=progress (or -1 inactive), y=strength, z=seed, w=group.
float aur_eventActive(vec4 e) { return step(0.0,e.x); }
float aur_eventProgress(vec4 e) { return clamp(e.x,0.0,1.0); }
float aur_eventStrength(vec4 e) { return max(0.0,e.y)*aur_eventActive(e); }
float aur_eventSeed(vec4 e) { return e.z; }
float aur_eventGroup(vec4 e) { return e.w; }
float aur_eventEaseOut(vec4 e, float powerValue) {
    float p=aur_eventProgress(e);
    return aur_eventStrength(e)*pow(max(0.0,1.0-p),max(0.01,powerValue));
}
float aur_eventPulse(vec4 e, float attackFraction, float decayPower) {
    if (e.x<0.0) return 0.0;
    float p=clamp(e.x,0.0,1.0);
    float a=clamp(attackFraction,0.001,0.95);
    float up=smoothstep(0.0,a,p);
    float down=pow(max(0.0,1.0-p),max(0.01,decayPower));
    return e.y*up*down;
}
float aur_eventRing(vec4 e, float phase, float width) {
    if (e.x<0.0) return 0.0;
    float w=max(1e-4,width);
    return e.y*exp(-abs(clamp(e.x,0.0,1.0)-phase)/w);
}
float aur_eventVariant(vec4 e, float count) {
    float n=max(1.0,floor(count));
    return floor(clamp(e.z,0.0,0.999999)*n);
}
float aur_eventSigned(vec4 e) {
    return mix(-1.0,1.0,step(0.5,fract(e.z*17.713)));
}
