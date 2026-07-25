const PACKAGE_ROOT = normpath(joinpath(@__DIR__, ".."))

include(joinpath(PACKAGE_ROOT, "src", "BaselineModel.jl"))
include(joinpath(PACKAGE_ROOT, "src", "ExactHat.jl"))

using .BaselineModel
using .ExactHat

fund = build_baseline_fundamentals()
base = solve_level_equilibrium(fund)
println(
    "level: iterations=",
    base.iterations,
    ", tolerance=",
    fund.settings.tolerance,
    ", final diff=",
    base.final_diff,
)

experiments = build_counterfactuals(base, fund)
checkpoints = (1, 10, 50, 100, 250, 500, 750, 1000, 1500, 2000, 2500, 3000)

for name in propertynames(experiments)
    result = getproperty(experiments, name).result
    history = result.convergence_history
    println()
    println(
        name,
        ": converged=",
        result.converged,
        ", iterations=",
        result.iterations,
        ", final diff=",
        result.final_diff,
    )
    for iteration in checkpoints
        iteration <= length(history) || continue
        println("  iteration ", iteration, ": ", history[iteration])
    end
end
