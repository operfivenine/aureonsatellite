// core.camera; dependencies: core.math
mat3 aur_lookAt(vec3 ro, vec3 target, float roll) {
    vec3 f=normalize(target-ro);
    vec3 upRef=abs(f.y)>0.985 ? vec3(0.0,0.0,1.0) : vec3(0.0,1.0,0.0);
    vec3 r=normalize(cross(f,upRef));
    vec3 u=normalize(cross(r,f));
    float c=cos(roll), s=sin(roll);
    vec3 rr=r*c+u*s;
    vec3 uu=-r*s+u*c;
    return mat3(rr,uu,f);
}
vec3 aur_cameraRay(vec2 centeredUv, float aspect, vec3 ro, vec3 target, float fovDeg, float roll) {
    vec2 p=centeredUv;
    p.x*=aspect;
    float z=1.0/tan(radians(clamp(fovDeg,1.0,179.0))*0.5);
    return normalize(aur_lookAt(ro,target,roll)*vec3(p,z));
}
