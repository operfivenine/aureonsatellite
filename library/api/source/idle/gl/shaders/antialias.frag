#version 330 core
// Scene-only FXAA with an edge endpoint search and subpixel correction.
// Display-encoded RGBA8 input; no temporal history, no UI in the input image.
uniform sampler2D u_scene;
uniform vec2 u_source_texel;
uniform vec2 u_output_resolution;
out vec4 fragColor;

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
float sampleLuma(vec2 uv) { return luma(texture(u_scene, uv).rgb); }

void main() {
    vec2 uv = gl_FragCoord.xy / u_output_resolution;
    vec2 dx = vec2(u_source_texel.x, 0.0);
    vec2 dy = vec2(0.0, u_source_texel.y);
    vec4 center = texture(u_scene, uv);
    float m = luma(center.rgb);
    float n = sampleLuma(uv + dy), s = sampleLuma(uv - dy);
    float e = sampleLuma(uv + dx), w = sampleLuma(uv - dx);
    float lo = min(m, min(min(n, s), min(e, w)));
    float hi = max(m, max(max(n, s), max(e, w)));
    float contrast = hi - lo;
    if (contrast < max(0.03125, hi * 0.125)) {
        fragColor = center;
        return;
    }
    float nw = sampleLuma(uv - dx + dy), ne = sampleLuma(uv + dx + dy);
    float sw = sampleLuma(uv - dx - dy), se = sampleLuma(uv + dx - dy);
    // Preserve isolated bright points used by all the starfields.
    float surrounding = max(max(max(n, s), max(e, w)), max(max(nw, ne), max(sw, se)));
    if (m - surrounding > contrast * 0.8) {
        fragColor = center;
        return;
    }
    float acrossY = 2.0 * abs(n + s - 2.0*m)
                  + abs(ne + se - 2.0*e) + abs(nw + sw - 2.0*w);
    float acrossX = 2.0 * abs(e + w - 2.0*m)
                  + abs(ne + nw - 2.0*n) + abs(se + sw - 2.0*s);
    bool alongX = acrossY >= acrossX;
    float plus = alongX ? n : e;
    float minus = alongX ? s : w;
    bool towardsPlus = abs(plus - m) >= abs(minus - m);
    float adjacent = towardsPlus ? plus : minus;
    float average = (adjacent + m) * 0.5;
    float gradient = abs(adjacent - m);
    vec2 normal = (alongX ? dy : dx) * (towardsPlus ? 1.0 : -1.0);
    vec2 tangent = alongX ? dx : dy;
    vec2 edgeCenter = uv + normal * 0.5;
    float negativeDistance = 1.0, positiveDistance = 1.0;
    float negative = sampleLuma(edgeCenter - tangent) - average;
    float positive = sampleLuma(edgeCenter + tangent) - average;
    bool negativeDone = abs(negative) >= gradient * 0.25;
    bool positiveDone = abs(positive) >= gradient * 0.25;
    // Bound work on long edges, keeping nearby endpoint samples precise.
    for (int i = 0; i < 10; ++i) {
        if (negativeDone && positiveDone) break;
        float stepSize = i < 4 ? 1.0 : (i < 7 ? 2.0 : 4.0);
        if (!negativeDone) {
            negativeDistance += stepSize;
            negative = sampleLuma(edgeCenter - tangent * negativeDistance) - average;
            negativeDone = abs(negative) >= gradient * 0.25;
        }
        if (!positiveDone) {
            positiveDistance += stepSize;
            positive = sampleLuma(edgeCenter + tangent * positiveDistance) - average;
            positiveDone = abs(positive) >= gradient * 0.25;
        }
    }
    bool nearestNegative = negativeDistance < positiveDistance;
    float nearestValue = nearestNegative ? negative : positive;
    float nearestDistance = min(negativeDistance, positiveDistance);
    float edgeOffset = 0.0;
    if ((nearestValue < 0.0) != (m < average)) {
        edgeOffset = 0.5 - nearestDistance / (negativeDistance + positiveDistance);
    }
    float neighbourhood = (2.0*(n+s+e+w) + nw+ne+sw+se) / 12.0;
    float subpixel = clamp(abs(neighbourhood - m) / contrast, 0.0, 1.0);
    subpixel = smoothstep(0.0, 1.0, subpixel);
    subpixel = subpixel * subpixel * 0.5;
    fragColor = texture(u_scene, uv + normal * max(edgeOffset, subpixel));
}
