// experimental.normal_mapping; dependencies: 
vec3 aur_decodeNormal(vec3 sampleValue, float strength, float greenSign) {
    vec3 v=sampleValue*2.0-1.0;
    v.xy*=max(strength,0.0);
    v.y*=greenSign<0.0?-1.0:1.0;
    v.z=max(v.z,0.0001);
    return normalize(v);
}
vec3 aur_normalMap(vec3 geometricNormal, vec3 tangentU, vec3 tangentV,
    vec3 sampleValue, float strength, float greenSign) {
    float nl=dot(geometricNormal,geometricNormal);
    vec3 n=nl>1e-12?geometricNormal*inversesqrt(nl):vec3(0,1,0);
    if(strength<=0.0)return n;
    vec3 t=tangentU-n*dot(n,tangentU);
    float tl=dot(t,t);
    if(tl<1e-12)return n;
    t*=inversesqrt(tl);
    vec3 b=cross(n,t);
    float orientation=dot(b,tangentV);
    if(abs(orientation)<1e-6)return n;
    b*=orientation<0.0?-1.0:1.0;
    vec3 mapped=aur_decodeNormal(sampleValue,strength,greenSign);
    return normalize(t*mapped.x+b*mapped.y+n*mapped.z);
}
