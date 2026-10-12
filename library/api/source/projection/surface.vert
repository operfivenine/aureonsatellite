#version 330 core
layout(location=0) in vec2 a_xz;
uniform mat4 u_mvp;
uniform float u_bands[64];
uniform vec4 u_waves[8];
uniform int u_wave_count;
uniform float u_time;
uniform float u_amplitude;
out vec3 v_world;
out vec2 v_uv;
out float v_band;
out float v_impulse;
float band(float x){
    float f=clamp((x+1.55)/3.1,0.,1.)*63.;
    int i=int(floor(f));
    return mix(u_bands[i],u_bands[min(i+1,63)],fract(f));
}
void main(){
    float x=a_xz.x, z=a_xz.y;
    float b=(band(x-.055)+2.*band(x)+band(x+.055))*.25;
    float shape=.32+.68*pow(.5+.5*sin(x*4.8+z*1.4-u_time*.65),2.);
    float rim=1.-smoothstep(.65,1.15,length(vec2(x/1.55,z/1.05)));
    float h=.025+.022*sin(x*3.5+z*4.+u_time*.45);
    h+=b*(.28+.73*shape)*u_amplitude*rim;
    float wave=0.;
    for(int i=0;i<8;i++){
        if(i>=u_wave_count)break;
        float age=u_waves[i].x, power=u_waves[i].y;
        float d=length(vec2(x-u_waves[i].z,z+.65));
        float delta=d-age*2.5;
        wave+=power*exp(-delta*delta*42.)*exp(-age*2.1);
    }
    h+=wave*.22*rim;
    v_world=vec3(x,h,z);v_uv=(a_xz+vec2(1.55,1.05))/vec2(3.1,2.1);
    v_band=b;v_impulse=wave;
    gl_Position=u_mvp*vec4(v_world,1.);
}
