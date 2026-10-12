// core.object_motion; dependencies: core.math
struct AurPathSample { vec3 position; vec3 velocity; };
struct AurObjectPose { vec3 position; mat3 rotation; float scale; };
vec3 aur_objectUnit(vec3 v, vec3 fallbackValue) {
    float m=dot(v,v);
    return m>1e-12 ? v*inversesqrt(m) : fallbackValue;
}
// Columns map local +X/right, +Y/up, +Z/forward into world coordinates.
mat3 aur_objectFrame(vec3 forwardValue, vec3 upHint) {
    vec3 f=aur_objectUnit(forwardValue,vec3(0,0,1));
    vec3 u=aur_objectUnit(upHint,vec3(0,1,0));
    if(abs(dot(f,u))>0.999) u=abs(f.y)<0.9?vec3(0,1,0):vec3(1,0,0);
    vec3 r=normalize(cross(u,f));
    return mat3(r,cross(f,r),f);
}
// Active local-to-world rotation: X, then Y, then Z, all angles in radians.
mat3 aur_objectEuler(vec3 angles) {
    vec3 c=cos(angles),s=sin(angles);
    mat3 x=mat3(1,0,0, 0,c.x,s.x, 0,-s.x,c.x);
    mat3 y=mat3(c.y,0,-s.y, 0,1,0, s.y,0,c.y);
    mat3 z=mat3(c.z,s.z,0, -s.z,c.z,0, 0,0,1);
    return z*y*x;
}
AurObjectPose aur_objectPose(vec3 positionValue, vec3 angles, float scaleValue) {
    AurObjectPose o; o.position=positionValue; o.rotation=aur_objectEuler(angles);
    o.scale=max(abs(scaleValue),0.0001); return o;
}
AurObjectPose aur_objectFollow(AurPathSample path, vec3 upHint, vec3 fallbackForward, float scaleValue) {
    AurObjectPose o; o.position=path.position;
    o.rotation=aur_objectFrame(aur_objectUnit(path.velocity,aur_objectUnit(fallbackForward,vec3(0,0,1))),upHint);
    o.scale=max(abs(scaleValue),0.0001); return o;
}
vec3 aur_objectToLocal(AurObjectPose o,vec3 worldPosition) {
    return transpose(o.rotation)*(worldPosition-o.position)/o.scale;
}
vec3 aur_objectToWorld(AurObjectPose o,vec3 localPosition) {
    return o.position+o.rotation*(localPosition*o.scale);
}
vec3 aur_objectNormal(AurObjectPose o,vec3 localNormal) {
    return aur_objectUnit(o.rotation*localNormal,vec3(0,1,0));
}
float aur_objectDistance(AurObjectPose o,float localDistance) {return localDistance*o.scale;}
AurPathSample aur_pathLine(vec3 origin,vec3 velocity,float timeValue) {
    AurPathSample p;p.position=origin+velocity*timeValue;p.velocity=velocity;return p;
}
// Axis is the orbit normal; phase is radians, angularSpeed is radians/second.
AurPathSample aur_pathOrbit(vec3 center,vec3 axis,float radius,float angularSpeed,float phase,float timeValue) {
    mat3 basis=aur_objectFrame(axis,vec3(0,1,0));
    float a=phase+angularSpeed*timeValue,r=max(0.0,radius);
    AurPathSample p;
    p.position=center+r*(basis[0]*cos(a)+basis[1]*sin(a));
    p.velocity=r*angularSpeed*(-basis[0]*sin(a)+basis[1]*cos(a));return p;
}
// Smooth periodic shuttle: period covers A->B->A; phase is in cycles.
// Position velocity is the exact derivative; use aur_shuttleHeading for smooth turns.
AurPathSample aur_pathShuttle(vec3 a,vec3 b,float period,float phase,float timeValue) {
    float w=6.28318530718/max(abs(period),0.001);
    float t=timeValue*w+phase*6.28318530718;
    AurPathSample p;p.position=mix(a,b,0.5-0.5*cos(t));
    p.velocity=(b-a)*(0.5*w*sin(t));return p;
}
// Intentional heading near reversal; pure velocity following otherwise flips by pi.
vec3 aur_shuttleHeading(vec3 a,vec3 b,vec3 upHint,float period,float phase,float timeValue,float turnFraction) {
    vec3 f=aur_objectUnit(b-a,vec3(0,0,1));
    mat3 basis=aur_objectFrame(f,upHint);
    float cycle=fract(timeValue/max(abs(period),0.001)+phase);
    float width=clamp(turnFraction,0.001,0.24);
    float atA=cycle>0.75?cycle-1.0:cycle;
    float theta;
    if(abs(atA)<width) theta=3.14159265359*(1.0-smoothstep(-width,width,atA));
    else theta=3.14159265359*smoothstep(0.5-width,0.5+width,cycle);
    return f*cos(theta)+basis[0]*sin(theta);
}
