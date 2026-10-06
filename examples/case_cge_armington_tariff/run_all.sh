#!/usr/bin/env bash
# 一键复现：armington_tariff（strucmod v0.3 工作流验收案例；示意数据）
set -e
export PYTHONIOENCODING=utf-8
python model/03_solve/armington_tariff/solve.py --purge --checks --scenario S1 --scenario S2
python model/03_solve/armington_tariff/counterfactuals.py
python model/03_solve/armington_tariff/latex_tables.py
