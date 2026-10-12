#version 330 core
uniform vec2 u_resolution;
uniform vec3 u_hyb_right;
uniform vec3 u_hyb_up;
uniform vec3 u_hyb_forward;
uniform vec2 u_hyb_clip;
out vec4 fragColor;
void main(){
    vec2 uv=gl_FragCoord.xy/max(u_resolution,vec2(1.0));
    fragColor=vec4(mix(vec3(0.01,0.01,0.03),vec3(0.06,0.03,0.12),uv.y),1.0);
    gl_FragDepth=1.0; // Distant sky only. Compute shared-camera depth for finite hits.
}
