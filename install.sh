#!/usr/bin/env bash
# install.sh — strucmod 多模式安装器
#
# 用法：
#   bash install.sh <mode> [target]
#
# Modes:
#   claude-global    将本仓库放到 ~/.claude/plugins/strucmod/（Claude Code 全局插件）
#   claude-local     将本仓库放到 <target>/.claude/plugins/strucmod/（Claude Code 项目级插件，默认 target=pwd）
#   codex            将本仓库放到 <target>/.claude/plugins/strucmod/ 并在 <target> 根分发 AGENTS.md（Codex CLI 用）
#   cursor           将本仓库放到 <target>/.claude/plugins/strucmod/ 并在 <target>/.cursor/rules/ 分发 .mdc（Cursor 用）
#   aider            将本仓库放到 <target>/.claude/plugins/strucmod/ 并在 <target> 根分发 .aider.conf.yml（Aider 用）
#   windsurf         将本仓库放到 <target>/.claude/plugins/strucmod/ 并在 <target> 根分发 .windsurfrules（Windsurf 用）
#   copilot          将本仓库放到 <target>/.claude/plugins/strucmod/ 并在 <target>/.github/ 分发 copilot-instructions.md
#   universal        codex + cursor + aider + windsurf + copilot 一并分发（推荐：让任何 agent 都能用）
#
# 示例：
#   bash install.sh claude-global
#   bash install.sh claude-local ~/research/my-rbc-paper
#   bash install.sh universal    ~/research/my-rbc-paper

set -euo pipefail

MODE="${1:-}"
TARGET="${2:-$(pwd)}"

if [[ -z "$MODE" ]]; then
  echo "用法：bash install.sh <mode> [target]"
  echo ""
  echo "Modes: claude-global | claude-local | codex | cursor | aider | windsurf | copilot | universal"
  exit 1
fi

# 找到本仓库（脚本所在目录）
PLUGIN_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$PLUGIN_SRC/.claude-plugin/plugin.json" ]]; then
  echo "[install] ❌ 找不到 plugin manifest：$PLUGIN_SRC/.claude-plugin/plugin.json"
  echo "         本脚本必须从 strucmod 仓库根目录运行。"
  exit 2
fi

# ----- 工具：复制 plugin 到 .claude/plugins/strucmod/ -----
install_plugin() {
  local dest_root="$1"
  local plugin_dest="$dest_root/.claude/plugins/strucmod"
  if [[ -d "$plugin_dest" ]]; then
    echo "[install] $plugin_dest 已存在，先删旧版"
    rm -rf "$plugin_dest"
  fi
  mkdir -p "$plugin_dest"
  # 复制除 .git 和大文件外的所有内容
  for entry in "$PLUGIN_SRC"/* "$PLUGIN_SRC"/.[!.]*; do
    [[ -e "$entry" ]] || continue
    case "$(basename "$entry")" in
      .git|.git-*) continue ;;
    esac
    cp -r "$entry" "$plugin_dest/"
  done
  echo "[install] ✅ plugin installed at $plugin_dest"
}

# ----- 工具：分发适配文件到目标根 -----
distribute_adapter() {
  local dest_root="$1"
  local agent="$2"
  local adapters="$PLUGIN_SRC/templates/adapters"

  case "$agent" in
    codex)
      cp "$adapters/AGENTS.md" "$dest_root/AGENTS.md"
      echo "[install]   + AGENTS.md (Codex)"
      ;;
    cursor)
      mkdir -p "$dest_root/.cursor/rules"
      cp "$adapters/cursor/rules/strucmod.mdc" "$dest_root/.cursor/rules/"
      cp "$adapters/AGENTS.md" "$dest_root/AGENTS.md" 2>/dev/null || true
      echo "[install]   + .cursor/rules/strucmod.mdc (Cursor)"
      ;;
    aider)
      cp "$adapters/.aider.conf.yml" "$dest_root/.aider.conf.yml"
      cp "$adapters/AGENTS.md" "$dest_root/AGENTS.md" 2>/dev/null || true
      echo "[install]   + .aider.conf.yml (Aider)"
      ;;
    windsurf)
      cp "$adapters/.windsurfrules" "$dest_root/.windsurfrules"
      cp "$adapters/AGENTS.md" "$dest_root/AGENTS.md" 2>/dev/null || true
      echo "[install]   + .windsurfrules (Windsurf)"
      ;;
    copilot)
      mkdir -p "$dest_root/.github"
      cp "$adapters/github/copilot-instructions.md" "$dest_root/.github/"
      cp "$adapters/AGENTS.md" "$dest_root/AGENTS.md" 2>/dev/null || true
      echo "[install]   + .github/copilot-instructions.md (Copilot)"
      ;;
  esac
}

case "$MODE" in
  claude-global)
    DEST="${HOME}"
    install_plugin "$DEST"
    echo ""
    echo "✅ Claude Code 全局插件安装完成。"
    echo "   你在任何目录里跑 claude，skills 都会自动可用。"
    ;;

  claude-local)
    install_plugin "$TARGET"
    echo ""
    echo "✅ Claude Code 项目级插件安装到 $TARGET/.claude/plugins/strucmod/"
    echo "   在 $TARGET 下跑 claude，skills 会自动加载。"
    ;;

  codex|cursor|aider|windsurf|copilot)
    install_plugin "$TARGET"
    distribute_adapter "$TARGET" "$MODE"
    echo ""
    echo "✅ $MODE 适配安装完成。在 $TARGET 下打开对应 agent 即可。"
    ;;

  universal)
    install_plugin "$TARGET"
    for ag in codex cursor aider windsurf copilot; do
      distribute_adapter "$TARGET" "$ag"
    done
    echo ""
    echo "✅ 通用安装完成（Codex + Cursor + Aider + Windsurf + Copilot 适配文件全部分发）。"
    echo "   $TARGET 现可用任意 agent 打开。"
    ;;

  *)
    echo "[install] ❌ 未知模式：$MODE"
    echo "         可用：claude-global | claude-local | codex | cursor | aider | windsurf | copilot | universal"
    exit 3
    ;;
esac
