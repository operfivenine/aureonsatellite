#version 330 core
in vec3 v_world;
in vec3 v_coord;
in float v_band;
flat in int v_ring;
uniform vec3 u_primary;
uniform vec3 u_secondary;
uniform vec3 u_accent;
uniform float u_time;
uniform float u_intensity;
uniform float u_beat;
uniform float u_treble;
out vec4 fragColor;
const float TAU=6.28318530718;
void main(){
    float theta=v_coord.x;
    float sector=fract(theta/TAU*(v_ring<3?12.:8.)+float(v_ring)*.27);
    if(v_ring<4 && sector>.82)discard;
    float lane=abs(v_coord.y);
    vec3 n=normalize(cross(dFdx(v_world),dFdy(v_world)));
    float light=.4+.6*abs(dot(n,normalize(vec3(-.45,.65,1.))));
    float bevel=smoothstep(.62,.93,lane);
    float tickphase=theta/TAU*(v_ring<3?96.:120.);
    float tickwidth=max(fwidth(tickphase),.001);
    float tick=1.-smoothstep(.035,.035+tickwidth,abs(fract(tickphase)-.5));
    tick*=smoothstep(.25,.5,lane);
    float scanner=pow(max(0.,.5+.5*cos(theta-u_time*(v_ring==1?-1.:1.)*.65)),24.);
    vec3 base=v_ring==1?u_secondary:u_primary;
    base=mix(base,u_accent,step(.68,sector)*.44);
    float front=smoothstep(-1.5,1.3,v_world.z);
    float energy=.48+.24*v_band+.15*u_beat;
    float alpha=(.30*light+bevel*.36+tick*.32+scanner*.14)*(.55+.45*front)*energy*1.7;
    if(v_ring==3)alpha*=.5;
    if(v_ring>=4)alpha*=1.15;
    alpha=clamp(alpha*u_intensity,0.,.96);
    vec3 rgb=base*(.6+.4*light)+vec3(.16)*bevel+vec3(.24)*tick;
    rgb=mix(rgb,vec3(.75,1.,1.),scanner*(.3+.25*u_treble)+u_beat*.18);
    fragColor=vec4(clamp(rgb,0.,1.)*alpha,alpha);
}
