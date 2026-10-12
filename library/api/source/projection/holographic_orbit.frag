#version 330 core
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_low;
uniform float u_mid;
uniform float u_high;
uniform float u_energy;
uniform float u_flux;
out vec4 fragColor;

#define PI 3.141592653589793
float hash21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float lineGrid(float v,float freq,float width){ return 1.0-smoothstep(width,width*2.2,abs(sin(v*freq))); }
float circle(vec2 p,float r,float w){ return 1.0-smoothstep(w,w*2.0,abs(length(p)-r)); }
float ellipse(vec2 p,vec2 r,float w){ float d=length(p/r)-1.0; return 1.0-smoothstep(w,w*2.0,abs(d)); }

void main(){
    vec2 uv=(2.0*gl_FragCoord.xy-u_resolution.xy)/u_resolution.y;
    float t=u_time;
    vec3 col=vec3(0.0);

    // sparse deep-space stars, highs wake the fine points
    vec2 sp=uv*vec2(150.0,100.0);
    vec2 cell=floor(sp), f=fract(sp)-0.5;
    float seed=hash21(cell);
    vec2 off=vec2(hash21(cell+3.7),hash21(cell+8.2))-0.5;
    float star=exp(-dot(f-off*0.75,f-off*0.75)*430.0)*smoothstep(0.982,0.999,seed);
    col+=mix(vec3(0.05,0.34,0.37),vec3(0.40,1.0,0.92),seed)*star*(0.18+1.35*u_high);

    vec3 holo=vec3(0.035,0.92,0.82);
    vec3 cyan=vec3(0.10,0.73,0.85);

    // floor/pedestal ellipse
    vec2 fp=uv-vec2(0.0,-0.48);
    float ring=ellipse(fp,vec2(0.44,0.105),0.018);
    float inner=1.0-smoothstep(0.82,1.02,length(fp/vec2(0.43,0.105)));
    float grain=0.5+0.5*sin(fp.x*33.0+sin(fp.y*52.0+t*0.35)*2.4+t*0.25);
    float floorGlow=inner*(0.10+0.16*grain)*(0.65+0.80*u_low);
    col+=holo*(ring*(0.55+0.75*u_low)+floorGlow);

    // vertical hologram cone/beam
    float y=uv.y+0.44;
    float beamW=mix(0.015,0.23,clamp(y/0.72,0.0,1.0));
    float beam=(1.0-smoothstep(0.0,beamW,abs(uv.x)))*smoothstep(-0.02,0.06,y)*smoothstep(0.82,0.56,y);
    beam*=0.08+0.12*u_energy+0.08*sin(t*1.7+uv.y*18.0)*u_mid;
    col+=holo*beam;

    // central wire sphere
    vec2 c=vec2(0.0,0.17);
    float R=0.235+0.012*u_low;
    vec2 p=uv-c;
    float r2=dot(p,p);
    float sphMask=1.0-smoothstep(R*R*0.96,R*R,r2);
    if(r2<R*R){
        float z=sqrt(max(0.0,R*R-r2));
        vec3 n=vec3(p/R,z/R);
        float yaw=t*(0.12+0.12*u_mid);
        float ca=cos(yaw),sa=sin(yaw);
        vec3 q=vec3(ca*n.x+sa*n.z,n.y,-sa*n.x+ca*n.z);
        float lon=atan(q.z,q.x);
        float lat=asin(clamp(q.y,-1.0,1.0));
        float g1=lineGrid(lon,9.0,0.045);
        float g2=lineGrid(lat,10.0,0.050);
        float rim=pow(1.0-z/R,1.8);
        float scan=0.5+0.5*sin((uv.y-c.y)*115.0-t*3.0);
        float wires=max(g1,g2)*(0.52+0.42*u_mid);
        col+=holo*(wires+rim*0.42+scan*0.035*(0.4+u_high))*sphMask;
    }
    col+=holo*circle(p,R,0.010)*(0.48+0.62*u_energy);

    // orbit rings around sphere
    vec2 op=p; op.y*=2.45;
    float orbit=ellipse(op,vec2(0.34,0.22),0.012);
    float orbit2=ellipse((op*mat2(cos(0.55),-sin(0.55),sin(0.55),cos(0.55))),vec2(0.31,0.19),0.012);
    col+=cyan*(orbit*0.30+orbit2*(0.18+0.24*u_mid));

    // small Saturn at upper-left
    vec2 s=uv-vec2(-0.44,0.39);
    float sat=circle(s,0.045,0.012);
    float sring=ellipse(vec2(s.x,s.y*2.8),vec2(0.085,0.028),0.035);
    col+=holo*(sat*0.48+sring*0.35)*(0.75+0.25*u_energy);

    // tiny galaxy at upper-right
    vec2 g=uv-vec2(0.48,0.40);
    float gr=length(g);
    float ga=atan(g.y,g.x);
    float spiral=exp(-gr*15.0)*pow(0.5+0.5*sin(ga*2.0+gr*42.0-t*0.22),5.0);
    col+=cyan*spiral*(0.18+0.65*u_high);

    // bass impulse through pedestal and beam, flux gives rare flash
    float pulse=exp(-abs(fp.y)*26.0)*exp(-abs(length(fp/vec2(0.45,0.11))-1.0)*8.0);
    col+=holo*pulse*u_low*0.18;
    col+=vec3(0.12,0.80,0.78)*u_flux*0.055;

    // subtle scanlines / vignette
    col*=0.96+0.04*sin(gl_FragCoord.y*PI);
    float vig=1.0-smoothstep(0.65,1.35,length(uv*vec2(0.78,1.0)));
    col*=0.62+0.38*vig;
    col=vec3(1.0)-exp(-col*1.35);
    col=pow(max(col,vec3(0.0)),vec3(1.0/2.2));
    float alpha=clamp(max(col.r,max(col.g,col.b))*2.6,0.0,0.94);
    alpha*=smoothstep(1.25,0.35,length(uv*vec2(0.72,1.0)));
    fragColor=vec4(col,alpha);
}
