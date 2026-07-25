include(joinpath(@__DIR__, "src", "BaselineModel.jl"))

using .BaselineModel

const CANDIDATES = [
    (
        distance_power = distance_power,
        internal = 2.0,
        border = 1.05,
        sigma = 5.0,
        seed = seed,
    )
    for distance_power in (0.34, 0.35, 0.36)
    for seed in (8, 14, 42, 44, 54, 67)
]

function calibration_loss(moments)
    target = (own_location = 0.60, domestic_nonlocal = 0.30, foreign = 0.10)
    return (
        (moments.own_location - target.own_location)^2 +
        (moments.domestic_nonlocal - target.domestic_nonlocal)^2 +
        (moments.foreign - target.foreign)^2
    )
end

results = NamedTuple[]
for candidate in CANDIDATES
    settings = BaselineSettings(
        distance_power = candidate.distance_power,
        internal_trade_factor = candidate.internal,
        international_border_factor = candidate.border,
        sigma = candidate.sigma,
        seed = candidate.seed,
    )
    fundamentals = build_baseline_fundamentals(settings)
    solution = solve_level_equilibrium(fundamentals)
    solution.converged || error("Candidate did not converge: $candidate")
    moments = baseline_trade_moments(solution, fundamentals)
    push!(
        results,
        (
            candidate...,
            own_location = moments.own_location,
            domestic_nonlocal = moments.domestic_nonlocal,
            foreign = moments.foreign,
            loss = calibration_loss(moments),
        ),
    )
end

sort!(results; by = result -> result.loss)
for result in results
    println(result)
end
