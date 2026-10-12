// core.attachments; dependencies: core.object_motion
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
