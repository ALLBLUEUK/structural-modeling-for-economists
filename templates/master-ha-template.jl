# =====================================================================
# model/03_solve/<MODEL_NAME>/run.jl
# 语言版本：Julia 1.10
# 模型：<MODEL_NAME>（异质主体 / sequence-space 框架）
# spec：model/01_setup/<MODEL_NAME>/spec.md
# 创建：<author> <YYYY-MM-DD>
# =====================================================================

using Pkg
Pkg.activate(joinpath(@__DIR__, "..", "..", ".."))

using LinearAlgebra
using JSON3
using Dates
# 推荐：using SequenceJacobian, QuantEcon

include(joinpath(@__DIR__, "..", "..", "_utils", "setup_paths.jl"))
include(joinpath(@__DIR__, "..", "..", "_utils", "io.jl"))

# ---------------------------------------------------------------------
# 1. 加载校准
# ---------------------------------------------------------------------
const MODEL_NAME = "<MODEL_NAME>"
params = load_calibration(MODEL_NAME)

# ---------------------------------------------------------------------
# 2. 模型构建
# ---------------------------------------------------------------------
struct Model
    β::Float64       # 折现因子
    γ::Float64       # 风险厌恶
    r::Float64       # 利率
    w::Float64       # 工资
    a_grid::Vector{Float64}
    z_grid::Vector{Float64}
    Π::Matrix{Float64}     # 收入转移矩阵
end

function build_model(p::Dict)
    a_grid = collect(range(p["a_min"], p["a_max"]; length=p["n_a"]))
    # ... 构造收入网格与转移矩阵
    Model(p["beta"], p["gamma"], p["r"], p["w"], a_grid, [], zeros(0,0))
end

# ---------------------------------------------------------------------
# 3. 稳态（家庭策略 → 总量分布 → 价格清算）
# ---------------------------------------------------------------------
function steady_state(m::Model; tol=1e-8, maxiter=2000)
    # EGM / VFI 求家庭策略
    # 用 stationary distribution 求总量
    # 校准 r, w 使资产市场出清
    # 返回：策略函数、分布、价格、稳态量
    return Dict("status" => "TODO", "tol" => tol)
end

# ---------------------------------------------------------------------
# 4. 雅可比（sequence-space）
# ---------------------------------------------------------------------
function sequence_jacobian(m::Model, ss; T=300)
    # 推荐使用 SequenceJacobian.jl
    return Dict("T" => T)
end

# ---------------------------------------------------------------------
# 5. 主流程
# ---------------------------------------------------------------------
function main()
    @info "[$(MODEL_NAME)] 构建模型"
    m = build_model(params)

    @info "[$(MODEL_NAME)] 求稳态"
    ss = steady_state(m)
    save_checkpoint(joinpath("output", "checkpoints", "$(MODEL_NAME)_ss.json"), ss)

    @info "[$(MODEL_NAME)] 求 sequence-space 雅可比"
    J = sequence_jacobian(m, ss)
    save_checkpoint(joinpath("output", "checkpoints", "$(MODEL_NAME)_jacobian.json"), J)

    @info "[$(MODEL_NAME)] 完成。后续由 simulate-irf 接管"
end

main()
