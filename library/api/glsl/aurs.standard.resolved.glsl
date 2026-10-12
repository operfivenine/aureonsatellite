// ---- Aureon AURS Standard Library (trusted host code) ----
// module: core.math
float aur_sat(float x) { return clamp(x, 0.0, 1.0); }
vec2 aur_sat(vec2 x) { return clamp(x, 0.0, 1.0); }
vec3 aur_sat(vec3 x) { return clamp(x, 0.0, 1.0); }
float aur_remap(float x, float a, float b, float c, float d) {
    return mix(c, d, clamp((x-a) / max(1e-6, b-a), 0.0, 1.0));
}
mat2 aur_rot2(float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, -s, s, c);
}
float aur_smin(float a, float b, float k) {
    float h = clamp(0.5 + 0.5*(b-a)/max(1e-6,k), 0.0, 1.0);
    return mix(b, a, h) - k*h*(1.0-h);
}
float aur_repeat1(float x, float spacing) {
    return mod(x + 0.5*spacing, spacing) - 0.5*spacing;
}
vec2 aur_repeat2(vec2 p, vec2 spacing) {
    return mod(p + 0.5*spacing, spacing) - 0.5*spacing;
}

// module: core.noise
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

// module: core.sdf
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

// module: core.lighting
float aur_diffuse(vec3 n, vec3 l) { return max(dot(n,l),0.0); }
float aur_fresnel(vec3 n, vec3 v, float power) {
    return pow(1.0-max(dot(n,v),0.0), max(0.01,power));
}
float aur_rim(vec3 n, vec3 v, float width, float power) {
    float r=pow(1.0-max(dot(n,v),0.0),max(0.01,power));
    return smoothstep(max(0.0,1.0-width),1.0,r);
}
float aur_specular(vec3 n, vec3 l, vec3 v, float roughness) {
    vec3 h=normalize(l+v);
    float p=mix(96.0,4.0,clamp(roughness,0.0,1.0));
    return pow(max(dot(n,h),0.0),p);
}
float aur_attenuation(float distanceToLight, float radius) {
    float x=distanceToLight/max(1e-4,radius);
    return 1.0/(1.0+x*x);
}
float aur_shadowTerm(float currentShadow, float fieldDistance, float travel, float softness) {
    float penumbra=softness*fieldDistance/max(1e-4,travel);
    return min(currentShadow,clamp(penumbra,0.0,1.0));
}
vec3 aur_lit(vec3 baseColor, vec3 n, vec3 l, vec3 v, vec3 lightColor,
             float diffuseGain, float specularGain, float roughness) {
    float d=aur_diffuse(n,l)*diffuseGain;
    float s=aur_specular(n,l,v,roughness)*specularGain;
    return baseColor*(0.08+d)*lightColor + lightColor*s;
}

// module: core.environment
float aur_fogExp(float distanceValue, float density) {
    return 1.0-exp(-max(0.0,distanceValue)*max(0.0,density));
}
float aur_fogExp2(float distanceValue, float density) {
    float x=max(0.0,distanceValue)*max(0.0,density);
    return 1.0-exp(-x*x);
}
float aur_depthFade(float distanceValue, float nearDistance, float farDistance) {
    return smoothstep(nearDistance, max(nearDistance+1e-4,farDistance), distanceValue);
}
float aur_heightFog(float worldY, float baseHeight, float falloff) {
    return exp(-max(0.0,worldY-baseHeight)*max(0.0,falloff));
}
vec3 aur_applyFog(vec3 color, vec3 fogColor, float fogAmount) {
    return mix(color,fogColor,clamp(fogAmount,0.0,1.0));
}

// module: core.color
vec3 aur_palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a+b*cos(6.28318530718*(c*t+d));
}
vec3 aur_tonemapReinhard(vec3 c) { return c/(1.0+c); }
vec3 aur_tonemapAces(vec3 x) {
    const float a=2.51, b=0.03, c=2.43, d=0.59, e=0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.0,1.0);
}
vec3 aur_saturation(vec3 c, float amount) {
    float l=dot(c,vec3(0.2126,0.7152,0.0722));
    return mix(vec3(l),c,amount);
}
vec3 aur_contrast(vec3 c, float amount) { return (c-0.5)*amount+0.5; }

// module: core.composition
float aur_glow(float signedDistance, float width, float intensity) {
    return intensity*exp(-abs(signedDistance)/max(1e-4,width));
}
float aur_lineMask(float distanceValue, float width, float softness) {
    return 1.0-smoothstep(width,max(width+1e-5,width+softness),abs(distanceValue));
}
float aur_vignette(vec2 centeredUv, float strength) {
    float r=dot(centeredUv,centeredUv);
    return clamp(1.0-r*max(0.0,strength),0.0,1.0);
}
vec3 aur_screen(vec3 base, vec3 layer) { return 1.0-(1.0-base)*(1.0-layer); }

// module: core.camera
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

// module: core.world


// module: core.geometry
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

// module: core.materials
struct AurMaterial {
    vec3 baseColor;
    vec3 emission;
    float roughness;
    float metalness;
    float ao;
};
AurMaterial aur_material(vec3 baseColor, float roughness, float metalness, vec3 emission, float ao) {
    AurMaterial m;
    m.baseColor=max(baseColor,vec3(0.0));
    m.emission=max(emission,vec3(0.0));
    m.roughness=clamp(roughness,0.02,1.0);
    m.metalness=clamp(metalness,0.0,1.0);
    m.ao=clamp(ao,0.0,1.0);
    return m;
}
vec3 aur_materialVariation(vec3 baseColor, float variation, float amount) {
    float v=(clamp(variation,0.0,1.0)-0.5)*2.0;
    return max(vec3(0.0),baseColor*(1.0+v*amount));
}
vec3 aur_shadeMaterial(AurMaterial m, vec3 n, vec3 l, vec3 v, vec3 lightColor,
                       float lightStrength, float shadow) {
    float ndl=aur_diffuse(n,l);
    float spec=aur_specular(n,l,v,m.roughness);
    vec3 f0=mix(vec3(0.04),m.baseColor,m.metalness);
    vec3 diffuse=m.baseColor*(1.0-m.metalness)*ndl;
    vec3 reflected=f0*spec*(0.30+1.70*(1.0-m.roughness));
    vec3 ambient=m.baseColor*(0.035+0.075*m.ao);
    return (ambient+(diffuse+reflected)*lightColor*max(0.0,lightStrength))*clamp(shadow,0.0,1.0)+m.emission;
}
vec3 aur_addRim(vec3 color, vec3 rimColor, vec3 n, vec3 v, float power, float strength) {
    return color+rimColor*aur_fresnel(n,v,power)*max(0.0,strength);
}

// module: core.object


// module: core.scene_lighting
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

// module: core.atmosphere
float aur_phaseHG(float cosTheta, float g) {
    float gg=clamp(g,-0.95,0.95);
    float g2=gg*gg;
    float den=max(1e-4,pow(1.0+g2-2.0*gg*cosTheta,1.5));
    return (1.0-g2)/(12.5663706144*den);
}

float aur_layerBand(float worldY, float centerY, float halfWidth, float feather) {
    float d=abs(worldY-centerY)-max(0.0,halfWidth);
    return 1.0-smoothstep(0.0,max(1e-4,feather),d);
}

float aur_heightFogDensity(vec3 p, float baseHeight, float density, float falloff) {
    float h=max(0.0,p.y-baseHeight);
    return max(0.0,density)*exp(-h*max(0.0,falloff));
}

float aur_hazeDensity(float travel, float startDistance, float endDistance, float density) {
    float span=max(1e-4,endDistance-startDistance);
    float ramp=smoothstep(startDistance,endDistance,travel);
    return ramp*max(0.0,density)/span;
}

float aur_segmentDistance(vec3 p, vec3 a, vec3 b) {
    vec3 pa=p-a, ba=b-a;
    float h=clamp(dot(pa,ba)/max(1e-6,dot(ba,ba)),0.0,1.0);
    return length(pa-ba*h);
}

float aur_beamTube(vec3 p, vec3 a, vec3 b, float radius, float feather) {
    float d=aur_segmentDistance(p,a,b);
    float r=max(1e-4,radius);
    return 1.0-smoothstep(r,r+max(1e-4,feather),d);
}

float aur_beamCone(vec3 p, vec3 origin, vec3 direction, float lengthValue,
                   float radiusNear, float radiusFar, float feather) {
    vec3 d=normalize(direction);
    vec3 rel=p-origin;
    float t=dot(rel,d);
    float len=max(1e-4,lengthValue);
    if (t<0.0 || t>len) return 0.0;
    float radius=mix(max(1e-4,radiusNear),max(1e-4,radiusFar),t/len);
    float radial=length(rel-d*t);
    float side=1.0-smoothstep(radius,radius+max(1e-4,feather),radial);
    float edge=min(0.35,len*0.12);
    float ends=smoothstep(0.0,edge,t)*(1.0-smoothstep(len-edge,len,t));
    return side*ends;
}

vec3 aur_hash33(vec3 p) {
    return vec3(
        aur_hash31(p+vec3(17.1, 3.7,11.9)),
        aur_hash31(p+vec3( 5.3,29.1, 2.4)),
        aur_hash31(p+vec3(41.7,13.2,23.8))
    );
}

float aur_dustField(vec3 p, float cellSize, float particleRadius, float density, float seed) {
    float cs=max(0.03,cellSize);
    vec3 q=p/cs;
    vec3 cell=floor(q);
    vec3 local=fract(q)-0.5;
    vec3 rnd=aur_hash33(cell+vec3(seed,seed*1.73,seed*2.31));
    float present=step(1.0-clamp(density,0.0,1.0),rnd.x);
    vec3 center=(rnd.yzx-0.5)*0.78;
    float d=length(local-center);
    float r=clamp(particleRadius/cs,0.005,0.45);
    return present*(1.0-smoothstep(r,r*2.2,d));
}

float aur_fogNoise(vec3 p, float scale, float amount) {
    float n=aur_fbm3(p*max(0.001,scale));
    return mix(1.0,0.55+0.90*n,clamp(amount,0.0,1.0));
}

void aur_scatterStep(inout vec3 scatter, inout float transmittance,
                     vec3 sourceColor, float density, float stepLength) {
    float optical=max(0.0,density)*max(0.0,stepLength);
    float extinction=exp(-optical);
    float gathered=1.0-extinction;
    scatter+=transmittance*max(sourceColor,vec3(0.0))*gathered;
    transmittance*=extinction;
}

float aur_softBloomMask(float luminanceValue, float threshold, float knee) {
    float x=max(0.0,luminanceValue-threshold);
    float k=max(1e-4,knee);
    return x/(x+k);
}

vec3 aur_bloomContribution(vec3 emissionColor, float mask, float strength) {
    return max(emissionColor,vec3(0.0))*clamp(mask,0.0,1.0)*max(0.0,strength);
}

// module: core.motion
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

// module: core.presentation
// PASS 08 — final single-pass presentation and quality helpers.
float aur_luminance(vec3 c) { return dot(max(c,vec3(0.0)),vec3(0.2126,0.7152,0.0722)); }
float aur_qualityLevel() { return AUR_QUALITY_LEVEL; }
float aur_qualitySelect(float lowValue, float mediumValue, float highValue) {
    return AUR_QUALITY_LEVEL < 0.5 ? lowValue : (AUR_QUALITY_LEVEL > 1.5 ? highValue : mediumValue);
}
vec3 aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue) {
    return AUR_QUALITY_LEVEL < 0.5 ? lowValue : (AUR_QUALITY_LEVEL > 1.5 ? highValue : mediumValue);
}
float aur_qualitySelect(float lowValue, float mediumValue, float highValue, float extremeValue) {
    return AUR_QUALITY_LEVEL>2.5?extremeValue:aur_qualitySelect(lowValue,mediumValue,highValue);
}
vec3 aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue, vec3 extremeValue) {
    return AUR_QUALITY_LEVEL>2.5?extremeValue:aur_qualitySelect(lowValue,mediumValue,highValue);
}
float aur_detailScale(float lowValue, float mediumValue, float highValue) {
    return aur_qualitySelect(lowValue,mediumValue,highValue);
}
float aur_aaCoverage(float signedDistance) {
    float w=max(fwidth(signedDistance),1e-5);
    return 1.0-smoothstep(-w,w,signedDistance);
}
float aur_aaLine(float signedDistance, float halfWidth) {
    float w=max(fwidth(signedDistance),1e-5);
    return 1.0-smoothstep(halfWidth-w,halfWidth+w,abs(signedDistance));
}
vec2 aur_subpixelOffset(int sampleIndex) {
    const vec2 P[8]=vec2[8](
        vec2(-0.375,-0.125), vec2(0.125,-0.375), vec2(0.375,0.125), vec2(-0.125,0.375),
        vec2(-0.4375,0.3125), vec2(0.3125,0.4375), vec2(0.4375,-0.3125), vec2(-0.3125,-0.4375)
    );
    return P[clamp(sampleIndex,0,7)];
}
vec3 aur_exposure(vec3 color, float stops) { return max(color,vec3(0.0))*exp2(stops); }
vec3 aur_liftGammaGain(vec3 color, vec3 lift, vec3 gammaValue, vec3 gain) {
    vec3 c=max(color+lift,vec3(0.0))*max(gain,vec3(0.0));
    return pow(c,vec3(1.0)/max(gammaValue,vec3(0.05)));
}
vec3 aur_grade(vec3 color, float contrastValue, float saturationValue, vec3 tint) {
    vec3 c=aur_contrast(color,max(0.0,contrastValue));
    c=aur_saturation(c,max(0.0,saturationValue));
    return max(c,vec3(0.0))*max(tint,vec3(0.0));
}
vec3 aur_softClip(vec3 color, float shoulder) {
    float s=max(0.01,shoulder);
    vec3 c=max(color,vec3(0.0));
    return c/(vec3(1.0)+c/s);
}
float aur_filmGrain(vec2 pixel, float timeValue, float amount) {
    float n=aur_hash21(pixel+vec2(fract(timeValue*0.754877666)*4096.0,fract(timeValue*0.569840296)*2048.0));
    return (n-0.5)*2.0*max(0.0,amount);
}
vec3 aur_dither(vec3 color, vec2 pixel, float amount) {
    float n=aur_hash21(pixel+vec2(19.17,73.41))-0.5;
    return color+n*max(0.0,amount);
}
struct AurPresentation {
    float exposure;
    float contrast;
    float saturation;
    float vignette;
    float bloomThreshold;
    float bloomKnee;
    float bloomStrength;
    float grain;
    float dither;
    vec3 tint;
};
AurPresentation aur_presentation(float exposureValue, float contrastValue, float saturationValue,
    float vignetteValue, float bloomThreshold, float bloomKnee, float bloomStrength,
    float grainValue, float ditherValue, vec3 tintValue) {
    AurPresentation p;
    p.exposure=clamp(exposureValue,-8.0,8.0);
    p.contrast=clamp(contrastValue,0.0,4.0);
    p.saturation=clamp(saturationValue,0.0,4.0);
    p.vignette=clamp(vignetteValue,0.0,2.0);
    p.bloomThreshold=max(0.0,bloomThreshold);
    p.bloomKnee=max(1e-4,bloomKnee);
    p.bloomStrength=clamp(bloomStrength,0.0,2.0);
    p.grain=clamp(grainValue,0.0,0.20);
    p.dither=clamp(ditherValue,0.0,0.05);
    p.tint=max(tintValue,vec3(0.0));
    return p;
}
vec3 aur_present(vec3 hdrColor, vec2 centeredUv, vec2 fragCoord, float timeValue, AurPresentation p) {
    vec3 c=max(hdrColor,vec3(0.0));
    float lum=aur_luminance(c);
    float bm=aur_softBloomMask(lum,p.bloomThreshold,p.bloomKnee);
    c+=aur_bloomContribution(c,bm,p.bloomStrength);
    c=aur_exposure(c,p.exposure);
    c=aur_tonemapAces(c);
    c=aur_grade(c,p.contrast,p.saturation,p.tint);
    c*=aur_vignette(centeredUv,p.vignette);
    c+=aur_filmGrain(fragCoord,timeValue,p.grain);
    c=aur_dither(c,fragCoord,p.dither);
    return clamp(c,vec3(0.0),vec3(1.0));
}

// module: core.object_motion
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

// module: core.attachments
// Explicit composition: local socket/child pose is expressed in parent units.
AurObjectPose aur_objectCompose(AurObjectPose parent, AurObjectPose child) {
    AurObjectPose result;
    result.position=aur_objectToWorld(parent,child.position);
    result.rotation=parent.rotation*child.rotation;
    result.scale=parent.scale*child.scale;
    return result;
}
AurObjectPose aur_objectSocket(AurObjectPose parent,vec3 localPosition,vec3 localAngles) {
    return aur_objectCompose(parent,aur_objectPose(localPosition,localAngles,1.0));
}
vec3 aur_objectDirection(AurObjectPose pose,vec3 direction) {
    return aur_objectUnit(pose.rotation*direction,vec3(0,0,1));
}
// Density in socket space; exhaust travels along local -Z. No history buffer.
float aur_attachmentJet(vec3 worldPoint,AurObjectPose socket,float lengthValue,float radius,float timeValue,float strength) {
    if(lengthValue<=0.0 || radius<=0.0 || strength<=0.0)return 0.0;
    vec3 q=aur_objectToLocal(socket,worldPoint);
    float axial=-q.z/lengthValue;
    if(axial<0.0 || axial>1.0)return 0.0;
    float width=radius*mix(1.0,0.12,axial);
    float radial=1.0-smoothstep(width*0.15,width,length(q.xy));
    float ends=smoothstep(0.0,0.035,axial)*(1.0-smoothstep(0.65,1.0,axial));
    float flow=0.78+0.22*sin(axial*32.0-timeValue*18.0);
    return radial*ends*flow*clamp(strength,0.0,8.0);
}
float aur_attachmentBeacon(vec3 worldPoint,AurObjectPose socket,float radius,float timeValue,float frequency,float phase) {
    if(radius<=0.0)return 0.0;
    vec3 q=aur_objectToLocal(socket,worldPoint);
    float pulse=pow(0.5+0.5*cos(6.28318530718*(timeValue*frequency+phase)),8.0);
    return exp(-dot(q,q)/(radius*radius))*(0.12+0.88*pulse);
}

// module: core.instances
// Stable per-index descriptors. Count is deliberately absent: adding members
// does not reshuffle previous seeds, phases, scales or audio assignments.
struct AurInstance {
    float seed; float phase; float speed; float scale; float gain; int band;
};
AurInstance aur_instance(int index,float groupSeed,vec2 speedRange,vec2 scaleRange,vec2 gainRange) {
    float key=float(max(index,0))+floor(clamp(groupSeed,0.0,65535.0))*0.173;
    AurInstance v;
    v.seed=aur_hash11(key+13.71);
    v.phase=aur_hash11(key+41.39);
    v.speed=mix(min(speedRange.x,speedRange.y),max(speedRange.x,speedRange.y),aur_hash11(key+83.17));
    v.scale=max(0.0001,mix(min(scaleRange.x,scaleRange.y),max(scaleRange.x,scaleRange.y),aur_hash11(key+127.53)));
    v.gain=max(0.0,mix(min(gainRange.x,gainRange.y),max(gainRange.x,gainRange.y),aur_hash11(key+179.31)));
    v.band=int(min(31.0,floor(aur_hash11(key+223.79)*32.0)));
    return v;
}
float aur_instanceReaction(AurInstance instance,float bandValue,float broadValue,float broadMix) {
    return clamp(mix(max(0.0,bandValue),max(0.0,broadValue),clamp(broadMix,0.0,1.0))*instance.gain,0.0,1.0);
}
// Ring placement is for authored formation offsets, not collision avoidance.
vec3 aur_instanceRing(int index,int count,float radius,float phase) {
    float angle=6.28318530718*(float(index)/float(max(1,count))+phase);
    return vec3(cos(angle),0,sin(angle))*max(0.0,radius);
}

// module: core.trails_lod
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

// module: aurs.standard


// ---- end Aureon AURS Standard Library ----
