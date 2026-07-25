module ExactHat

using Random
using Statistics
using StatsBase

export CounterfactualSettings,
       solve_exact_hat,
       build_counterfactuals,
       counterfactual_statistics

Base.@kwdef struct CounterfactualSettings
    trade_cost_hat::Float64 = 0.90
    road_seed::Int = 20_260_724
    road_traversal_cost_hat::Float64 = 0.50
    development_seed::Int = 20_260_725
    development_zone_count::Int = 3
    development_zone_sizes::NTuple{3,Int} = (15, 16, 14)
    development_border_width::Int = 5
    development_productivity_hat::Float64 = 1.20
end

function _heap_push!(
    nodes::Vector{Int},
    distances::Vector{Float64},
    node::Int,
    distance::Float64,
)
    push!(nodes, node)
    push!(distances, distance)
    child = length(nodes)
    while child > 1
        parent = child ÷ 2
        distances[parent] <= distance && break
        nodes[child] = nodes[parent]
        distances[child] = distances[parent]
        child = parent
    end
    nodes[child] = node
    distances[child] = distance
    return nothing
end

function _heap_pop!(
    nodes::Vector{Int},
    distances::Vector{Float64},
)
    node = nodes[1]
    distance = distances[1]
    last_node = pop!(nodes)
    last_distance = pop!(distances)
    if !isempty(nodes)
        parent = 1
        while true
            left = 2 * parent
            left > length(nodes) && break
            right = left + 1
            child =
                right <= length(nodes) &&
                distances[right] < distances[left] ? right : left
            distances[child] >= last_distance && break
            nodes[parent] = nodes[child]
            distances[parent] = distances[child]
            parent = child
        end
        nodes[parent] = last_node
        distances[parent] = last_distance
    end
    return node, distance
end

"""
    _effective_distance_matrix(cell_cost)

Compute QSE-style lowest-cost-route distances on a rectangular grid. Moving
between neighboring cells costs their average traversal cost, multiplied by
one for horizontal/vertical moves and by `sqrt(2)` for diagonal moves.
"""
function _effective_distance_matrix(cell_cost::AbstractMatrix)
    nrows, ncols = size(cell_cost)
    nobs = length(cell_cost)
    linear = LinearIndices(cell_cost)
    row_of = [Tuple(CartesianIndices(cell_cost)[i])[1] for i in 1:nobs]
    col_of = [Tuple(CartesianIndices(cell_cost)[i])[2] for i in 1:nobs]
    output = Matrix{Float64}(undef, nobs, nobs)
    moves = (
        (-1, -1, sqrt(2.0)),
        (-1, 0, 1.0),
        (-1, 1, sqrt(2.0)),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (1, -1, sqrt(2.0)),
        (1, 0, 1.0),
        (1, 1, sqrt(2.0)),
    )

    for source in 1:nobs
        best = fill(Inf, nobs)
        best[source] = 0.0
        heap_nodes = Int[]
        heap_distances = Float64[]
        _heap_push!(heap_nodes, heap_distances, source, 0.0)

        while !isempty(heap_nodes)
            current, current_distance =
                _heap_pop!(heap_nodes, heap_distances)
            current_distance > best[current] && continue
            row = row_of[current]
            col = col_of[current]
            for (dr, dc, step_length) in moves
                next_row = row + dr
                next_col = col + dc
                if 1 <= next_row <= nrows && 1 <= next_col <= ncols
                    neighbor = linear[next_row, next_col]
                    edge_cost =
                        step_length *
                        (cell_cost[current] + cell_cost[neighbor]) / 2.0
                    candidate = current_distance + edge_cost
                    if candidate < best[neighbor]
                        best[neighbor] = candidate
                        _heap_push!(
                            heap_nodes,
                            heap_distances,
                            neighbor,
                            candidate,
                        )
                    end
                end
            end
        end
        output[:, source] .= best
        output[source, source] = 1.0
    end
    return output
end

function _is_identity_shock(shock)
    for name in (
        :d_hat,
        :A_hat,
        :B_hat,
        :T_hat,
        :H_hat,
        :F_hat,
        :L_total_hat,
    )
        if hasproperty(shock, name) &&
           !all(getproperty(shock, name) .== 1.0)
            return false
        end
    end
    return true
end

function _hat_vector(shock, name, nobs)
    hasproperty(shock, name) || return ones(Float64, nobs)
    value = getproperty(shock, name)
    return value isa Number ? fill(Float64(value), nobs) : Float64.(value)
end

"""
    solve_exact_hat(baseline, fundamentals, shock; mobile=true)

Solve the exact-hat system using baseline expenditure shares and expenditure
levels. `d_hat[n, i]` changes delivery cost from supplier `i` to destination `n`.
"""
function solve_exact_hat(
    base,
    fund,
    shock;
    mobile::Bool=true,
    maximum_iterations::Int=3_000,
    tolerance::Float64=1.0e-8,
    damping::Float64=0.30,
)
    nobs = fund.NN
    if _is_identity_shock(shock)
        return (
            w_hat = ones(Float64, nobs),
            L_hat = ones(Float64, nobs),
            P_hat = ones(Float64, nobs),
            pi_hat = ones(Float64, nobs, nobs),
            lambda_hat = ones(Float64, nobs),
            B_hat = ones(Float64, nobs),
            T_hat = ones(Float64, nobs),
            H_hat = ones(Float64, nobs),
            iterations = 0,
            final_diff = 0.0,
            converged = true,
            convergence_history = [0.0],
        )
    end

    (; alpha, sigma, kappa, Iwest, Ieast) = fund
    west = Iwest .== 1.0
    east = Ieast .== 1.0
    lambda0 = base.lambda

    w_hat = ones(Float64, nobs)
    L_hat = ones(Float64, nobs)
    P_hat = ones(Float64, nobs)
    pi_hat = ones(Float64, nobs, nobs)
    lambda_hat = ones(Float64, nobs)
    base_income = base.w .* base.L
    H_hat = _hat_vector(shock, :H_hat, nobs)
    B_hat = _hat_vector(shock, :B_hat, nobs)
    T_hat = _hat_vector(shock, :T_hat, nobs)
    F_hat = _hat_vector(shock, :F_hat, nobs)
    L_total_hat = _hat_vector(shock, :L_total_hat, nobs)

    final_diff = Inf
    iterations = maximum_iterations
    convergence_history = Float64[]

    for iter in 1:maximum_iterations
        cost_term =
            (shock.d_hat .* transpose(w_hat ./ shock.A_hat)) .^
            (1.0 - sigma)
        P_power =
            vec(sum(base.pi .* cost_term .* transpose(L_hat); dims=2)) ./
            F_hat
        P_hat .= P_power .^ (1.0 / (1.0 - sigma))
        pi_hat .=
            (cost_term .* transpose(L_hat)) ./
            (P_power .* F_hat)

        L_new = ones(Float64, nobs)
        if mobile
            if isinf(kappa)
                exponent = alpha / (1.0 - alpha)
                attractiveness =
                    w_hat .^ exponent .* H_hat .*
                    P_hat .^ (-exponent)
            else
                value_hat =
                    B_hat .* w_hat .^ alpha .* H_hat .^ (1.0 - alpha) ./
                    (
                        P_hat .^ alpha .*
                        L_hat .^ (1.0 - alpha)
                    )
                attractiveness = T_hat .* value_hat .^ kappa
            end
            denom_w = sum(lambda0[west] .* attractiveness[west])
            denom_e = sum(lambda0[east] .* attractiveness[east])
            lambda_hat[west] .= attractiveness[west] ./ denom_w
            lambda_hat[east] .= attractiveness[east] ./ denom_e
            L_new .= L_total_hat .* lambda_hat
        end

        revenue =
            transpose(pi_hat .* base.pi) *
            (w_hat .* L_hat .* base_income)
        w_new = revenue ./ (L_hat .* base_income)
        w_new ./= mean(w_new)

        final_diff = max(
            maximum(abs.(log.(w_new ./ w_hat))),
            maximum(abs.(log.(L_new ./ L_hat))),
        )
        push!(convergence_history, final_diff)
        w_hat .= damping .* w_new .+ (1.0 - damping) .* w_hat
        L_hat .= damping .* L_new .+ (1.0 - damping) .* L_hat

        if final_diff < tolerance
            iterations = iter
            break
        end
    end

    wage_scale = geomean(w_hat[west])
    w_hat ./= wage_scale
    P_hat ./= wage_scale

    return (
        w_hat = w_hat,
        L_hat = L_hat,
        P_hat = P_hat,
        pi_hat = pi_hat,
        lambda_hat = lambda_hat,
        B_hat = B_hat,
        T_hat = T_hat,
        H_hat = H_hat,
        iterations = iterations,
        final_diff = final_diff,
        converged = final_diff < tolerance,
        convergence_history = convergence_history,
    )
end

function _build_road_path(fund, settings::CounterfactualSettings)
    rng = MersenneTwister(settings.road_seed)
    path = Int[]

    function append_location!(row, col)
        location = fund.region[row, col]
        if isempty(path) || path[end] != location
            push!(path, location)
        end
    end

    row = rand(rng, 4:(fund.N - 3))
    append_location!(row, 1)
    for col in 1:(fund.N - 1)
        next_row = clamp(row + rand(rng, (-1, 0, 0, 1)), 2, fund.N - 1)
        append_location!(row, col + 1)
        if next_row != row
            append_location!(next_row, col + 1)
        end
        row = next_row
    end
    return path
end

function _build_development_zone_labels(
    fund,
    settings::CounterfactualSettings,
)
    settings.development_zone_count == 3 ||
        error("The teaching example is designed for three development zones.")
    rng = MersenneTwister(settings.development_seed)
    labels = zeros(Int, fund.NN)
    first_border_col =
        fund.half - settings.development_border_width + 1
    allowed_cols = first_border_col:fund.half
    third = fld(fund.N, 3)
    row_bands = (
        1:max(1, third - 1),
        (third + 1):max(third + 1, 2 * third - 1),
        (2 * third + 1):fund.N,
    )

    for zone in 1:settings.development_zone_count
        rows = row_bands[zone]
        target_size = settings.development_zone_sizes[zone]
        center = fund.region[rand(rng, rows), rand(rng, allowed_cols)]
        labels[center] = zone
        members = [center]

        while length(members) < target_size
            frontier = Int[]
            for location in members
                row = Int(fund.row[location])
                col = Int(fund.col[location])
                for (dr, dc) in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    next_row = row + dr
                    next_col = col + dc
                    if next_row in rows && next_col in allowed_cols
                        candidate = fund.region[next_row, next_col]
                        if labels[candidate] == 0
                            push!(frontier, candidate)
                        end
                    end
                end
            end
            isempty(frontier) &&
                error("Unable to grow development zone $(zone).")
            candidate = rand(rng, unique(frontier))
            labels[candidate] = zone
            push!(members, candidate)
        end
    end
    return labels
end

function build_counterfactuals(
    base,
    fund;
    settings::CounterfactualSettings=CounterfactualSettings(),
)
    NN = fund.NN

    internal_d_hat = ifelse.(
        fund.cross_border,
        1.0,
        settings.trade_cost_hat,
    )
    for location in 1:NN
        internal_d_hat[location, location] = 1.0
    end
    internal_shock = (
        name = :internal_trade_liberalization,
        d_hat = internal_d_hat,
        A_hat = ones(Float64, NN),
    )
    internal_result =
        solve_exact_hat(base, fund, internal_shock; mobile=true)

    integration_shock = (
        name = :bilateral_border_liberalization,
        d_hat = ifelse.(
            fund.cross_border,
            settings.trade_cost_hat,
            1.0,
        ),
        A_hat = ones(Float64, NN),
    )
    integration_result =
        solve_exact_hat(base, fund, integration_shock; mobile=true)

    road_path = _build_road_path(fund, settings)
    road_mask = falses(NN)
    road_mask[road_path] .= true
    route_cost_hat = ones(Float64, NN)
    route_cost_hat[road_mask] .= settings.road_traversal_cost_hat
    baseline_route_distance =
        _effective_distance_matrix(ones(Float64, fund.N, fund.N))
    counterfactual_route_distance =
        _effective_distance_matrix(
            reshape(route_cost_hat, fund.N, fund.N),
        )
    road_d_hat =
        (
            counterfactual_route_distance ./
            baseline_route_distance
        ) .^ fund.settings.distance_power
    for location in 1:NN
        road_d_hat[location, location] = 1.0
    end
    road_shock = (
        name = :road_construction,
        seed = settings.road_seed,
        path = road_path,
        location_mask = road_mask,
        route_cost_hat = route_cost_hat,
        baseline_route_distance = baseline_route_distance,
        counterfactual_route_distance = counterfactual_route_distance,
        d_hat = road_d_hat,
        A_hat = ones(Float64, NN),
    )
    road_result = solve_exact_hat(base, fund, road_shock)

    zone_labels = _build_development_zone_labels(fund, settings)
    zone = zone_labels .> 0
    zone_A_hat = ones(Float64, NN)
    zone_A_hat[zone] .= settings.development_productivity_hat
    development_shock = (
        name = :development_zones,
        seed = settings.development_seed,
        zone_labels = zone_labels,
        location_mask = zone,
        d_hat = ones(Float64, NN, NN),
        A_hat = zone_A_hat,
    )
    development_result = solve_exact_hat(base, fund, development_shock)

    return (
        internal = (
            shock = internal_shock,
            result = internal_result,
        ),
        integration = (
            shock = integration_shock,
            result = integration_result,
        ),
        road = (
            shock = road_shock,
            result = road_result,
        ),
        development = (
            shock = development_shock,
            result = development_result,
        ),
    )
end

function _weighted_mean(x, weights)
    return sum(x .* weights) / sum(weights)
end

function counterfactual_statistics(result, base, fund)
    pi_new = base.pi .* result.pi_hat
    expenditure_new =
        (base.w .* base.L) .* result.w_hat .* result.L_hat
    foreign_share_by_destination =
        vec(sum(pi_new .* fund.cross_border; dims=2))
    aggregate_foreign_share =
        sum(expenditure_new .* foreign_share_by_destination) /
        sum(expenditure_new)

    value_hat =
        result.B_hat .* result.w_hat .^ fund.alpha .*
        result.H_hat .^ (1.0 - fund.alpha) ./
        (
            result.P_hat .^ fund.alpha .*
            result.L_hat .^ (1.0 - fund.alpha)
        )

    function country_welfare(mask)
        if isinf(fund.kappa)
            return maximum(value_hat[mask])
        end
        return (
            sum(
                base.lambda[mask] .* result.T_hat[mask] .*
                value_hat[mask] .^ fund.kappa,
            )
        ) ^ (1.0 / fund.kappa)
    end

    country(mask) = (
        wage_change =
            _weighted_mean(100.0 .* log.(result.w_hat[mask]), base.L[mask]),
        population_reallocation =
            _weighted_mean(
                100.0 .* abs.(result.L_hat[mask] .- 1.0),
                base.L[mask],
            ),
        price_change =
            _weighted_mean(100.0 .* log.(result.P_hat[mask]), base.L[mask]),
        welfare_change =
            100.0 * log(country_welfare(mask)),
    )

    return (
        foreign_expenditure_share = aggregate_foreign_share,
        west = country(fund.Iwest .== 1.0),
        east = country(fund.Ieast .== 1.0),
    )
end

end
