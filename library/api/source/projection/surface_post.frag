#version 330 core
uniform sampler2D u_scene;
uniform vec2 u_texel;
uniform float u_glow;
in vec2 v_uv;
out vec4 fragColor;
void main(){
    vec4 core=texture(u_scene,v_uv);
    vec4 blur=vec4(0.);
    for(int i=0;i<12;i++){
        float angle=float(i)*.5235987756;
        vec2 delta=vec2(cos(angle),sin(angle))*u_texel;
        blur+=texture(u_scene,v_uv+delta*3.)*.050;
        blur+=texture(u_scene,v_uv+delta*7.)*.026;
    }
    float a=clamp(core.a+blur.a*u_glow*.65,0.,1.);
    vec3 rgb=min(core.rgb+blur.rgb*u_glow,vec3(a));
    fragColor=vec4(rgb,a);
}
