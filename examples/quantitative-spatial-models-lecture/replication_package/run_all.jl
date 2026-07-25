ENV["GKSwstype"] = "100"

using Serialization

const PACKAGE_ROOT = @__DIR__
const FIGURE_DIR = joinpath(PACKAGE_ROOT, "figures")
const OUTPUT_DIR = joinpath(PACKAGE_ROOT, "output")
const SLIDE_DIR = normpath(joinpath(PACKAGE_ROOT, ".."))

include(joinpath(PACKAGE_ROOT, "src", "BaselineModel.jl"))
include(joinpath(PACKAGE_ROOT, "src", "ExactHat.jl"))
include(joinpath(PACKAGE_ROOT, "src", "Figures.jl"))

using .BaselineModel
using .ExactHat
using .LectureFigures

function main(args=ARGS)
    println("1/4 Constructing baseline fundamentals...")
    fund = build_baseline_fundamentals()

    println("2/4 Solving level equilibrium...")
    base = solve_level_equilibrium(fund)
    base.converged || error("Level equilibrium did not converge.")
    residuals = baseline_residuals(base, fund)

    println("3/4 Solving exact-hat counterfactuals...")
    experiments = build_counterfactuals(base, fund)
    for name in propertynames(experiments)
        result = getproperty(experiments, name).result
        println(
            "    ",
            name,
            ": converged=",
            result.converged,
            ", iterations=",
            result.iterations,
            ", final diff=",
            result.final_diff,
        )
    end
    all((
        experiments.internal.result.converged,
        experiments.integration.result.converged,
        experiments.road.result.converged,
        experiments.development.result.converged,
    )) || error("At least one exact-hat counterfactual did not converge.")

    println("4/4 Writing figures and outputs...")
    paths = save_all_figures(FIGURE_DIR, base, fund, experiments)
    mkpath(OUTPUT_DIR)
    serialize(
        joinpath(OUTPUT_DIR, "baseline.jls"),
        (fundamentals=fund, baseline=base),
    )
    internal_stats = counterfactual_statistics(
        experiments.internal.result,
        base,
        fund,
    )
    integration_stats = counterfactual_statistics(
        experiments.integration.result,
        base,
        fund,
    )
    road_stats = counterfactual_statistics(
        experiments.road.result,
        base,
        fund,
    )
    development_stats = counterfactual_statistics(
        experiments.development.result,
        base,
        fund,
    )
    moments = baseline_trade_moments(base, fund)
    write_replication_summary(
        joinpath(OUTPUT_DIR, "replication_summary.txt"),
        base,
        fund,
        residuals,
        moments,
        experiments,
        internal_stats,
        integration_stats,
        road_stats,
        development_stats,
    )

    if "--sync-slide" in args
        for path in paths
            cp(path, joinpath(SLIDE_DIR, basename(path)); force=true)
        end
        println("Synced figures to: ", SLIDE_DIR)
    end

    println("Replication complete.")
    println("Figures: ", FIGURE_DIR)
    println("Outputs: ", OUTPUT_DIR)
    return nothing
end

main()
