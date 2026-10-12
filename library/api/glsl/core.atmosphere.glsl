// core.atmosphere; dependencies: core.math, core.noise, core.environment, core.composition
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
