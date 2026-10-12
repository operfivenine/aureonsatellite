// core.trails_lod; dependencies: core.math
float aur_lodWeight(float distanceValue,float nearDistance,float farDistance) {
    float lo=max(0.0,min(nearDistance,farDistance));
    float hi=max(lo+0.001,max(nearDistance,farDistance));
    return 1.0-smoothstep(lo,hi,max(0.0,distanceValue));
}
float aur_trailFade(float age,float lifetime) {
    if(lifetime<=0.0 || age<0.0)return 0.0;
    float t=clamp(age/lifetime,0.0,1.0);return (1.0-t)*(1.0-t);
}
// Soft finite segment seen along a normalized ray, clipped at scene depth.
// Returns coverage, not a physical integral. Caller supplies age/taper/color.
float aur_trailSegment(vec3 ro,vec3 rd,float depth,vec3 a,vec3 b,float radius) {
    if(depth<=0.0 || radius<=0.0)return 0.0;
    vec3 v=b-a,w=ro-a;float vv=dot(v,v);
    if(vv<1e-10)return 0.0;

    // OPT 05.8: conservative per-segment broad phase.  The finite segment
    // expanded by radius is fully contained by this midpoint sphere.  Use a
    // sqrt-free overestimate of (0.5*length(v)+radius)^2, so a rejection can
    // never remove coverage produced by the exact trail kernel below.
    vec3 center=a+v*0.5;
    float boundRadius2=0.5*vv+2.0*radius*radius;
    float boundT=clamp(dot(center-ro,rd),0.0,depth);
    vec3 boundDelta=ro+rd*boundT-center;
    if(dot(boundDelta,boundDelta)>boundRadius2)return 0.0;

    float rv=dot(rd,v),rw=dot(rd,w),vw=dot(v,w);
    float denom=max(1e-8,vv-rv*rv);
    float u=clamp((vw-rv*rw)/denom,0.0,1.0);
    float t=clamp(dot(a+v*u-ro,rd),0.0,depth);
    u=clamp(dot(ro+rd*t-a,v)/vv,0.0,1.0);
    t=clamp(dot(a+v*u-ro,rd),0.0,depth);
    float d=length(ro+rd*t-(a+v*u));
    return 1.0-smoothstep(radius*0.25,radius,d);
}
