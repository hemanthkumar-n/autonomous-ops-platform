#!/bin/bash

# ─────────────────────────────────────────────
#  tshelper - Linux Troubleshooting Helper Tool
#  Usage:
#    ./tshelper.sh             → interactive menu
#    ./tshelper.sh <command>   → run directly
# ─────────────────────────────────────────────

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# ─── Banner ────────────────────────────────────
print_banner() {
  echo -e "${CYAN}${BOLD}"
  echo "  ████████╗███████╗██╗  ██╗███████╗██╗     ██████╗ ███████╗██████╗ "
  echo "     ██╔══╝██╔════╝██║  ██║██╔════╝██║     ██╔══██╗██╔════╝██╔══██╗"
  echo "     ██║   ███████╗███████║█████╗  ██║     ██████╔╝█████╗  ██████╔╝"
  echo "     ██║   ╚════██║██╔══██║██╔══╝  ██║     ██╔═══╝ ██╔══╝  ██╔══██╗"
  echo "     ██║   ███████║██║  ██║███████╗███████╗██║     ███████╗██║  ██║"
  echo "     ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝"
  echo -e "${RESET}"
  echo -e "  ${DIM}Linux Troubleshooting Helper — by tshelper${RESET}"
  echo -e "  ${DIM}─────────────────────────────────────────${RESET}"
  echo ""
}

# ─── Section Header ────────────────────────────
print_section() {
  echo ""
  echo -e "${YELLOW}${BOLD}▶ $1${RESET}"
  echo -e "${DIM}$(printf '─%.0s' {1..50})${RESET}"
}

# ─── Run a command with label ──────────────────
run_cmd() {
  local label="$1"
  local cmd="$2"
  echo -e "${GREEN}  ➤ ${BOLD}$label${RESET} ${DIM}($cmd)${RESET}"
  echo ""
  eval "$cmd"
  echo ""
}

# ─── Commands ──────────────────────────────────

cmd_disk() {
  print_section "Disk Usage"
  run_cmd "Disk space (human-readable)" "df -h"
  run_cmd "Inode usage" "df -i"
  run_cmd "Top 10 largest dirs in current path" "du -ah --max-depth=1 . 2>/dev/null | sort -rh | head -10"
}

cmd_memory() {
  print_section "Memory & Swap"
  run_cmd "Memory overview" "free -h"
  run_cmd "Top 10 memory-hungry processes" "ps aux --sort=-%mem | awk 'NR<=11{print}'"
}

cmd_process() {
  print_section "Process Info"
  run_cmd "All processes (snapshot)" "ps aux --sort=-%cpu | head -20"
  run_cmd "Process tree" "pstree -p 2>/dev/null || ps -ejH 2>/dev/null | head -30"
}

cmd_network() {
  print_section "Network"
  run_cmd "Listening & established ports" "ss -tulp"
  run_cmd "Active connections" "ss -tnp state established"
  run_cmd "Routing table" "ip route"
  run_cmd "Network interfaces" "ip -br addr"
}

cmd_cpu() {
  print_section "CPU Info"
  run_cmd "CPU summary" "lscpu | grep -E 'Model name|Socket|Core|Thread|MHz'"
  run_cmd "Load averages (uptime)" "uptime"
  run_cmd "Top CPU processes" "ps aux --sort=-%cpu | awk 'NR<=11{print}'"
}

cmd_logs() {
  print_section "System Logs (last 30 lines)"
  run_cmd "Kernel / system messages" "journalctl -n 30 --no-pager 2>/dev/null || tail -30 /var/log/syslog 2>/dev/null || tail -30 /var/log/messages 2>/dev/null"
  run_cmd "Auth log (last 10 lines)" "journalctl -u ssh -n 10 --no-pager 2>/dev/null || tail -10 /var/log/auth.log 2>/dev/null"
}

cmd_services() {
  print_section "Services"
  run_cmd "Failed services" "systemctl --failed --no-pager 2>/dev/null"
  run_cmd "Running services" "systemctl list-units --type=service --state=running --no-pager 2>/dev/null | head -20"
}

cmd_all() {
  cmd_disk
  cmd_memory
  cmd_cpu
  cmd_network
  cmd_process
  cmd_services
  cmd_logs
}

# ─── Help ──────────────────────────────────────
print_help() {
  echo -e "${BOLD}Usage:${RESET}"
  echo "  ./tshelper.sh                 → interactive menu"
  echo "  ./tshelper.sh <subcommand>    → run directly"
  echo ""
  echo -e "${BOLD}Subcommands:${RESET}"
  echo "  disk       Disk usage (df -h, du, inodes)"
  echo "  memory     RAM & swap (free -h, top processes)"
  echo "  cpu        CPU info, load averages"
  echo "  network    Ports, connections, routing (ss -tulp)"
  echo "  process    Running processes, process tree"
  echo "  services   Systemd services, failed units"
  echo "  logs       Recent system & auth logs"
  echo "  all        Run all checks"
  echo "  help       Show this message"
  echo ""
}

# ─── Interactive Menu ──────────────────────────
interactive_menu() {
  while true; do
    print_banner
    echo -e "  ${BOLD}Pick a category to troubleshoot:${RESET}"
    echo ""
    echo -e "  ${CYAN}[1]${RESET} 💾  Disk"
    echo -e "  ${CYAN}[2]${RESET} 🧠  Memory & Swap"
    echo -e "  ${CYAN}[3]${RESET} ⚙️   CPU"
    echo -e "  ${CYAN}[4]${RESET} 🌐  Network"
    echo -e "  ${CYAN}[5]${RESET} 🔄  Processes"
    echo -e "  ${CYAN}[6]${RESET} 🛠️   Services"
    echo -e "  ${CYAN}[7]${RESET} 📋  Logs"
    echo -e "  ${CYAN}[8]${RESET} 🚀  Run ALL checks"
    echo -e "  ${RED}[q]${RESET} Exit"
    echo ""
    echo -ne "  ${BOLD}Choice: ${RESET}"
    read -r choice

    case "$choice" in
      1) cmd_disk ;;
      2) cmd_memory ;;
      3) cmd_cpu ;;
      4) cmd_network ;;
      5) cmd_process ;;
      6) cmd_services ;;
      7) cmd_logs ;;
      8) cmd_all ;;
      q|Q) echo -e "\n${DIM}Goodbye!${RESET}\n"; exit 0 ;;
      *) echo -e "\n${RED}Invalid choice. Try again.${RESET}" ;;
    esac

    echo ""
    echo -ne "${DIM}Press Enter to return to menu...${RESET}"
    read -r
    clear
  done
}

# ─── Entry Point ───────────────────────────────
case "$1" in
  disk)     print_banner; cmd_disk ;;
  memory)   print_banner; cmd_memory ;;
  cpu)      print_banner; cmd_cpu ;;
  network)  print_banner; cmd_network ;;
  process)  print_banner; cmd_process ;;
  services) print_banner; cmd_services ;;
  logs)     print_banner; cmd_logs ;;
  all)      print_banner; cmd_all ;;
  help|--help|-h) print_banner; print_help ;;
  "")       clear; interactive_menu ;;
  *)
    echo -e "${RED}Unknown command: $1${RESET}"
    echo ""
    print_help
    exit 1
    ;;
esac
