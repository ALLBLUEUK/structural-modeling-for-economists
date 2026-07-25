module LectureFigures

using Plots
using Statistics
using Printf

export FIGURE_FILENAMES,
       save_all_figures,
       write_replication_summary

const FIGURE_FILENAMES = [
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

function _theme!()
    default(
        fontfamily = "Computer Modern",
        grid = false,
        titlefontsize = 18,
        guidefontsize = 15,
        tickfontsize = 14,
        colorbar_titlefontsize = 14,
        colorbar_tickfontsize = 13,
        dpi = 220,
    )
end

function _region_ticks(count)
    return unique(round.(Int, range(1, count; length=6)))
end

function _tick_label(value)
    magnitude = abs(value)
    digits =
        magnitude >= 100 ? 0 :
        magnitude >= 10 ? 1 :
        magnitude >= 1 ? 2 : 3
    label = @sprintf("%.*f", digits, value)
    label = replace(label, r"(\.\d*?[1-9])0+$" => s"\1")
    label = replace(label, r"\.0+$" => "")
    return label == "-0" ? "0" : label
end

function _colorbar_ticks(values; neutral=nothing)
    sample = Float64.(vec(values))
    lower, upper = extrema(sample)
    ticks = Float64[lower]

    if lower < upper
        if !isnothing(neutral)
            center = Float64(neutral)
            negative = sample[sample .< center]
            positive = sample[sample .> center]
            !isempty(negative) && push!(ticks, median(negative))
            lower <= center <= upper && push!(ticks, center)
            !isempty(positive) && push!(ticks, median(positive))
        else
            append!(ticks, quantile(sample, [0.25, 0.50, 0.75]))
        end
        push!(ticks, upper)
    end

    ticks = sort!(unique(ticks))
    return ticks, _tick_label.(ticks)
end

function _nice_clims(values; neutral=nothing, target_intervals=7)
    sample = Float64.(vec(values))
    lower, upper = extrema(sample)
    if !isnothing(neutral)
        lower = min(lower, Float64(neutral))
        upper = max(upper, Float64(neutral))
    end
    if lower == upper
        padding = max(abs(lower), 1.0) * 0.01
        return lower - padding, upper + padding
    end

    raw_step = (upper - lower) / target_intervals
    power = 10.0^floor(log10(raw_step))
    fraction = raw_step / power
    nice_fraction =
        fraction <= 1.0 ? 1.0 :
        fraction <= 2.0 ? 2.0 :
        fraction <= 2.5 ? 2.5 :
        fraction <= 5.0 ? 5.0 : 10.0
    step = nice_fraction * power
    return floor(lower / step) * step, ceil(upper / step) * step
end

function _location_map(
    values,
    fund,
    title;
    color=nothing,
    clims=nothing,
    colorbar_ticks=_colorbar_ticks(values),
    tickfontsize=16,
    guidefontsize=17,
    titlefontsize=19,
    colorbar_tickfontsize=15,
    left_margin=3Plots.mm,
    right_margin=2Plots.mm,
    show_colorbar=true,
)
    palette = isnothing(color) ? _quantile_gradient(values) : color
    country_ticks = (
        [
            round(Int, (1 + fund.half) / 2),
            round(Int, (fund.half + 1 + fund.N) / 2),
        ],
        ["West", "East"],
    )
    region_ticks = _region_ticks(fund.N)
    p = heatmap(
        reshape(values, fund.N, fund.N);
        title = title,
        color = palette,
        clims = clims,
        aspect_ratio = :none,
        xlabel = "",
        ylabel = "Region within country",
        xticks = country_ticks,
        yticks = region_ticks,
        tickfontsize = tickfontsize,
        guidefontsize = guidefontsize,
        framestyle = :axes,
        foreground_color_axis = :white,
        foreground_color_border = :white,
        foreground_color_guide = :black,
        foreground_color_text = :black,
        colorbar = show_colorbar,
        colorbar_ticks = colorbar_ticks,
        colorbar_tickfontsize = colorbar_tickfontsize,
        margin = 0Plots.mm,
        left_margin = left_margin,
        right_margin = right_margin,
        top_margin = 5Plots.mm,
        bottom_margin = 5Plots.mm,
        titlefontsize = titlefontsize,
    )
    vline!(
        p,
        [fund.half + 0.5];
        color = :black,
        linewidth = 2.5,
        label = false,
    )
    return p
end

function _add_bilateral_country_boundaries!(p, fund)
    boundary = fund.NN ÷ 2 + 0.5
    vline!(
        p,
        [boundary];
        color = :black,
        linewidth = 2.5,
        label = false,
    )
    hline!(
        p,
        [boundary];
        color = :black,
        linewidth = 2.5,
        label = false,
    )
    return p
end

function _quantile_gradient(values)
    probabilities = [0.0, 0.50, 0.80, 0.95, 0.99, 1.0]
    palette = [
        :white,
        :lightcyan,
        :lightskyblue,
        :deepskyblue,
        :royalblue,
        :midnightblue,
    ]
    levels = quantile(vec(values), probabilities)
    span = levels[end] - levels[1]
    positions =
        span > 0 ? (levels .- levels[1]) ./ span : probabilities
    for index in 2:length(positions)
        positions[index] =
            max(positions[index], positions[index - 1] + eps(Float64))
    end
    positions[end] = 1.0
    return cgrad(palette, positions)
end

function _level_map(values, fund, title; clims=extrema(values))
    return _location_map(
        values,
        fund,
        title;
        color = _quantile_gradient(values),
        clims = clims,
    )
end

function _truncated_change_clims(
    values;
    lower_probability::Float64=0.01,
    upper_probability::Float64=0.99,
)
    flattened = Float64.(vec(values))
    lower = min(quantile(flattened, lower_probability), 0.0)
    upper = max(quantile(flattened, upper_probability), 0.0)
    actual_lower, actual_upper = extrema(flattened)
    lower == actual_lower && actual_lower < actual_upper &&
        (lower = min(
            quantile(
                flattened[flattened .> actual_lower],
                lower_probability,
            ),
            0.0,
        ))
    upper == actual_upper && actual_lower < actual_upper &&
        (upper = max(
            quantile(
                flattened[flattened .< actual_upper],
                upper_probability,
            ),
            0.0,
        ))
    if actual_lower < 0.0 && lower >= 0.0
        negative = flattened[flattened .< 0.0]
        candidate = quantile(flattened, 0.05)
        lower =
            candidate < 0.0 ? candidate : quantile(negative, 0.90)
    end
    if actual_upper > 0.0 && upper <= 0.0
        positive = flattened[flattened .> 0.0]
        candidate = quantile(flattened, 0.95)
        upper =
            candidate > 0.0 ? candidate : quantile(positive, 0.10)
    end
    if lower == upper
        padding = max(abs(lower), 1.0) * 0.01
        return lower - padding, upper + padding
    end
    return lower, upper
end

function _change_color_sets()
    negative_colors = [
        colorant"#6D5AAE",
        colorant"#4145A5",
        colorant"#2F6FC1",
        colorant"#2799C6",
        colorant"#2CBCC1",
        colorant"#75D3C7",
        colorant"#B9E8DF",
        colorant"#E1EEEE",
        colorant"#D9D9D9",
    ]
    positive_colors = [
        :lightgray,
        :lightyellow,
        :gold,
        :darkorange1,
        :tomato,
        :indianred3,
    ]
    return negative_colors, positive_colors
end

function _linear_change_palette(clims)
    lower, upper = clims
    negative_colors, positive_colors = _change_color_sets()
    if lower < 0.0 < upper
        center = -lower / (upper - lower)
        negative_positions =
            collect(range(0.0, center; length=length(negative_colors)))
        positive_positions =
            collect(range(center, 1.0; length=length(positive_colors)))
        return cgrad(
            vcat(negative_colors, positive_colors[2:end]),
            vcat(negative_positions, positive_positions[2:end]),
        )
    elseif upper <= 0.0
        return cgrad(negative_colors)
    else
        return cgrad(positive_colors)
    end
end

function _quantile_change_palette(values, clims)
    lower, upper = clims
    sample = Float64.(vec(values))
    negative_colors, positive_colors = _change_color_sets()
    colors = Any[]
    positions = Float64[]

    function add_knot(raw_value, color)
        position = clamp(
            (raw_value - lower) / (upper - lower),
            0.0,
            1.0,
        )
        if isempty(positions) || position > positions[end] + 1.0e-10
            push!(positions, position)
            push!(colors, color)
        end
    end

    if lower < 0.0
        negative = sample[(sample .> lower) .& (sample .< 0.0)]
        gradient = cgrad(negative_colors)
        add_knot(lower, get(gradient, 0.0))
        if !isempty(negative)
            for probability in range(0.0, 1.0; length=33)[2:end-1]
                add_knot(
                    quantile(negative, probability),
                    get(gradient, probability),
                )
            end
        end
        add_knot(min(0.0, upper), :lightgray)
    end

    if lower <= 0.0 <= upper
        add_knot(0.0, :lightgray)
    end

    if upper > 0.0
        positive = sample[(sample .> 0.0) .& (sample .< upper)]
        gradient = cgrad(positive_colors)
        isempty(positions) && add_knot(lower, :lightgray)
        if !isempty(positive)
            for probability in range(0.0, 1.0; length=33)[2:end-1]
                add_knot(
                    quantile(positive, probability),
                    get(gradient, probability),
                )
            end
        end
        add_knot(upper, get(gradient, 1.0))
    end

    return cgrad(colors, positions)
end

function _truncated_colorbar_ticks(values, clims)
    lower, upper = clims
    ticks = collect(range(lower, upper; length=5))
    if lower < 0.0 < upper
        span = upper - lower
        ticks = [
            tick for tick in ticks
            if tick == lower || tick == upper ||
               abs(tick) > 0.08 * span
        ]
        if min(-lower, upper) > 0.08 * span
            push!(ticks, 0.0)
        end
        ticks = sort!(unique(ticks))
    end
    labels = _tick_label.(ticks)
    actual_lower, actual_upper = extrema(Float64.(vec(values)))
    actual_lower < lower &&
        (labels[1] = "≤" * labels[1])
    actual_upper > upper &&
        (labels[end] = "≥" * labels[end])
    return ticks, labels
end

function _change_map(
    values,
    fund,
    title;
    lower_probability::Float64=0.01,
    upper_probability::Float64=0.99,
    show_colorbar::Bool=true,
    quantile_colors::Bool=false,
)
    clims = _truncated_change_clims(
        values;
        lower_probability=lower_probability,
        upper_probability=upper_probability,
    )
    palette =
        quantile_colors ?
        _quantile_change_palette(values, clims) :
        _linear_change_palette(clims)
    return _location_map(
        values,
        fund,
        title;
        color = palette,
        clims = clims,
        colorbar_ticks = _truncated_colorbar_ticks(values, clims),
        tickfontsize = 22,
        guidefontsize = 22,
        titlefontsize = 22,
        colorbar_tickfontsize = 20,
        left_margin = 8Plots.mm,
        show_colorbar = show_colorbar,
    )
end

function _change_colorbar(
    values;
    lower_probability::Float64=0.01,
    upper_probability::Float64=0.99,
    quantile_colors::Bool=false,
)
    clims = _truncated_change_clims(
        values;
        lower_probability=lower_probability,
        upper_probability=upper_probability,
    )
    lower, upper = clims
    ticks, labels = _truncated_colorbar_ticks(values, clims)
    resolution = 256
    tick_positions =
        1.0 .+
        (resolution - 1.0) .* (ticks .- lower) ./ (upper - lower)
    palette =
        quantile_colors ?
        _quantile_change_palette(values, clims) :
        _linear_change_palette(clims)
    return heatmap(
        reshape(
            collect(range(lower, upper; length=resolution)),
            resolution,
            1,
        );
        color = palette,
        clims = clims,
        colorbar = false,
        xticks = false,
        yticks = (tick_positions, labels),
        ymirror = true,
        tickfontsize = 16,
        framestyle = :box,
        foreground_color_axis = :black,
        foreground_color_border = :black,
        foreground_color_text = :black,
        margin = 0Plots.mm,
        left_margin = 0Plots.mm,
        right_margin = 8Plots.mm,
        top_margin = 5Plots.mm,
        bottom_margin = 5Plots.mm,
    )
end

function _save_fundamentals(outdir, fund)
    pA = _level_map(fund.A, fund, "Productivity A")
    figure = plot(
        pA;
        size = (720, 560),
        margin = 0Plots.mm,
        left_margin = 8Plots.mm,
        right_margin = 4Plots.mm,
        bottom_margin = 10Plots.mm,
        top_margin = 3Plots.mm,
    )
    savefig(figure, joinpath(outdir, "worked_example_fundamentals.png"))
end

function _save_trade_costs(outdir, fund)
    p = heatmap(
        fund.d;
        title = "Baseline iceberg trade costs d[n,i]",
        color = _quantile_gradient(fund.d),
        clims = extrema(fund.d),
        aspect_ratio = :none,
        xlabel = "Supplier location i",
        ylabel = "Destination location n",
        colorbar = true,
        colorbar_ticks = _colorbar_ticks(fund.d),
        margin = 2Plots.mm,
    )
    _add_bilateral_country_boundaries!(p, fund)
    savefig(
        plot(p; size=(1000, 760), margin=1Plots.mm),
        joinpath(outdir, "worked_example_trade_costs.png"),
    )
end

function _save_baseline(outdir, base, fund)
    baseline_land_rent = base.w .* base.L ./ fund.H
    pL = _level_map(log.(base.L), fund, "Log population")
    pw = _level_map(log.(base.w), fund, "Log wage")
    pP = _level_map(log.(base.P), fund, "Log price index")
    pr = _level_map(log.(baseline_land_rent), fund, "Log land rent")
    figure = plot(
        pL,
        pw,
        pr,
        pP;
        layout = (2, 2),
        size = (1650, 900),
        margin = 0Plots.mm,
        left_margin = 6Plots.mm,
        right_margin = 6Plots.mm,
        bottom_margin = 6Plots.mm,
        top_margin = 2Plots.mm,
    )
    savefig(figure, joinpath(outdir, "worked_example_baseline.png"))
end

function _trade_share_heatmap(base, fund)
    shares = 100.0 .* base.pi
    p = heatmap(
        shares;
        title = "Bilateral shares pi[n,i] (%)",
        color = _quantile_gradient(shares),
        clims = extrema(shares),
        aspect_ratio = :none,
        xlabel = "Supplier location i",
        ylabel = "Destination location n",
        colorbar = true,
        colorbar_ticks = _colorbar_ticks(shares),
        margin = 2Plots.mm,
    )
    return _add_bilateral_country_boundaries!(p, fund)
end

function _trade_cost_trade_scatter(base, fund)
    off_diagonal =
        [n != i for n in 1:fund.NN, i in 1:fund.NN]
    domestic = off_diagonal .& .!fund.cross_border
    international = off_diagonal .& fund.cross_border
    expenditure = base.w .* base.L
    bilateral_trade =
        base.pi .* reshape(expenditure, :, 1)
    log_bilateral_trade = log.(bilateral_trade)

    p = scatter(
        fund.d[domestic],
        log_bilateral_trade[domestic];
        title = "Trade costs and log bilateral expenditure",
        xlabel = "Iceberg trade cost tau[n,i]",
        ylabel = "log X[n,i]",
        markercolor = :royalblue,
        markeralpha = 0.10,
        markersize = 1.1,
        markerstrokewidth = 0,
        label = "Within country",
        framestyle = :box,
        legend = :topright,
        margin = 5Plots.mm,
        bottom_margin = 9Plots.mm,
    )
    scatter!(
        p,
        fund.d[international],
        log_bilateral_trade[international];
        markercolor = :firebrick,
        markeralpha = 0.10,
        markersize = 1.1,
        markerstrokewidth = 0,
        label = "Across border",
    )
    return p
end

function _save_trade_matrix(outdir, base, fund)
    figure = plot(
        _trade_share_heatmap(base, fund),
        _trade_cost_trade_scatter(base, fund);
        layout = @layout([matrix{0.53w} scatter]),
        size = (1500, 650),
        margin = 0Plots.mm,
        left_margin = 5Plots.mm,
        right_margin = 5Plots.mm,
        bottom_margin = 6Plots.mm,
        top_margin = 3Plots.mm,
    )
    savefig(figure, joinpath(outdir, "worked_example_trade_matrix.png"))
end

function _hat_palette(values)
    lower = min(minimum(values), 1.0)
    upper = max(maximum(values), 1.0)
    if lower == upper
        return (
            color = cgrad([:lightgray, :lightgray]),
            clims = (1.0 - 0.01, 1.0 + 0.01),
        )
    elseif upper == 1.0
        return (
            color = cgrad([:navy, :lightgray]),
            clims = (lower, upper),
        )
    elseif lower == 1.0
        return (
            color = cgrad([:lightgray, :firebrick]),
            clims = (lower, upper),
        )
    end

    center = (1.0 - lower) / (upper - lower)
    return (
        color = cgrad(
            [:navy, :lightgray, :firebrick],
            [0.0, center, 1.0],
        ),
        clims = (lower, upper),
    )
end

function _hat_matrix_map(values, fund, title)
    palette = _hat_palette(values)
    ticks = _region_ticks(fund.NN)
    p = heatmap(
        values;
        title = title,
        color = palette.color,
        clims = palette.clims,
        aspect_ratio = :none,
        xlabel = "Supplier location i",
        ylabel = "Destination location n",
        xticks = ticks,
        yticks = ticks,
        tickfontsize = 22,
        guidefontsize = 22,
        framestyle = :axes,
        foreground_color_axis = :white,
        foreground_color_border = :white,
        foreground_color_guide = :black,
        foreground_color_text = :black,
        colorbar = true,
        colorbar_ticks = _colorbar_ticks(values; neutral=1.0),
        colorbar_tickfontsize = 20,
        margin = 0Plots.mm,
        left_margin = 3Plots.mm,
        right_margin = 8Plots.mm,
        top_margin = 2Plots.mm,
        bottom_margin = 5Plots.mm,
        titlefontsize = 24,
    )
    return _add_bilateral_country_boundaries!(p, fund)
end

function _hat_location_map(values, fund, title)
    palette = _hat_palette(values)
    return _location_map(
        values,
        fund,
        title;
        color = palette.color,
        clims = palette.clims,
        colorbar_ticks = _colorbar_ticks(values; neutral=1.0),
        tickfontsize = 22,
        guidefontsize = 22,
        titlefontsize = 24,
        colorbar_tickfontsize = 20,
        right_margin = 8Plots.mm,
    )
end

function _save_shock_figure(path, plot_object)
    savefig(
        plot(plot_object; size=(960, 680), margin=0Plots.mm),
        path,
    )
end

function _save_shock_figures(outdir, fund, experiments)
    _save_shock_figure(
        joinpath(outdir, "worked_example_shock_internal.png"),
        _hat_matrix_map(
            experiments.internal.shock.d_hat,
            fund,
            "Internal trade costs fall by 10%",
        ),
    )
    _save_shock_figure(
        joinpath(outdir, "worked_example_shock_integration.png"),
        _hat_matrix_map(
            experiments.integration.shock.d_hat,
            fund,
            "Cross-border trade costs fall by 10%",
        ),
    )
    _save_shock_figure(
        joinpath(outdir, "worked_example_shock_road.png"),
        _hat_location_map(
            experiments.road.shock.route_cost_hat,
            fund,
            "Road traversal-cost weight: hat = 0.5",
        ),
    )
    _save_shock_figure(
        joinpath(outdir, "worked_example_shock_development.png"),
        _hat_location_map(
            experiments.development.shock.A_hat,
            fund,
            "Productivity hat for three development zones",
        ),
    )
end

function _save_result_figure(outdir, name, experiment, fund)
    result = experiment.result
    land_rent_hat = result.w_hat .* result.L_hat ./ result.H_hat
    real_wage_hat = result.w_hat ./ (
            result.P_hat .^ fund.alpha .*
            land_rent_hat .^ (1.0 - fund.alpha)
        )
    real_wage_change = 100.0 .* (real_wage_hat .- 1.0)
    population_change = 100.0 .* (result.L_hat .- 1.0)
    price_change = 100.0 .* (result.P_hat .- 1.0)
    land_rent_change = 100.0 .* (land_rent_hat .- 1.0)
    lower_probability, upper_probability =
        name == "development" ? (0.10, 0.90) : (0.05, 0.95)
    quantile_colors = name == "development"

    function map_and_bar(values, title)
        return (
            _change_map(
                values,
                fund,
                title;
                lower_probability=lower_probability,
                upper_probability=upper_probability,
                show_colorbar=false,
                quantile_colors=quantile_colors,
            ),
            _change_colorbar(
                values;
                lower_probability=lower_probability,
                upper_probability=upper_probability,
                quantile_colors=quantile_colors,
            ),
        )
    end

    real_wage_map, real_wage_bar =
        map_and_bar(real_wage_change, "Real-wage change (%)")
    population_map, population_bar =
        map_and_bar(population_change, "Population change (%)")
    price_map, price_bar =
        map_and_bar(price_change, "Price-index change (%)")
    rent_map, rent_bar =
        map_and_bar(land_rent_change, "Land-rent change (%)")

    figure = plot(
        real_wage_map,
        real_wage_bar,
        population_map,
        population_bar,
        price_map,
        price_bar,
        rent_map,
        rent_bar;
        layout = grid(
            2,
            4;
            widths=[0.43, 0.07, 0.43, 0.07],
            heights=[0.50, 0.50],
        ),
        size = (1500, 900),
        margin = 0Plots.mm,
        left_margin = 6Plots.mm,
        right_margin = 6Plots.mm,
        bottom_margin = 6Plots.mm,
        top_margin = 2Plots.mm,
    )
    savefig(
        figure,
        joinpath(outdir, "worked_example_results_$(name).png"),
    )
end

function _save_result_figures(outdir, fund, experiments)
    _save_result_figure(
        outdir,
        "internal",
        experiments.internal,
        fund,
    )
    _save_result_figure(
        outdir,
        "integration",
        experiments.integration,
        fund,
    )
    _save_result_figure(
        outdir,
        "road",
        experiments.road,
        fund,
    )
    _save_result_figure(
        outdir,
        "development",
        experiments.development,
        fund,
    )
end

function save_all_figures(outdir, base, fund, experiments)
    mkpath(outdir)
    _theme!()
    _save_baseline(outdir, base, fund)
    _save_fundamentals(outdir, fund)
    _save_trade_costs(outdir, fund)
    _save_trade_matrix(outdir, base, fund)
    _save_shock_figures(outdir, fund, experiments)
    _save_result_figures(outdir, fund, experiments)
    return [joinpath(outdir, filename) for filename in FIGURE_FILENAMES]
end

function _aggregate_foreign_share(base, fund)
    foreign_by_destination =
        vec(sum(base.pi .* fund.cross_border; dims=2))
    expenditure = base.w .* base.L
    return sum(expenditure .* foreign_by_destination) / sum(expenditure)
end

function write_replication_summary(
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
    mkpath(dirname(path))
    open(path, "w") do io
        println(io, "Quantitative Spatial Model — Replication Summary")
        println(io, "Generated from randomly simulated baseline fundamentals.")
        println(io)
        println(io, "Baseline settings")
        println(io, "baseline seed = ", fund.settings.seed)
        println(
            io,
            "road-path seed = ",
            experiments.road.shock.seed,
        )
        println(
            io,
            "development-zone seed = ",
            experiments.development.shock.seed,
        )
        println(io, "grid = ", fund.N, " x ", fund.N)
        println(io, "alpha = ", fund.alpha)
        println(io, "sigma = ", fund.sigma)
        println(io, "kappa = ", fund.kappa)
        println(
            io,
            "standard deviation of log productivity = ",
            fund.settings.productivity_log_sd,
        )
        println(
            io,
            "domestic nonlocal trade-cost factor = ",
            fund.settings.internal_trade_factor,
        )
        println(
            io,
            "international border factor = ",
            fund.settings.international_border_factor,
        )
        println(
            io,
            "cross-country distance normalization = ",
            fund.settings.international_distance_normalization,
        )
        println(io, "distance power = ", fund.settings.distance_power)
        println(io, "F = ", fund.F)
        println(io, "H_i = ", first(fund.H))
        println(io, "total labor = ", fund.LL)
        println(io, "baseline iterations = ", base.iterations)
        println(io, "baseline final diff = ", base.final_diff)
        println(io)
        println(io, "Validation")
        println(
            io,
            "max trade-share row-sum error = ",
            residuals.trade_share_adding_up,
        )
        println(
            io,
            "max goods-market relative residual = ",
            residuals.goods_market_relative,
        )
        println(io, "west labor residual = ", residuals.west_population)
        println(io, "east labor residual = ", residuals.east_population)
        println(
            io,
            "baseline own-location expenditure share = ",
            moments.own_location,
        )
        println(
            io,
            "baseline domestic-nonlocal expenditure share = ",
            moments.domestic_nonlocal,
        )
        println(
            io,
            "baseline foreign expenditure share = ",
            moments.foreign,
        )
        println(io)
        println(io, "Internal trade liberalization")
        println(
            io,
            "exact-hat iterations = ",
            experiments.internal.result.iterations,
        )
        println(
            io,
            "exact-hat final diff = ",
            experiments.internal.result.final_diff,
        )
        println(io, "west = ", internal_stats.west)
        println(io, "east = ", internal_stats.east)
        println(io)
        println(io, "Bilateral border liberalization")
        println(
            io,
            "exact-hat iterations = ",
            experiments.integration.result.iterations,
        )
        println(
            io,
            "exact-hat final diff = ",
            experiments.integration.result.final_diff,
        )
        println(
            io,
            "counterfactual foreign expenditure share = ",
            integration_stats.foreign_expenditure_share,
        )
        println(io, "west = ", integration_stats.west)
        println(io, "east = ", integration_stats.east)
        println(io)
        println(io, "Road construction")
        println(
            io,
            "exact-hat iterations = ",
            experiments.road.result.iterations,
        )
        println(
            io,
            "exact-hat final diff = ",
            experiments.road.result.final_diff,
        )
        println(io, "west = ", road_stats.west)
        println(io, "east = ", road_stats.east)
        println(io)
        println(io, "Development zones")
        println(
            io,
            "exact-hat iterations = ",
            experiments.development.result.iterations,
        )
        println(
            io,
            "exact-hat final diff = ",
            experiments.development.result.final_diff,
        )
        println(io, "west = ", development_stats.west)
        println(io, "east = ", development_stats.east)
    end
    return path
end

end
