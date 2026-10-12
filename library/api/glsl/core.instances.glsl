// core.instances; dependencies: core.noise, core.object_motion
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
