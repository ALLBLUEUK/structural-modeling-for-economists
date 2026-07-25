using Test
using StatsBase

const PACKAGE_ROOT = normpath(joinpath(@__DIR__, ".."))
const DEFAULT_ORIGINAL = normpath(joinpath(
    PACKAGE_ROOT, "..", "..", "SpatialModelSample.jl"
))
const ORIGINAL_SCRIPT = get(
    ENV,
    "ORIGINAL_LECTURE_SCRIPT",
    DEFAULT_ORIGINAL,
)

include(joinpath(PACKAGE_ROOT, "src", "BaselineModel.jl"))
using .BaselineModel

@testset "Parity with original lecture code" begin
    @test isfile(ORIGINAL_SCRIPT)

    original = Module(:OriginalLectureBenchmark)
    original_source = read(ORIGINAL_SCRIPT, String)
    original_source = replace(
        original_source,
        r"(?m)^using Plots\s*$" => "",
        r"(?m)^heatmap\(.*\)\s*$" => "",
    )
    counterfactual_marker =
        "####################################counterfactual"
    marker_position = findfirst(counterfactual_marker, original_source)
    if marker_position !== nothing
        original_source = original_source[begin:(first(marker_position) - 1)]
    end
    redirect_stdout(devnull) do
        Base.include_string(original, original_source, ORIGINAL_SCRIPT)
    end

    fund = build_baseline_fundamentals(legacy_baseline_settings())
    sol = solve_level_equilibrium(fund)
    original_d = getproperty(original, :icebergcost) .*
                 getproperty(original, :bord) .*
                 getproperty(original, :bordc)
    west = fund.Iwest .== 1.0
    original_wage_scale = geomean(getproperty(original, :w)[west])

    @test fund.A ≈ getproperty(original, :A) rtol=1e-13 atol=0.0
    @test fund.H == getproperty(original, :H)
    @test fund.d ≈ original_d rtol=1e-13 atol=0.0
    @test sol.w ≈
          getproperty(original, :w) ./ original_wage_scale rtol=1e-12 atol=1e-12
    @test sol.L ≈ getproperty(original, :L) rtol=1e-12 atol=1e-9
    @test sol.P ≈
          vec(getproperty(original, :P)) ./ original_wage_scale rtol=1e-12 atol=1e-12
    @test sol.pi ≈ getproperty(original, :trade_share) rtol=1e-12 atol=1e-12
end
