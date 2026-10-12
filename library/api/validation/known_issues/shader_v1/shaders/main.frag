#version 330 core
uniform vec2 u_resolution;
uniform float u_pulse;
out vec4 fragColor;
void main(){
    vec2 p=(gl_FragCoord.xy-0.5*u_resolution)/max(u_resolution.y,1.0);
    float radius=0.2+0.08*u_pulse;
    float d=length(p)-radius;
    float light=exp(-abs(d)*60.0)*0.65;
    fragColor=vec4(vec3(0.025,0.01,0.06)+vec3(0.2,0.65,1.0)*light,1.0);
}
