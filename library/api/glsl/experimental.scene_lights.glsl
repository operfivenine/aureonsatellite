// experimental.scene_lights; dependencies: core.scene_lighting, core.object_motion
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
