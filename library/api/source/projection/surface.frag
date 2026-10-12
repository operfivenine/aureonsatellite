#version 330 core
in vec3 v_world;
in vec2 v_uv;
in float v_band;
in float v_impulse;
uniform vec3 u_primary;
uniform vec3 u_secondary;
uniform vec3 u_accent;
uniform vec2 u_grid;
uniform float u_intensity;
uniform float u_treble;
out vec4 fragColor;
void main(){
    float edge=length(vec2(v_world.x/1.55,v_world.z/1.05));
    float mask=1.-smoothstep(.88,1.03,edge);
    if(mask<.002)discard;
    vec2 grid=v_uv*u_grid;
    vec2 d=abs(fract(grid-.5)-.5)/max(fwidth(grid),vec2(.001));
    float wire=1.-smoothstep(.35,1.12,min(d.x,d.y));
    float diag=abs(fract(grid.x+grid.y)-.5)/max(fwidth(grid.x+grid.y),.001);
    wire=max(wire,(1.-smoothstep(.2,.85,diag))*.30);
    vec2 dots=abs(fract(grid-.5)-.5)/max(fwidth(grid),vec2(.001));
    float node=1.-smoothstep(.55,1.65,length(dots));
    vec3 n=normalize(cross(dFdx(v_world),dFdy(v_world)));
    float light=.25+.75*abs(dot(n,normalize(vec3(-.4,1.,.65))));
    float peak=smoothstep(.12,.75,v_world.y);
    vec3 rgb=mix(u_secondary,u_primary,clamp((v_world.z+1.05)/2.1,0.,1.));
    rgb=mix(rgb,u_accent,peak*.8);
    float crest=smoothstep(.35,.82,v_world.y);
    float pulse=clamp(v_impulse,0.,1.);
    float a=(.045+.07*light+wire*(.44+.24*v_band)+node*(.14+.35*u_treble)+pulse*.10)*mask;
    rgb=rgb*(.65+.35*light)+vec3(.16)*crest*wire+vec3(.24)*node;
    rgb=mix(rgb,u_primary,pulse*.45);
    a=clamp(a*u_intensity,0.,.92);
    fragColor=vec4(clamp(rgb,0.,1.)*a,a);
}
