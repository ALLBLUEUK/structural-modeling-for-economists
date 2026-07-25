using Test
using Statistics
using LinearAlgebra
using StatsBase

const PACKAGE_ROOT = normpath(joinpath(@__DIR__, ".."))

include(joinpath(PACKAGE_ROOT, "src", "BaselineModel.jl"))
include(joinpath(PACKAGE_ROOT, "src", "ExactHat.jl"))
include(joinpath(PACKAGE_ROOT, "src", "Figures.jl"))

using .BaselineModel
using .ExactHat
using .LectureFigures

@testset "Baseline fundamentals" begin
    fund = build_baseline_fundamentals()

    @test fund.N == 30
    @test fund.NN == 900
    @test fund.settings.productivity_log_sd == 1.00
    @test std(log.(fund.A)) ≈ 1.00 atol=0.05
    @test fund.settings.distance_power == 0.35
    @test fund.settings.internal_trade_factor == 2.0
    @test fund.settings.international_border_factor == 2.0
    @test fund.settings.international_distance_normalization ≈
          6.3029643017941
    @test fund.settings.kappa == 1.50
    @test fund.kappa == 1.50
    @test size(fund.d) == (900, 900)
    @test all(diag(fund.d) .== 1.0)
    @test fund.d[1, 2] ≈ fund.settings.internal_trade_factor

    first_east = fund.N * div(fund.N, 2) + 1
    expected_cross_cost =
        fund.settings.internal_trade_factor *
        fund.settings.international_border_factor *
        (
            fund.dist[1, first_east] /
            fund.settings.international_distance_normalization
        )^fund.settings.distance_power
    @test fund.d[1, first_east] ≈ expected_cross_cost

    @test geomean(fund.A[fund.Iwest .== 1.0]) ≈ 1.0 atol=1e-12
    @test geomean(fund.A[fund.Ieast .== 1.0]) ≈ 1.0 atol=1e-12
    @test all(fund.B .== 1.0)
    @test all(fund.H .== 100.0)
end

@testset "Level equilibrium identities" begin
    fund = build_baseline_fundamentals()
    sol = solve_level_equilibrium(fund)
    res = baseline_residuals(sol, fund)

    @test sol.converged
    @test size(sol.pi) == (fund.NN, fund.NN)
    @test maximum(abs.(vec(sum(sol.pi; dims=2)) .- 1.0)) < 1e-12
    @test sum(sol.L[fund.Iwest .== 1.0]) ≈ fund.LLwest rtol=1e-10
    @test sum(sol.L[fund.Ieast .== 1.0]) ≈ fund.LLeast rtol=1e-10
    @test maximum(abs.(sol.lambda[fund.Iwest .== 1.0] .-
                       sol.L[fund.Iwest .== 1.0] ./ fund.LLwest)) < 1e-12
    @test maximum(abs.(sol.lambda[fund.Ieast .== 1.0] .-
                       sol.L[fund.Ieast .== 1.0] ./ fund.LLeast)) < 1e-12

    location_value =
        fund.B .* sol.w .^ fund.alpha .* fund.H .^ (1.0 - fund.alpha) ./
        (sol.P .^ fund.alpha .* sol.L .^ (1.0 - fund.alpha))
    choice_weight = location_value .^ fund.kappa
    for country in (fund.Iwest .== 1.0, fund.Ieast .== 1.0)
        predicted_share =
            choice_weight[country] ./ sum(choice_weight[country])
        @test maximum(
            abs.(sol.lambda[country] .- predicted_share),
        ) < 1e-8
    end
    @test res.trade_share_adding_up < 1e-12
    @test res.goods_market_relative < 0.02
    @test geomean(sol.w[fund.Iwest .== 1.0]) ≈ 1.0 atol=1e-10

    moments = baseline_trade_moments(sol, fund)
    @test moments.own_location ≈ 0.60 atol=0.01
    @test moments.domestic_nonlocal ≈ 0.30 atol=0.01
    @test moments.foreign ≈ 0.10 atol=0.01
    @test maximum(sol.L ./ sum(sol.L)) < 0.02
    wage_ratio = maximum(sol.w) / minimum(sol.w)
    @test 50.0 < wage_ratio < 200.0
end

@testset "Exact-hat identities and shocks" begin
    fund = build_baseline_fundamentals()
    base = solve_level_equilibrium(fund)
    counterfactual_settings = CounterfactualSettings()

    @test counterfactual_settings.trade_cost_hat == 0.90
    @test counterfactual_settings.road_seed == 20_260_724
    @test counterfactual_settings.road_traversal_cost_hat == 0.50
    @test counterfactual_settings.development_seed == 20_260_725
    @test counterfactual_settings.development_productivity_hat == 1.20

    no_shock = (
        name = :no_shock,
        d_hat = ones(fund.NN, fund.NN),
        A_hat = ones(fund.NN),
    )
    identity = solve_exact_hat(base, fund, no_shock)
    @test identity.w_hat == ones(fund.NN)
    @test identity.L_hat == ones(fund.NN)
    @test identity.P_hat == ones(fund.NN)
    @test identity.pi_hat == ones(fund.NN, fund.NN)
    @test identity.convergence_history == [0.0]

    experiments =
        build_counterfactuals(base, fund; settings=counterfactual_settings)
    @test all(
        getproperty(experiments, name).result.converged
        for name in propertynames(experiments)
    )
    @test all(
        experiments.integration.shock.d_hat[fund.cross_border] .==
        counterfactual_settings.trade_cost_hat
    )
    @test all(
        experiments.integration.shock.d_hat[.!fund.cross_border] .== 1.0
    )
    @test experiments.integration.shock.d_hat ≈
          transpose(experiments.integration.shock.d_hat)
    @test all(experiments.integration.shock.A_hat .== 1.0)

    domestic_nonlocal =
        .!fund.cross_border .&
        .!Matrix{Bool}(I, fund.NN, fund.NN)
    @test all(
        experiments.internal.shock.d_hat[domestic_nonlocal] .==
        counterfactual_settings.trade_cost_hat
    )
    @test all(
        experiments.internal.shock.d_hat[fund.cross_border] .== 1.0
    )
    @test all(diag(experiments.internal.shock.d_hat) .== 1.0)
    @test experiments.internal.shock.d_hat ≈
          transpose(experiments.internal.shock.d_hat)
    @test all(experiments.internal.shock.A_hat .== 1.0)

    road_path = experiments.road.shock.path
    road_mask = experiments.road.shock.location_mask
    @test experiments.road.shock.seed == counterfactual_settings.road_seed
    @test road_path ==
          ExactHat._build_road_path(fund, counterfactual_settings)
    @test length(road_path) == length(unique(road_path))
    @test all(road_mask[road_path])
    @test minimum(fund.col[road_path]) == 1
    @test maximum(fund.col[road_path]) == fund.N
    @test any(fund.Iwest[road_path] .== 1.0)
    @test any(fund.Ieast[road_path] .== 1.0)
    @test all(
        abs(fund.row[road_path[index + 1]] - fund.row[road_path[index]]) +
        abs(fund.col[road_path[index + 1]] - fund.col[road_path[index]]) == 1
        for index in 1:(length(road_path) - 1)
    )
    @test all(
        experiments.road.shock.route_cost_hat[road_mask] .==
        counterfactual_settings.road_traversal_cost_hat
    )
    @test all(experiments.road.shock.route_cost_hat[.!road_mask] .== 1.0)
    @test all(diag(experiments.road.shock.d_hat) .== 1.0)
    @test experiments.road.shock.d_hat ≈
          transpose(experiments.road.shock.d_hat)
    @test all(experiments.road.shock.d_hat .<= 1.0)
    @test minimum(experiments.road.shock.d_hat) > 0.50
    @test count(x -> x < 1.0, experiments.road.shock.d_hat) >
          0.10 * fund.NN * (fund.NN - 1)
    @test length(unique(round.(
        experiments.road.shock.d_hat;
        digits=5,
    ))) > 20
    @test any(
        experiments.road.shock.d_hat[
            (fund.Iwest .== 1.0),
            (fund.Ieast .== 1.0),
        ] .< 1.0
    )
    @test all(experiments.road.shock.A_hat .== 1.0)

    uniform_route_distance =
        ExactHat._effective_distance_matrix(ones(fund.N, fund.N))
    road_weights = reshape(
        experiments.road.shock.route_cost_hat,
        fund.N,
        fund.N,
    )
    road_route_distance =
        ExactHat._effective_distance_matrix(road_weights)
    expected_road_hat =
        (road_route_distance ./ uniform_route_distance) .^
        fund.settings.distance_power
    expected_road_hat[diagind(expected_road_hat)] .= 1.0
    @test experiments.road.shock.d_hat ≈ expected_road_hat

    zone_labels = experiments.development.shock.zone_labels
    @test experiments.development.shock.seed ==
          counterfactual_settings.development_seed
    @test zone_labels ==
          ExactHat._build_development_zone_labels(
        fund,
        counterfactual_settings,
    )
    @test sort(unique(zone_labels[zone_labels .> 0])) == [1, 2, 3]
    @test all(
        12 <= count(==(zone), zone_labels) <= 20
        for zone in 1:3
    )
    @test any((fund.Iwest .== 1.0)[zone_labels .> 0])
    @test all((fund.Iwest .== 1.0)[zone_labels .> 0])
    @test !any((fund.Ieast .== 1.0)[zone_labels .> 0])
    @test all(
        fund.col[zone_labels .> 0] .>=
        fund.half - counterfactual_settings.development_border_width + 1
    )
    @test all(
        fund.col[zone_labels .> 0] .<=
        fund.half
    )
    @test all(
        experiments.development.shock.A_hat[zone_labels .> 0] .==
        counterfactual_settings.development_productivity_hat
    )
    @test all(
        experiments.development.shock.A_hat[zone_labels .== 0] .== 1.0
    )
    @test all(experiments.development.shock.d_hat .== 1.0)

    pi_new = base.pi .* experiments.integration.result.pi_hat
    @test maximum(abs.(vec(sum(pi_new; dims=2)) .- 1.0)) < 1e-10
    @test all(
        last(getproperty(experiments, name).result.convergence_history) ==
        getproperty(experiments, name).result.final_diff
        for name in propertynames(experiments)
    )
    @test all(
        isapprox(
            geomean(
                getproperty(experiments, name).result.w_hat[
                    fund.Iwest .== 1.0
                ],
            ),
            1.0;
            atol=1e-10,
        )
        for name in propertynames(experiments)
    )

    for name in propertynames(experiments)
        result = getproperty(experiments, name).result
        location_hat =
            (
                result.w_hat .^ fund.alpha ./
                (
                    result.P_hat .^ fund.alpha .*
                    result.L_hat .^ (1.0 - fund.alpha)
                )
            ) .^ fund.kappa
        for country in (fund.Iwest .== 1.0, fund.Ieast .== 1.0)
            denominator = sum(
                base.lambda[country] .*
                location_hat[country],
            )
            predicted_population_hat =
                location_hat[country] ./ denominator
            @test maximum(
                abs.(
                    result.L_hat[country] .-
                    predicted_population_hat
                ),
            ) < 1e-7
        end

        stats = counterfactual_statistics(result, base, fund)
        value_hat =
            result.w_hat .^ fund.alpha ./
            (
                result.P_hat .^ fund.alpha .*
                result.L_hat .^ (1.0 - fund.alpha)
            )
        for (label, country) in (
            (:west, fund.Iwest .== 1.0),
            (:east, fund.Ieast .== 1.0),
        )
            expected_welfare_hat =
                sum(
                    base.lambda[country] .*
                    value_hat[country] .^ fund.kappa,
                ) ^ (1.0 / fund.kappa)
            @test getproperty(stats, label).welfare_change ≈
                  100.0 * log(expected_welfare_hat) atol=1e-10
        end
    end

end

@testset "Slide narrative order" begin
    slide_source = read(
        normpath(joinpath(PACKAGE_ROOT, "..", "quantitative_spatial_models.tex")),
        String,
    )
    system_position = findfirst("label=mainHatSystem", slide_source)
    derivation_position = findfirst("label=deriveHatPrice", slide_source)
    @test system_position !== nothing
    @test derivation_position !== nothing
    @test first(system_position) < first(derivation_position)

    parameter_position = findfirst(
        raw"\boldsymbol\theta=(\alpha,\sigma,\kappa)",
        slide_source,
    )
    model_page_position = findfirst(
        "Why Does Exact-Hat Algebra Help?",
        slide_source,
    )
    estimation_objective_position = findfirst(
        raw"\widehat\Omega(\boldsymbol\Theta)",
        slide_source,
    )
    methods_page_position = findfirst(
        "Structural Estimation: A Common Framework",
        slide_source,
    )
    inversion_example_position = findfirst(
        "Model Inversion: Recovering the Expenditure Share",
        slide_source,
    )
    @test parameter_position !== nothing
    @test model_page_position !== nothing
    @test estimation_objective_position !== nothing
    @test methods_page_position !== nothing
    @test inversion_example_position !== nothing
    @test first(model_page_position) < first(parameter_position)
    @test first(parameter_position) < first(methods_page_position)
    @test first(methods_page_position) <
          first(estimation_objective_position)
    @test first(estimation_objective_position) <
          first(inversion_example_position)
    @test occursin(
        raw"\alpha"
        * "\n"
        * raw"      =\frac{P_nC_n}{P_nC_n+r_nh_n}",
        slide_source,
    )

    @test occursin(
        raw"\underbrace{\alpha,\sigma,\kappa,F,\{\bar L_c\}_c}",
        slide_source,
    )
    @test occursin(raw"\kappa=1.5", slide_source)
    @test occursin("Internal Trade Liberalization: Shock", slide_source)
    @test occursin("Internal Trade: Results", slide_source)
    @test occursin("Bilateral Border Liberalization: Shock", slide_source)
    @test occursin("External Trade: Results", slide_source)
    @test occursin(
        raw"\widehat d_{ni}=0.9",
        slide_source,
    )
    @test !occursin(raw"T_n", slide_source)
    @test !occursin(raw"T_i", slide_source)
    @test !occursin(raw"T_k", slide_source)
    @test !occursin(raw"\widehat{\mathbf T}", slide_source)
    @test !occursin(raw"\wh T", slide_source)
    @test !occursin("location weight", lowercase(slide_source))
    @test occursin("lowest-cost route", slide_source)
    @test occursin("inside West near the border", slide_source)
    @test count("Source:", slide_source) == 1
end

@testset "Declared figure outputs" begin
    @test FIGURE_FILENAMES == [
        "worked_example_baseline.png",
        "worked_example_fundamentals.png",
        "worked_example_trade_costs.png",
        "worked_example_trade_matrix.png",
        "worked_example_shock_internal.png",
        "worked_example_results_internal.png",
        "worked_example_shock_integration.png",
        "worked_example_results_integration.png",
        "worked_example_shock_road.png",
        "worked_example_results_road.png",
        "worked_example_shock_development.png",
        "worked_example_results_development.png",
    ]
end

@testset "Replication summary coverage" begin
    fund = build_baseline_fundamentals()
    base = solve_level_equilibrium(fund)
    residuals = baseline_residuals(base, fund)
    moments = baseline_trade_moments(base, fund)
    experiments = build_counterfactuals(base, fund)
    internal_stats =
        counterfactual_statistics(experiments.internal.result, base, fund)
    integration_stats =
        counterfactual_statistics(experiments.integration.result, base, fund)
    road_stats =
        counterfactual_statistics(experiments.road.result, base, fund)
    development_stats =
        counterfactual_statistics(experiments.development.result, base, fund)

    mktemp() do path, io
        close(io)
        write_replication_summary(
            path,
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
        summary = read(path, String)
        @test occursin("baseline own-location expenditure share", summary)
        @test occursin("baseline domestic-nonlocal expenditure share", summary)
        @test occursin("baseline foreign expenditure share", summary)
        @test occursin("Road construction", summary)
        @test occursin("Development zones", summary)
    end
end

@testset "Counterfactual color scales" begin
    fund = build_baseline_fundamentals()

    hat_palette = LectureFigures._hat_palette([0.8, 1.0])
    hat_lower, hat_upper = hat_palette.clims
    unchanged_coordinate =
        (1.0 - hat_lower) / (hat_upper - hat_lower)
    unchanged_color =
        get(hat_palette.color, unchanged_coordinate)
    @test maximum((
        unchanged_color.r,
        unchanged_color.g,
        unchanged_color.b,
    )) < 0.95

    outlier_changes = vcat(
        collect(range(-2.0, 2.0; length=850)),
        fill(25.0, 50),
    )
    truncated_limits =
        LectureFigures._truncated_change_clims(outlier_changes)
    @test truncated_limits[1] <= 0.0 <= truncated_limits[2]
    @test truncated_limits[1] > minimum(outlier_changes)
    @test truncated_limits[2] < maximum(outlier_changes)

    change_plot =
        LectureFigures._change_map(outlier_changes, fund, "test")
    @test change_plot.subplots[1][:clims] == truncated_limits
    @test vec(change_plot.series_list[1][:z].surf) ≈ outlier_changes

    tick_values, tick_labels =
        LectureFigures._truncated_colorbar_ticks(
            outlier_changes,
            truncated_limits,
        )
    @test first(tick_values) == first(truncated_limits)
    @test last(tick_values) == last(truncated_limits)
    @test startswith(first(tick_labels), "≤")
    @test startswith(last(tick_labels), "≥")
    @test length(tick_values) == length(tick_labels)

    crowded_limits = (-1.96, 4.99)
    crowded_values = [-3.0, -1.0, -0.2, 0.0, 1.0, 6.0]
    crowded_ticks, _ =
        LectureFigures._truncated_colorbar_ticks(
            crowded_values,
            crowded_limits,
        )
    crowded_span = crowded_limits[2] - crowded_limits[1]
    @test count(
        tick -> abs(tick) < 0.08 * crowded_span,
        crowded_ticks,
    ) == 1

    near_zero_endpoint_limits = (-2.0, 0.089)
    near_zero_endpoint_ticks, _ =
        LectureFigures._truncated_colorbar_ticks(
            [-2.2, -1.0, -0.2, 0.0, 0.10],
            near_zero_endpoint_limits,
        )
    @test 0.0 ∉ near_zero_endpoint_ticks

    gradient =
        change_plot.series_list[1].plotattributes[:seriescolor]
    lower, upper = truncated_limits
    coordinate(value) = (value - lower) / (upper - lower)
    neutral_color = get(gradient, coordinate(0.0))
    color_distance(a, b) = sqrt(
        (a.r - b.r)^2 + (a.g - b.g)^2 + (a.b - b.b)^2
    )

    @test maximum((
        neutral_color.r,
        neutral_color.g,
        neutral_color.b,
    )) < 0.95

    dense_coordinates = range(0.0, 1.0; length=501)
    dense_colors = get.(Ref(gradient), dense_coordinates)
    adjacent_distances = [
        color_distance(dense_colors[index], dense_colors[index + 1])
        for index in 1:(length(dense_colors) - 1)
    ]
    @test maximum(adjacent_distances) < 0.08
    endpoint_colors = (get(gradient, 0.0), get(gradient, 1.0))
    @test all(
        (color.r + color.g + color.b) / 3 > 0.40
        for color in endpoint_colors
    )

    shock_plot = LectureFigures._hat_location_map(
        fill(1.0, fund.NN),
        fund,
        "test",
    )
    for plot_object in (change_plot, shock_plot)
        subplot = plot_object.subplots[1]
        @test subplot[:aspect_ratio] == :none
        @test subplot[:xaxis][:tickfontsize] >= 20
        @test subplot[:yaxis][:tickfontsize] >= 20
        @test subplot[:xaxis][:guidefontsize] >= 20
        @test subplot[:yaxis][:guidefontsize] >= 20
        @test subplot[:colorbar_tickfontsize] >= 18
        @test subplot[:titlefontsize] >= 22
        @test subplot[:top_margin].value >= 4
        @test subplot[:xaxis][:ticks] ==
              ([8, 23], ["West", "East"])
        @test isempty(subplot[:xaxis][:guide])
        @test subplot[:yaxis][:guide] == "Region within country"
    end
    @test shock_plot.subplots[1][:right_margin].value >= 6
    @test any(
        series[:seriestype] == :straightline &&
        all(series[:x] .== fund.half + 0.5)
        for series in shock_plot.series_list
    )

    bilateral_shock_plot = LectureFigures._hat_matrix_map(
        ones(fund.NN, fund.NN),
        fund,
        "bilateral test",
    )
    country_boundary = fund.NN ÷ 2 + 0.5
    @test any(
        series[:seriestype] == :straightline &&
        all(series[:x] .== country_boundary)
        for series in bilateral_shock_plot.series_list
    )
    @test any(
        series[:seriestype] == :straightline &&
        all(series[:y] .== country_boundary)
        for series in bilateral_shock_plot.series_list
    )

    figure_source = read(
        joinpath(PACKAGE_ROOT, "src", "Figures.jl"),
        String,
    )
    @test occursin(
        "land_rent_hat = result.w_hat .* result.L_hat ./ result.H_hat",
        figure_source,
    )
    @test occursin(
        "real_wage_hat = result.w_hat ./",
        figure_source,
    )
    @test occursin(
        "result.P_hat .^ fund.alpha .*",
        figure_source,
    )
    @test occursin(
        "land_rent_hat .^ (1.0 - fund.alpha)",
        figure_source,
    )
    @test occursin(
        "real_wage_change = 100.0 .* (real_wage_hat .- 1.0)",
        figure_source,
    )
    @test occursin(
        "map_and_bar(real_wage_change, \"Real-wage change (%)\")",
        figure_source,
    )
    @test occursin(
        "population_change = 100.0 .* (result.L_hat .- 1.0)",
        figure_source,
    )
    @test occursin(
        "price_change = 100.0 .* (result.P_hat .- 1.0)",
        figure_source,
    )
    @test occursin(
        "land_rent_change = 100.0 .* (land_rent_hat .- 1.0)",
        figure_source,
    )
    @test occursin(
        "baseline_land_rent = base.w .* base.L ./ fund.H",
        figure_source,
    )
    @test occursin(
        "_level_map(log.(base.w), fund, \"Log wage\")",
        figure_source,
    )
    @test occursin(
        "_level_map(log.(base.L), fund, \"Log population\")",
        figure_source,
    )
    @test occursin(
        "_level_map(log.(base.P), fund, \"Log price index\")",
        figure_source,
    )
    @test occursin(
        "_level_map(log.(baseline_land_rent), fund, \"Log land rent\")",
        figure_source,
    )
end
