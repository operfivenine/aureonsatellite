// core.presentation; dependencies: core.math, core.noise, core.color, core.composition, core.atmosphere
// PASS 08 — final single-pass presentation and quality helpers.
float aur_luminance(vec3 c) { return dot(max(c,vec3(0.0)),vec3(0.2126,0.7152,0.0722)); }
float aur_qualityLevel() { return AUR_QUALITY_LEVEL; }
float aur_qualitySelect(float lowValue, float mediumValue, float highValue) {
    return AUR_QUALITY_LEVEL < 0.5 ? lowValue : (AUR_QUALITY_LEVEL > 1.5 ? highValue : mediumValue);
}
vec3 aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue) {
    return AUR_QUALITY_LEVEL < 0.5 ? lowValue : (AUR_QUALITY_LEVEL > 1.5 ? highValue : mediumValue);
}
float aur_qualitySelect(float lowValue, float mediumValue, float highValue, float extremeValue) {
    return AUR_QUALITY_LEVEL>2.5?extremeValue:aur_qualitySelect(lowValue,mediumValue,highValue);
}
vec3 aur_qualitySelect(vec3 lowValue, vec3 mediumValue, vec3 highValue, vec3 extremeValue) {
    return AUR_QUALITY_LEVEL>2.5?extremeValue:aur_qualitySelect(lowValue,mediumValue,highValue);
}
float aur_detailScale(float lowValue, float mediumValue, float highValue) {
    return aur_qualitySelect(lowValue,mediumValue,highValue);
}
float aur_aaCoverage(float signedDistance) {
    float w=max(fwidth(signedDistance),1e-5);
    return 1.0-smoothstep(-w,w,signedDistance);
}
float aur_aaLine(float signedDistance, float halfWidth) {
    float w=max(fwidth(signedDistance),1e-5);
    return 1.0-smoothstep(halfWidth-w,halfWidth+w,abs(signedDistance));
}
vec2 aur_subpixelOffset(int sampleIndex) {
    const vec2 P[8]=vec2[8](
        vec2(-0.375,-0.125), vec2(0.125,-0.375), vec2(0.375,0.125), vec2(-0.125,0.375),
        vec2(-0.4375,0.3125), vec2(0.3125,0.4375), vec2(0.4375,-0.3125), vec2(-0.3125,-0.4375)
    );
    return P[clamp(sampleIndex,0,7)];
}
vec3 aur_exposure(vec3 color, float stops) { return max(color,vec3(0.0))*exp2(stops); }
vec3 aur_liftGammaGain(vec3 color, vec3 lift, vec3 gammaValue, vec3 gain) {
    vec3 c=max(color+lift,vec3(0.0))*max(gain,vec3(0.0));
    return pow(c,vec3(1.0)/max(gammaValue,vec3(0.05)));
}
vec3 aur_grade(vec3 color, float contrastValue, float saturationValue, vec3 tint) {
    vec3 c=aur_contrast(color,max(0.0,contrastValue));
    c=aur_saturation(c,max(0.0,saturationValue));
    return max(c,vec3(0.0))*max(tint,vec3(0.0));
}
vec3 aur_softClip(vec3 color, float shoulder) {
    float s=max(0.01,shoulder);
    vec3 c=max(color,vec3(0.0));
    return c/(vec3(1.0)+c/s);
}
float aur_filmGrain(vec2 pixel, float timeValue, float amount) {
    float n=aur_hash21(pixel+vec2(fract(timeValue*0.754877666)*4096.0,fract(timeValue*0.569840296)*2048.0));
    return (n-0.5)*2.0*max(0.0,amount);
}
vec3 aur_dither(vec3 color, vec2 pixel, float amount) {
    float n=aur_hash21(pixel+vec2(19.17,73.41))-0.5;
    return color+n*max(0.0,amount);
}
struct AurPresentation {
    float exposure;
    float contrast;
    float saturation;
    float vignette;
    float bloomThreshold;
    float bloomKnee;
    float bloomStrength;
    float grain;
    float dither;
    vec3 tint;
};
AurPresentation aur_presentation(float exposureValue, float contrastValue, float saturationValue,
    float vignetteValue, float bloomThreshold, float bloomKnee, float bloomStrength,
    float grainValue, float ditherValue, vec3 tintValue) {
    AurPresentation p;
    p.exposure=clamp(exposureValue,-8.0,8.0);
    p.contrast=clamp(contrastValue,0.0,4.0);
    p.saturation=clamp(saturationValue,0.0,4.0);
    p.vignette=clamp(vignetteValue,0.0,2.0);
    p.bloomThreshold=max(0.0,bloomThreshold);
    p.bloomKnee=max(1e-4,bloomKnee);
    p.bloomStrength=clamp(bloomStrength,0.0,2.0);
    p.grain=clamp(grainValue,0.0,0.20);
    p.dither=clamp(ditherValue,0.0,0.05);
    p.tint=max(tintValue,vec3(0.0));
    return p;
}
vec3 aur_present(vec3 hdrColor, vec2 centeredUv, vec2 fragCoord, float timeValue, AurPresentation p) {
    vec3 c=max(hdrColor,vec3(0.0));
    float lum=aur_luminance(c);
    float bm=aur_softBloomMask(lum,p.bloomThreshold,p.bloomKnee);
    c+=aur_bloomContribution(c,bm,p.bloomStrength);
    c=aur_exposure(c,p.exposure);
    c=aur_tonemapAces(c);
    c=aur_grade(c,p.contrast,p.saturation,p.tint);
    c*=aur_vignette(centeredUv,p.vignette);
    c+=aur_filmGrain(fragCoord,timeValue,p.grain);
    c=aur_dither(c,fragCoord,p.dither);
    return clamp(c,vec3(0.0),vec3(1.0));
}
