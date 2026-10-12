#version 330 core
layout(location=0) in vec3 position;
layout(location=1) in vec4 color;
layout(location=2) in vec3 normal;
uniform mat4 modelView;
uniform mat4 projection;
out vec4 vColor;
void main(){vColor=color;gl_Position=projection*modelView*vec4(position,1.0);}
