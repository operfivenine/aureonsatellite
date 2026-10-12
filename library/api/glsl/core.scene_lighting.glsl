// core.scene_lighting; dependencies: core.math, core.lighting, core.materials
struct AurLightRig {
    vec3 ambientColor;
    float ambientStrength;
    vec3 keyDirection;
    vec3 keyColor;
    float keyIntensity;
    vec3 fillDirection;
    vec3 fillColor;
    float fillIntensity;
    vec3 rimDirection;
    vec3 rimColor;
    float rimIntensity;
};

AurLightRig aur_lightRig(
    vec3 ambientColor, float ambientStrength,
    vec3 keyDirection, vec3 keyColor, float keyIntensity,
    vec3 fillDirection, vec3 fillColor, float fillIntensity,
    vec3 rimDirection, vec3 rimColor, float rimIntensity) {
    AurLightRig r;
    r.ambientColor=max(ambientColor,vec3(0.0));
    r.ambientStrength=max(0.0,ambientStrength);
    r.keyDirection=normalize(keyDirection);
    r.keyColor=max(keyColor,vec3(0.0));
    r.keyIntensity=max(0.0,keyIntensity);
    r.fillDirection=normalize(fillDirection);
    r.fillColor=max(fillColor,vec3(0.0));
    r.fillIntensity=max(0.0,fillIntensity);
    r.rimDirection=normalize(rimDirection);
    r.rimColor=max(rimColor,vec3(0.0));
    r.rimIntensity=max(0.0,rimIntensity);
    return r;
}

vec3 aur_fresnelSchlick(float cosTheta, vec3 f0) {
    return f0+(1.0-f0)*pow(clamp(1.0-cosTheta,0.0,1.0),5.0);
}

float aur_distributionGGX(vec3 n, vec3 h, float roughness) {
    float a=max(0.035,roughness*roughness);
    float a2=a*a;
    float ndh=max(dot(n,h),0.0);
    float ndh2=ndh*ndh;
    float d=(ndh2*(a2-1.0)+1.0);
    return a2/max(1e-5,3.14159265359*d*d);
}

float aur_geometrySchlickGGX(float ndv, float roughness) {
    float r=roughness+1.0;
    float k=(r*r)/8.0;
    return ndv/max(1e-5,ndv*(1.0-k)+k);
}

float aur_geometrySmith(vec3 n, vec3 v, vec3 l, float roughness) {
    float ndv=max(dot(n,v),0.0);
    float ndl=max(dot(n,l),0.0);
    return aur_geometrySchlickGGX(ndv,roughness)*aur_geometrySchlickGGX(ndl,roughness);
}

vec3 aur_brdfLight(AurMaterial m, vec3 n, vec3 v, vec3 l, vec3 lightColor,
                   float intensity, float shadow) {
    float ndl=max(dot(n,l),0.0);
    float ndv=max(dot(n,v),0.0);
    if (ndl<=0.0 || ndv<=0.0 || intensity<=0.0) return vec3(0.0);
    vec3 h=normalize(v+l);
    vec3 f0=mix(vec3(0.04),m.baseColor,m.metalness);
    vec3 F=aur_fresnelSchlick(max(dot(h,v),0.0),f0);
    float D=aur_distributionGGX(n,h,m.roughness);
    float G=aur_geometrySmith(n,v,l,m.roughness);
    vec3 spec=(D*G*F)/max(1e-4,4.0*ndv*ndl);
    vec3 kd=(vec3(1.0)-F)*(1.0-m.metalness);
    vec3 diffuse=kd*m.baseColor/3.14159265359;
    return (diffuse+spec)*max(lightColor,vec3(0.0))*max(0.0,intensity)*ndl*clamp(shadow,0.0,1.0);
}

vec3 aur_ambientMaterial(AurMaterial m, vec3 ambientColor, float strength) {
    vec3 dielectric=m.baseColor*(1.0-0.45*m.metalness);
    vec3 metalTint=mix(vec3(0.0),m.baseColor,0.16*m.metalness);
    return (dielectric+metalTint)*max(ambientColor,vec3(0.0))*max(0.0,strength)*m.ao;
}

vec3 aur_rimLight(vec3 n, vec3 v, vec3 lightDirection, vec3 color, float intensity) {
    float facing=pow(clamp(1.0-dot(n,v),0.0,1.0),2.2);
    float side=0.22+0.78*max(dot(n,normalize(lightDirection)),0.0);
    return max(color,vec3(0.0))*max(0.0,intensity)*facing*side;
}

vec3 aur_shadeLightRig(AurMaterial m, vec3 n, vec3 v, AurLightRig rig, float keyShadow) {
    vec3 c=aur_ambientMaterial(m,rig.ambientColor,rig.ambientStrength);
    c+=aur_brdfLight(m,n,v,rig.keyDirection,rig.keyColor,rig.keyIntensity,keyShadow);
    c+=aur_brdfLight(m,n,v,rig.fillDirection,rig.fillColor,rig.fillIntensity,1.0);
    c+=aur_rimLight(n,v,rig.rimDirection,rig.rimColor,rig.rimIntensity);
    return c+m.emission;
}

vec3 aur_pointLight(AurMaterial m, vec3 n, vec3 v, vec3 p, vec3 lightPosition,
                    vec3 lightColor, float intensity, float radius, float shadow) {
    vec3 toL=lightPosition-p;
    float dist=max(length(toL),1e-5);
    vec3 l=toL/dist;
    float att=aur_attenuation(dist,max(1e-4,radius));
    return aur_brdfLight(m,n,v,l,lightColor,intensity*att,shadow);
}

float aur_spotCone(vec3 fromLightToPoint, vec3 lightForward, float innerCos, float outerCos) {
    float c=dot(normalize(fromLightToPoint),normalize(lightForward));
    float lo=min(innerCos,outerCos), hi=max(innerCos,outerCos);
    return smoothstep(lo,hi,c);
}

vec3 aur_spotLight(AurMaterial m, vec3 n, vec3 v, vec3 p, vec3 lightPosition,
                   vec3 lightForward, vec3 lightColor, float intensity, float radius,
                   float innerCos, float outerCos, float shadow) {
    vec3 toP=p-lightPosition;
    float cone=aur_spotCone(toP,lightForward,innerCos,outerCos);
    return aur_pointLight(m,n,v,p,lightPosition,lightColor,intensity*cone,radius,shadow);
}

vec3 aur_emissiveSpill(vec3 p, vec3 sourcePosition, vec3 sourceColor, float intensity, float radius) {
    float dist=length(p-sourcePosition);
    return max(sourceColor,vec3(0.0))*max(0.0,intensity)*aur_attenuation(dist,max(1e-4,radius));
}
