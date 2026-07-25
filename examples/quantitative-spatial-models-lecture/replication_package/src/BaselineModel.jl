module BaselineModel

using Random
using Statistics
using StatsBase
using LinearAlgebra

export BaselineSettings,
       legacy_baseline_settings,
       build_baseline_fundamentals,
       solve_level_equilibrium,
       baseline_residuals,
       baseline_trade_moments

Base.@kwdef struct BaselineSettings
    grid_size::Int = 30
    distance_power::Float64 = 0.35
    internal_trade_factor::Float64 = 2.0
    international_border_factor::Float64 = 2.0
    international_distance_normalization::Float64 = 6.3029643017941
    productivity_log_sd::Float64 = 1.00
    alpha::Float64 = 0.75
    sigma::Float64 = 5.0
    kappa::Float64 = 1.50
    fixed_cost::Float64 = 1.0
    housing_stock::Float64 = 100.0
    total_labor::Float64 = 100_000.0
    seed::Int = 42
    maximum_iterations::Int = 10_000
    tolerance::Float64 = 1.0e-12
    damping::Float64 = 0.25
end

"""
    legacy_baseline_settings()

Settings used in the original lecture script. Kept only for numerical parity
testing; the default teaching baseline uses rounded trade-cost parameters and
approximately matches 60 percent own-location, 30 percent domestic-nonlocal,
and 10 percent cross-country expenditure shares.
"""
function legacy_baseline_settings()
    return BaselineSettings(
        internal_trade_factor = 2.0,
        international_border_factor = 2.0,
        international_distance_normalization = 1.0,
        productivity_log_sd = 1.0,
        kappa = Inf,
        tolerance = 1.0e-3,
    )
end

"""
    build_baseline_fundamentals([settings])

Construct the exact baseline geography and fundamentals used by the lecture
example. The trade-cost matrix is indexed `d[n, i]`: cost of delivering from
supplier location `i` to destination location `n`.
"""
function build_baseline_fundamentals(
    settings::BaselineSettings = BaselineSettings(),
)
    N = settings.grid_size
    NN = N * N
    region = reshape(1:NN, N, N)

    col = zeros(Float64, NN)
    row = zeros(Float64, NN)
    for i in 1:N, j in 1:N
        id = region[i, j]
        col[id] = j
        row[id] = i
    end

    dist = zeros(Float64, NN, NN)
    for n in 1:NN, i in 1:NN
        dx = col[n] - col[i]
        dy = row[n] - row[i]
        dist[n, i] = sqrt(dx * dx + dy * dy)
    end

    icebergcost = dist .^ settings.distance_power
    for i in 1:NN
        icebergcost[i, i] = 1.0
    end

    bord = fill(settings.internal_trade_factor, NN, NN)
    for i in 1:NN
        bord[i, i] = 1.0
    end

    half = div(N, 2)
    Iwest_matrix = zeros(Float64, N, N)
    Ieast_matrix = zeros(Float64, N, N)
    Iwest_matrix[:, 1:half] .= 1.0
    Ieast_matrix[:, (half + 1):N] .= 1.0
    Iwest = reshape(Iwest_matrix, NN)
    Ieast = reshape(Ieast_matrix, NN)

    bordc = ones(Float64, NN, NN)
    bordc[Iwest .== 1.0, Ieast .== 1.0] .=
        settings.international_border_factor
    bordc[Ieast .== 1.0, Iwest .== 1.0] .=
        settings.international_border_factor

    cross_border = (
        (Iwest .== 1.0) * transpose(Ieast .== 1.0) .+
        (Ieast .== 1.0) * transpose(Iwest .== 1.0)
    ) .> 0
    icebergcost[cross_border] ./=
        settings.international_distance_normalization ^
        settings.distance_power
    d = icebergcost .* bord .* bordc

    Random.seed!(settings.seed)
    A = exp.(settings.productivity_log_sd .* randn(NN))
    west = Iwest .== 1.0
    east = Ieast .== 1.0
    A[west] ./= geomean(A[west])
    A[east] ./= geomean(A[east])

    B = ones(Float64, NN)
    H = fill(settings.housing_stock, NN)
    LL = settings.total_labor
    LLwest = (sum(Iwest) / (sum(Iwest) + sum(Ieast))) * LL
    LLeast = (sum(Ieast) / (sum(Iwest) + sum(Ieast))) * LL

    return (
        settings = settings,
        N = N,
        NN = NN,
        half = half,
        region = region,
        col = col,
        row = row,
        dist = dist,
        icebergcost = icebergcost,
        bord = bord,
        bordc = bordc,
        international_distance_normalization =
            settings.international_distance_normalization,
        d = d,
        cross_border = cross_border,
        Iwest = Iwest,
        Ieast = Ieast,
        A = A,
        B = B,
        H = H,
        alpha = settings.alpha,
        sigma = settings.sigma,
        kappa = settings.kappa,
        F = settings.fixed_cost,
        LL = LL,
        LLwest = LLwest,
        LLeast = LLeast,
    )
end

"""
    solve_level_equilibrium(fundamentals)

Solve the damped level equilibrium with finite-elasticity location choice
within each country.
Returned `pi[n, i]` is destination `n`'s expenditure share on supplier `i`.
"""
function solve_level_equilibrium(fund)
    (;
        A,
        B,
        H,
        Iwest,
        Ieast,
        alpha,
        sigma,
        kappa,
        LL,
        LLwest,
        LLeast,
        F,
        d,
    ) = fund
    settings = fund.settings
    mu = sigma / (sigma - 1.0)
    nobs = length(A)

    L = fill(LL / nobs, nobs)
    w = ones(Float64, nobs)
    pi = zeros(Float64, nobs, nobs)
    P = ones(Float64, nobs)
    lambda = zeros(Float64, nobs)
    M = zeros(Float64, nobs, nobs)

    iter = 0
    diff = 1.0
    while iter < settings.maximum_iterations && diff > settings.tolerance
        for n in 1:nobs, i in 1:nobs
            M[n, i] = L[i] * (d[n, i] * w[i] / A[i])^(1.0 - sigma)
        end

        S = vec(sum(M; dims=2))
        P .= mu .* ((S ./ (sigma * F)) .^ (1.0 / (1.0 - sigma)))

        if isinf(kappa)
            num_lambda =
                (((w ./ P) .^ alpha) .* (H .^ (1.0 - alpha))) .^
                (1.0 / (1.0 - alpha))
        else
            location_value =
                B .* w .^ alpha .* H .^ (1.0 - alpha) ./
                (P .^ alpha .* L .^ (1.0 - alpha))
            num_lambda = location_value .^ kappa
        end
        west = Iwest .== 1.0
        east = Ieast .== 1.0
        lambda[west] .= num_lambda[west] ./ sum(num_lambda[west])
        lambda[east] .= num_lambda[east] ./ sum(num_lambda[east])

        pi .= M ./ S
        w_new = (transpose(pi) * (w .* L)) ./ L

        L_new = zeros(Float64, nobs)
        L_new[west] .= lambda[west] .* LLwest
        L_new[east] .= lambda[east] .* LLeast

        diff_w = sum(((w_new .- w) ./ (w_new .+ w)) .^ 2)
        diff_L = sum(((L_new .- L) ./ (L_new .+ L)) .^ 2)
        diff = max(diff_w, diff_L)

        w_new ./= mean(w_new)
        w .= settings.damping .* w_new .+ (1.0 - settings.damping) .* w
        L .= settings.damping .* L_new .+ (1.0 - settings.damping) .* L
        iter += 1
    end

    # In the lecture closure, lambda is the within-country population share.
    west = Iwest .== 1.0
    east = Ieast .== 1.0
    lambda[west] .= L[west] ./ sum(L[west])
    lambda[east] .= L[east] ./ sum(L[east])

    wage_scale = geomean(w[west])
    w ./= wage_scale
    P ./= wage_scale
    M .*= wage_scale^(sigma - 1.0)

    return (
        w = w,
        L = L,
        P = P,
        pi = pi,
        lambda = lambda,
        M = copy(M),
        iterations = iter,
        final_diff = diff,
        converged = diff <= settings.tolerance,
    )
end

function baseline_residuals(sol, fund)
    row_error = maximum(abs.(vec(sum(sol.pi; dims=2)) .- 1.0))
    revenue = transpose(sol.pi) * (sol.w .* sol.L)
    income = sol.w .* sol.L
    goods_error = maximum(abs.(revenue .- income) ./ max.(abs.(income), eps()))
    west_error = abs(sum(sol.L[fund.Iwest .== 1.0]) - fund.LLwest)
    east_error = abs(sum(sol.L[fund.Ieast .== 1.0]) - fund.LLeast)
    return (
        trade_share_adding_up = row_error,
        goods_market_relative = goods_error,
        west_population = west_error,
        east_population = east_error,
    )
end

"""
    baseline_trade_moments(solution, fundamentals)

Return expenditure-weighted shares for own-location purchases, purchases from
other locations in the same country, and purchases from the other country.
"""
function baseline_trade_moments(sol, fund)
    expenditure = sol.w .* sol.L
    total_expenditure = sum(expenditure)
    own_location =
        sum(expenditure .* diag(sol.pi)) / total_expenditure
    foreign_by_destination =
        vec(sum(sol.pi .* fund.cross_border; dims=2))
    foreign =
        sum(expenditure .* foreign_by_destination) / total_expenditure
    return (
        own_location = own_location,
        domestic_nonlocal = 1.0 - own_location - foreign,
        foreign = foreign,
    )
end

end
