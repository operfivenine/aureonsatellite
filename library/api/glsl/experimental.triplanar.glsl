// experimental.triplanar; dependencies: experimental.normal_mapping
struct AurTriplanar {
    vec2 uvX; vec2 uvY; vec2 uvZ;
    vec3 weights; vec3 signs; vec3 normal;
};
AurTriplanar aur_triplanar(vec3 position, vec3 normal, float scale, float sharpness) {
    AurTriplanar p;
    float len2=dot(normal,normal);
    p.normal=len2>1e-12?normal*inversesqrt(len2):vec3(0,1,0);
    p.signs=vec3(p.normal.x<0.0?-1.0:1.0,p.normal.y<0.0?-1.0:1.0,p.normal.z<0.0?-1.0:1.0);
    vec3 v=position*max(scale,0.0001);
    p.uvX=vec2(-p.signs.x*v.z,v.y);
    p.uvY=vec2(v.x,-p.signs.y*v.z);
    p.uvZ=vec2(p.signs.z*v.x,v.y);
    vec3 w=pow(abs(p.normal),vec3(clamp(sharpness,1.0,16.0)));
    p.weights=w/max(w.x+w.y+w.z,1e-12);
    return p;
}
vec3 aur_triplanarBlend(AurTriplanar p, vec3 x, vec3 y, vec3 z) {
    return x*p.weights.x+y*p.weights.y+z*p.weights.z;
}
vec3 aur_triplanarNormal(AurTriplanar p, vec3 x, vec3 y, vec3 z,
    float strength, float greenSign) {
    if(strength<=0.0)return p.normal;
    vec3 nx=aur_decodeNormal(x,strength,greenSign);
    vec3 ny=aur_decodeNormal(y,strength,greenSign);
    vec3 nz=aur_decodeNormal(z,strength,greenSign);
    // Blend tangent perturbations, not absolute projection-axis normals.
    // This preserves the original surface for a flat normal map.
    vec2 sx=nx.xy/max(nx.z,0.1),sy=ny.xy/max(ny.z,0.1),sz=nz.xy/max(nz.z,0.1);
    vec3 d=vec3(0,sx.y,-p.signs.x*sx.x)*p.weights.x
          +vec3(sy.x,0,-p.signs.y*sy.y)*p.weights.y
          +vec3(p.signs.z*sz.x,sz.y,0)*p.weights.z;
    d-=p.normal*dot(p.normal,d);
    return normalize(p.normal+d);
}
