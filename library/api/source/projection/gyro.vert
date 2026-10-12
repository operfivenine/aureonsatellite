#version 330 core
layout(location=0) in vec4 a_ring;
uniform mat4 u_mvp;
uniform mat4 u_rotations[6];
uniform float u_bands[64];
uniform float u_bass;
uniform float u_beat;
uniform float u_amplitude;
uniform float u_treble;
out vec3 v_world;
out vec3 v_coord;
out float v_band;
flat out int v_ring;
const float PI=3.14159265359;
const float radius[6]=float[6](1.34,1.12,.90,1.53,.23,.18);
const float width[6]=float[6](.065,.060,.055,.014,.025,.018);
void main(){
    int ring=int(a_ring.w+.1);
    float theta=a_ring.x;
    int bin=int(mod(theta/(2.*PI)*64.+float(ring)*19.,64.));
    float band=u_bands[bin];
    float expansion=1.+u_amplitude*(u_bass*.055+u_beat*.035);
    float r=radius[ring]*expansion+width[ring]*a_ring.y;
    float thick=ring<3?.022:.009;
    vec3 local=vec3(r*cos(theta),r*sin(theta),a_ring.z*thick);
    v_world=(u_rotations[ring]*vec4(local,1.)).xyz;
    v_coord=vec3(theta,a_ring.y,a_ring.z);
    v_band=band;v_ring=ring;
    gl_Position=u_mvp*vec4(v_world,1.);
}
