"""AURS Standard Library — stable public node for PASS 01 through PASS 08.

Authors of new AURS scenes should import exactly ``aurs.standard``.  The host
keeps the implementation modular, and legacy ``core.*`` library ids remain
accepted for backward compatibility and lean historical packages, but they are
not the recommended author-facing contract.

The library is trusted host code: packages still ship declarative behavior and
GLSL only; they cannot execute Python or own OpenGL/window lifecycle.  Public
helper symbols are namespaced with ``aur_``.  The core is intentionally
theme-agnostic; future space/urban/nature/etc. content belongs in optional
``domain.*`` packs layered above this node.
"""
from dataclasses import dataclass

from .expressions import PackageError


STANDARD_LIBRARY_ID = "aurs.standard"
STANDARD_LIBRARY_API_VERSION = "1.1"
STANDARD_LIBRARY_API_MAJOR = 1
STANDARD_LIBRARY_API_MINOR = 1
STANDARD_LIBRARY_STATUS = "stable"
STANDARD_LIBRARY_NAMESPACE = "aur_"
# Internal implementation revision retained for old internal smoke tests/tools.
# It is not the package author contract; use STANDARD_LIBRARY_API_VERSION.
STANDARD_LIBRARY_REVISION = 10
STANDARD_LIBRARY_VERSION = STANDARD_LIBRARY_REVISION  # legacy internal alias
STANDARD_PASSES = (
    ("pass01.camera", "Camera", "behavior.camera.v2"),
    ("pass02.reactive", "Reactive Behavior", "behavior.temporal.v2"),
    ("pass03.environment", "World / Environment", "scene.environment_core.v1"),
    ("pass04.object", "Main Object / Geometry + Materials", "scene.object_core.v1"),
    ("pass05.lighting", "Lighting / Material Response / Scene Lighting Rig", "scene.lighting_rig.v1"),
    ("pass06.atmosphere", "Atmosphere / Volumetrics / Particles", "scene.atmosphere_core.v1"),
    ("pass07.motion", "Events / Motion / Secondary Animation", "scene.motion_core.v1"),
    ("pass08.presentation", "Polish / Quality / Presentation", "scene.presentation_core.v1"),
)

def standard_passes():
    return STANDARD_PASSES


@dataclass(frozen=True)
class ShaderModule:
    name: str
    source: str
    requires: tuple[str, ...] = ()


MODULES: dict[str, ShaderModule] = {}


def _module(name: str, source: str, requires=()):
    MODULES[name] = ShaderModule(name, source.strip() + "\n", tuple(requires))


_module("core.math", r'''
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
''')

_module("core.noise", r'''
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
''', ("core.math",))

_module("core.sdf", r'''
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
''', ("core.math",))

_module("core.lighting", r'''
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
''', ("core.math",))

_module("core.environment", r'''
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
''', ("core.math",))

_module("core.color", r'''
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
''', ("core.math",))

_module("core.composition", r'''
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
''', ("core.math",))

_module("core.camera", r'''
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
''', ("core.math",))

_module("core.geometry", r'''
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
''', ("core.math", "core.sdf"))

_module("core.materials", r'''
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
''', ("core.math", "core.lighting"))

_module("core.scene_lighting", r'''
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
''', ("core.math", "core.lighting", "core.materials"))


_module("core.atmosphere", r'''
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
''', ("core.math", "core.noise", "core.environment", "core.composition"))

_module("core.motion", r'''
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
''', ("core.math", "core.geometry"))

_module("core.presentation", r'''
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
''', ("core.math", "core.noise", "core.color", "core.composition", "core.atmosphere"))

_module("core.object", "", (
    "core.math", "core.noise", "core.sdf", "core.geometry", "core.lighting", "core.materials",
))

# Convenience bundle: a scene can opt into the complete theme-agnostic PASS 03
# toolbox with one name while individual modules remain available for lean packs.
_module("core.world", "", (
    "core.math", "core.noise", "core.sdf", "core.lighting",
    "core.environment", "core.color", "core.composition", "core.camera",
))

# Additive API 1.1 contract: no changes to the frozen API 1.0 symbols.
_module("core.object_motion", r'''
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
''', ("core.math",))

OBJECT_MOTION_V1_SYMBOLS = (
    'AurPathSample', 'AurObjectPose', 'aur_objectUnit', 'aur_objectFrame',
    'aur_objectEuler', 'aur_objectPose', 'aur_objectFollow', 'aur_objectToLocal',
    'aur_objectToWorld', 'aur_objectNormal', 'aur_objectDistance',
    'aur_pathLine', 'aur_pathOrbit', 'aur_pathShuttle', 'aur_shuttleHeading',
)

_module("core.attachments", r'''
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
''', ("core.object_motion",))

ATTACHMENTS_V1_SYMBOLS = (
    'aur_objectCompose', 'aur_objectSocket', 'aur_objectDirection',
    'aur_attachmentJet', 'aur_attachmentBeacon',
)

_module("core.instances", r'''
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
''', ("core.noise", "core.object_motion"))

INSTANCES_V1_SYMBOLS = ('AurInstance','aur_instance','aur_instanceReaction','aur_instanceRing')

_module("core.trails_lod", r'''
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
''', ("core.math",))
TRAILS_LOD_V1_SYMBOLS = ('aur_lodWeight','aur_trailFade','aur_trailSegment')

# One stable author-facing node. PASS 01 Camera and PASS 02 Reactive Behavior
# are provided by the AURS v2 host/runtime; PASS 03–08 are trusted shader
# modules resolved below the same public identity.
_module("aurs.standard", "", ("core.world", "core.object", "core.scene_lighting", "core.atmosphere", "core.motion", "core.presentation", "core.object_motion", "core.attachments", "core.instances", "core.trails_lod"))

# Frozen compatibility manifest for Standard Library API 1.0.  New releases may
# add symbols/modules, but must not silently remove or change these names while
# claiming API-major 1 compatibility.
STANDARD_LIBRARY_V1_LEGACY_IDS = (
    'core.atmosphere',
    'core.camera',
    'core.color',
    'core.composition',
    'core.environment',
    'core.geometry',
    'core.lighting',
    'core.materials',
    'core.math',
    'core.motion',
    'core.noise',
    'core.object',
    'core.presentation',
    'core.scene_lighting',
    'core.sdf',
    'core.world',
)
STANDARD_LIBRARY_V1_SYMBOLS = (
    'AurLightRig',
    'AurMaterial',
    'AurPresentation',
    'aur_aaCoverage',
    'aur_aaLine',
    'aur_addRim',
    'aur_ambientMaterial',
    'aur_applyFog',
    'aur_attenuation',
    'aur_beamCone',
    'aur_beamTube',
    'aur_bendX',
    'aur_bloomContribution',
    'aur_brdfLight',
    'aur_cameraRay',
    'aur_contrast',
    'aur_depthFade',
    'aur_detailScale',
    'aur_diffuse',
    'aur_distributionGGX',
    'aur_dither',
    'aur_dustField',
    'aur_easeInOut',
    'aur_easeSmoother',
    'aur_emissiveSpill',
    'aur_eventActive',
    'aur_eventEaseOut',
    'aur_eventGroup',
    'aur_eventProgress',
    'aur_eventPulse',
    'aur_eventRing',
    'aur_eventSeed',
    'aur_eventSigned',
    'aur_eventStrength',
    'aur_eventVariant',
    'aur_exposure',
    'aur_fbm2',
    'aur_fbm3',
    'aur_filmGrain',
    'aur_fogExp',
    'aur_fogExp2',
    'aur_fogNoise',
    'aur_followMix',
    'aur_fresnel',
    'aur_fresnelSchlick',
    'aur_geometrySchlickGGX',
    'aur_geometrySmith',
    'aur_glow',
    'aur_grade',
    'aur_hash11',
    'aur_hash21',
    'aur_hash22',
    'aur_hash31',
    'aur_hash33',
    'aur_hazeDensity',
    'aur_heightFog',
    'aur_heightFogDensity',
    'aur_layerBand',
    'aur_liftGammaGain',
    'aur_lightRig',
    'aur_lineMask',
    'aur_lit',
    'aur_lookAt',
    'aur_luminance',
    'aur_material',
    'aur_materialVariation',
    'aur_motionCycle',
    'aur_motionPingPong',
    'aur_motionSine',
    'aur_motionSmoothCycle',
    'aur_motionTriangle',
    'aur_noise2',
    'aur_noise3',
    'aur_opChamferUnion',
    'aur_opIntersect',
    'aur_opOnion',
    'aur_opRound',
    'aur_opSmoothUnion',
    'aur_opSubtract',
    'aur_opUnion',
    'aur_palette',
    'aur_phaseHG',
    'aur_pivotRotateX',
    'aur_pivotRotateY',
    'aur_pivotRotateZ',
    'aur_pointLight',
    'aur_polarRepeat',
    'aur_present',
    'aur_presentation',
    'aur_qualityLevel',
    'aur_qualitySelect',
    'aur_remap',
    'aur_repeat1',
    'aur_repeat2',
    'aur_repeat3',
    'aur_rim',
    'aur_rimLight',
    'aur_rot2',
    'aur_rotateX',
    'aur_rotateY',
    'aur_rotateZ',
    'aur_sat',
    'aur_saturation',
    'aur_screen',
    'aur_sdBox',
    'aur_sdCapsule',
    'aur_sdCylinderY',
    'aur_sdPlane',
    'aur_sdRoundBox',
    'aur_sdSphere',
    'aur_sdTorus',
    'aur_secondarySway',
    'aur_segmentDistance',
    'aur_sequenceWindow',
    'aur_shadeLightRig',
    'aur_shadeMaterial',
    'aur_shadowTerm',
    'aur_slideTransform',
    'aur_smin',
    'aur_softBloomMask',
    'aur_softClip',
    'aur_specular',
    'aur_spotCone',
    'aur_spotLight',
    'aur_subpixelOffset',
    'aur_tonemapAces',
    'aur_tonemapReinhard',
    'aur_twistY',
    'aur_vignette',
)


def public_libraries() -> tuple[str, ...]:
    """Stable author-facing library ids."""
    return (STANDARD_LIBRARY_ID,)


def legacy_libraries() -> tuple[str, ...]:
    """Frozen API-1 compatibility ids; not recommended for new scenes."""
    return STANDARD_LIBRARY_V1_LEGACY_IDS


def available_libraries() -> tuple[str, ...]:
    """All accepted ids, including legacy ``core.*`` compatibility imports."""
    return tuple(sorted(MODULES))


def resolve_libraries(value) -> tuple[str, ...]:
    """Validate names and return dependencies in deterministic injection order."""
    if value is None:
        return ()
    if not isinstance(value, list) or len(value) > 16 or any(not isinstance(x, str) for x in value):
        raise PackageError('AURS libraries must be a list of at most 16 names')
    if len(set(value)) != len(value):
        raise PackageError('AURS libraries must not contain duplicates')
    unknown=[name for name in value if name not in MODULES]
    if unknown:
        raise PackageError('Unknown AURS shader library: '+', '.join(sorted(unknown)))

    ordered=[]; visiting=set(); done=set()
    def visit(name):
        if name in done: return
        if name in visiting: raise RuntimeError('Built-in shader library dependency cycle')
        visiting.add(name)
        for dep in MODULES[name].requires: visit(dep)
        visiting.remove(name); done.add(name); ordered.append(name)
    for name in value: visit(name)
    return tuple(ordered)


def library_source(libraries: tuple[str, ...]) -> str:
    if not libraries:
        return ''
    blocks=['\n// ---- Aureon AURS Standard Library (trusted host code) ----\n']
    for name in libraries:
        source=MODULES[name].source
        if source:
            blocks.append('// module: '+name+'\n'+source+'\n')
    blocks.append('// ---- end Aureon AURS Standard Library ----\n')
    return ''.join(blocks)

# Frozen additive API 1.1 surface; API 1.0 symbols remain independently preserved.
STANDARD_LIBRARY_V1_1_SYMBOLS = (STANDARD_LIBRARY_V1_SYMBOLS + OBJECT_MOTION_V1_SYMBOLS + ATTACHMENTS_V1_SYMBOLS + INSTANCES_V1_SYMBOLS + TRAILS_LOD_V1_SYMBOLS)
STANDARD_LIBRARY_V1_1_FEATURES = ('scene.object_motion.v1', 'scene.attachments.v1', 'scene.instances.v1', 'scene.trails_lod.v1')


# Experimental and opt-in: does not expand the stable aurs.standard bundle.
_module("experimental.texture_materials", r'''
// Inputs are sampled linear values. Hardware decodes sRGB color/emission maps.
// ORM: R=ambient occlusion, G=roughness, B=metalness.
AurMaterial aur_textureMaterial(vec3 colorSample, vec3 ormSample,
    vec3 emissionSample, vec3 tint, float roughnessScale,
    float metalnessScale, float aoStrength, float emissionStrength) {
    return aur_material(colorSample*max(tint,vec3(0.0)),
        ormSample.g*max(roughnessScale,0.0),
        ormSample.b*max(metalnessScale,0.0),
        emissionSample*max(emissionStrength,0.0),
        mix(1.0,clamp(ormSample.r,0.0,1.0),clamp(aoStrength,0.0,1.0)));
}
// Separate map channels can be assembled without requiring extra samplers.
vec3 aur_packORM(float occlusion, float roughness, float metalness) {
    return clamp(vec3(occlusion,roughness,metalness),0.0,1.0);
}
vec2 aur_textureUV(vec2 uv, vec2 tiling, vec2 offset) {
    return uv*tiling+offset;
}
''', ("core.materials",))


# Tangent-space normal mapping: explicit UV frame, no screen derivatives.
_module("experimental.normal_mapping", r'''
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
''')

# Opt-in triplanar mapping. No derivatives or texture reads inside this module.
_module("experimental.triplanar", r'''
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
''', ("experimental.normal_mapping",))

# Experimental scene-owned lights; host lifecycle and stable API are unchanged.
_module("experimental.scene_lights", r'''
struct AurSceneLight {
    int kind;
    vec3 position; vec3 direction; vec3 color;
    float intensity; float radius; float innerCos; float outerCos;
};
// Direction points FROM light towards scene for all kinds (including directional).
AurSceneLight aur_sceneDirectional(vec3 direction, vec3 color, float intensity) {
    AurSceneLight l; l.kind=0; l.position=vec3(0);
    l.direction=aur_objectUnit(direction,vec3(0,-1,0));
    l.color=max(color,vec3(0)); l.intensity=max(intensity,0.0);
    l.radius=1.0; l.innerCos=1.0; l.outerCos=0.0; return l;
}
AurSceneLight aur_scenePoint(vec3 position, vec3 color, float intensity, float radius) {
    AurSceneLight l=aur_sceneDirectional(vec3(0,-1,0),color,intensity);
    l.kind=1; l.position=position; l.radius=max(radius,0.0001); return l;
}
AurSceneLight aur_sceneSpot(vec3 position, vec3 direction, vec3 color,
    float intensity, float radius, float innerDegrees, float outerDegrees) {
    AurSceneLight l=aur_scenePoint(position,color,intensity,radius);
    l.kind=2; l.direction=aur_objectUnit(direction,vec3(0,-1,0));
    float inner=clamp(min(innerDegrees,outerDegrees),0.0,89.8);
    float outer=clamp(max(innerDegrees,outerDegrees),inner+0.1,89.9);
    l.innerCos=cos(radians(inner)); l.outerCos=cos(radians(outer)); return l;
}
// Local source -> world. Radius remains in world units, independent of object scale.
AurSceneLight aur_sceneLightAttach(AurSceneLight l, AurObjectPose pose) {
    l.position=aur_objectToWorld(pose,l.position);
    l.direction=aur_objectUnit(pose.rotation*l.direction,vec3(0,-1,0)); return l;
}
AurSceneLight aur_sceneLightGain(AurSceneLight l, float gain) {
    l.intensity*=max(gain,0.0); return l;
}
vec3 aur_sceneLightShade(AurSceneLight l, AurMaterial material,
    vec3 position, vec3 normal, vec3 viewDirection, float visibility) {
    if(l.intensity<=0.0 || visibility<=0.0)return vec3(0);
    vec3 n=aur_objectUnit(normal,vec3(0,1,0));
    vec3 v=aur_objectUnit(viewDirection,n);
    if(l.kind==0)return aur_brdfLight(material,n,v,-l.direction,l.color,l.intensity,visibility);
    vec3 delta=l.position-position;
    float d2=dot(delta,delta);
    if(d2<1e-10)return vec3(0);
    vec3 direction=delta*inversesqrt(d2);
    float gain=aur_attenuation(sqrt(d2),l.radius);
    if(l.kind==2)gain*=smoothstep(l.outerCos,l.innerCos,dot(-direction,l.direction));
    return aur_brdfLight(material,n,v,direction,l.color,l.intensity*gain,visibility);
}
''', ("core.scene_lighting", "core.object_motion"))

# Accepted TEX03 RC2 filtering, factored into reusable opt-in helpers.
_module("experimental.normal_filtering", r'''
// Inputs are five filtered RGB normal samples in the same tangent frame:
// center and +/- half-pixel UV offsets on U and V. Texture reads stay in the scene.
float aur_normalVariance5(vec3 centerSample, vec3 plusU, vec3 minusU,
    vec3 plusV, vec3 minusV, float strength, float greenSign) {
    if(strength<=0.0)return 0.0;
    vec3 mean=(aur_decodeNormal(centerSample,strength,greenSign)
        +aur_decodeNormal(plusU,strength,greenSign)
        +aur_decodeNormal(minusU,strength,greenSign)
        +aur_decodeNormal(plusV,strength,greenSign)
        +aur_decodeNormal(minusV,strength,greenSign))*0.2;
    float lost=max(0.0,1.0-length(centerSample*2.0-1.0)-0.008)*strength*strength;
    return clamp(1.0-dot(mean,mean)+lost,0.0,0.25);
}
float aur_filteredRoughness(float roughness, float normalVariance) {
    float r=clamp(roughness,0.02,1.0);
    return clamp(pow(pow(r,4.0)+clamp(normalVariance,0.0,0.25),0.25),0.02,1.0);
}
AurMaterial aur_filterNormalMaterial(AurMaterial material, float normalVariance) {
    material.roughness=aur_filteredRoughness(material.roughness,normalVariance);
    return material;
}
''', ("experimental.normal_mapping", "core.materials"))
