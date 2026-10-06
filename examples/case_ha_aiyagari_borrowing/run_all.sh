#!/usr/bin/env bash
# 一键复现：aiyagari_borrowing（strucmod v0.3 工作流验收案例）
set -e
export PYTHONIOENCODING=utf-8
S=model/03_solve/aiyagari_borrowing/solve.py
python $S --scenario baseline
for b in 0.5 1 2 4 8; do python $S --scenario b$b --set b=$b; done
python $S --scenario limit_sigma0 --set sigma=0.001 --set r_hi_eps=1e-8 --set a_max=200
for b in 0 2 8; do python $S --scenario rob_nz15_b$b --set n_z=15 --set b=$b; done
# Tauchen 对照情形按设计 validated=False（退出码 2），不中断
for b in 0 8; do python $S --scenario cmp_tauchen_b$b --set use_rouwenhorst=0 --set b=$b || true; done
python model/03_solve/aiyagari_borrowing/tables_figures.py
python model/03_solve/aiyagari_borrowing/latex_tables.py
