#include <metal_stdlib>
using namespace metal;

#include "Common.metal"

// Minimal stage template: exposure + pivoted contrast + saturation.
// Replace these blocks with your real node implementations.
kernel void ColorLooks_BasicStage(
    texture2d<half, access::read>  inTex  [[texture(0)]],
    texture2d<half, access::write> outTex [[texture(1)]],
    constant ColorLooksParamsCommon& p    [[buffer(0)]],
    uint2 gid                             [[thread_position_in_grid]])
{
    if (gid.x >= p.width || gid.y >= p.height) return;

    half4 inPx = inTex.read(gid);
    float3 rgb = float3(inPx.rgb);
    float  a   = float(inPx.a);

    // Exposure (scene-linear multiply)
    rgb *= exp2(p.exposureStops);

    // Pivoted contrast in log2 domain (simple template)
    float3 logv     = safeLog2(rgb);
    float  pivotLog = log2(max(p.pivot, 1e-6));
    logv = (logv - pivotLog) * p.contrast + pivotLog;
    rgb  = safeExp2(logv);

    // Saturation in luma/chroma form (template)
    float l = luminance(rgb);
    float3 chroma = rgb - l;
    rgb = l + chroma * p.saturation;

    // Safety floor only (avoid negatives; don’t hard clamp highs in final pipeline)
    rgb = max(rgb, float3(0.0));

    // The output is half precision: values above 65504 (the largest finite
    // half) would be written as +inf at extreme exposure/contrast, and inf
    // poisons every later stage. Clamp to the half range; this only touches
    // values that were already unrepresentable.
    rgb = min(rgb, float3(65504.0));

    outTex.write(half4(half3(rgb), half(a)), gid);
}
