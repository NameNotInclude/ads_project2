#!/bin/bash
#
# compile_run.sh
#   编译 main，然后把 testdata 下的实例逐个喂给 main，结果写进 result/*.csv
#
# 用法:
#   ./sh/compile_run.sh [iter] [pattern]
#
#   iter     每个实例重复运行的次数，默认 1
#   pattern  文件通配，默认 'testdata/*/*.txt'
#
# 例子:
#   ./sh/compile_run.sh                          # 全部实例，各跑 1 次
#   ./sh/compile_run.sh 5                        # 全部实例，各跑 5 次取总/均
#   ./sh/compile_run.sh 3 'testdata/tier0[1-4]*/*.txt'   # 只跑小规模
#   ./sh/compile_run.sh 1 'testdata/tier09*/*.txt'       # 只跑某个 tier
#

set -u

# 始终在项目根目录下工作（main 里用相对路径 result/*.csv）
cd "$(dirname "$0")/.." || exit 1

ITER=${1:-1}
PATTERN=${2:-testdata/*/*.txt}

# ---------------------------------------------------------------- 1. 编译
echo "[1/3] 编译 main ..."
gcc -O2 -Wall -o main main.c method/base.c method/dominance.c method/bounding.c
if [ $? -ne 0 ]; then
    echo "编译失败，脚本退出" >&2
    exit 1
fi

# ---------------------------------------------------------------- 2. 清空结果
# main 是以追加模式打开 csv 的，先清空，避免上几次的结果混进来
echo "[2/3] 清空 result/*.csv ..."
mkdir -p result
: > result/base.csv
: > result/dominance.csv
: > result/bound.csv

# ---------------------------------------------------------------- 3. 跑实例
echo "[3/3] 运行 (iter=$ITER, pattern=$PATTERN)"

count=0
fail=0
start_all=$(date +%s%N)

shopt -s nullglob
for f in $PATTERN; do
    count=$((count + 1))
    ./main "$f" "$ITER"
    if [ $? -ne 0 ]; then
        echo
        echo "  运行失败: $f" >&2
        fail=$((fail + 1))
    fi
    if [ -t 1 ]; then
        printf "\r  %3d 个实例已跑: %-55s" "$count" "${f#testdata/}"
    else
        printf "  %3d 个实例已跑: %s\n" "$count" "${f#testdata/}"
    fi
done
shopt -u nullglob
echo

if [ "$count" -eq 0 ]; then
    echo "没有匹配到任何文件: $PATTERN" >&2
    exit 1
fi

# main 每次运行都会写一遍表头，这里只保留第一条（只删重复表头，不删数据）
for f in result/base.csv result/dominance.csv result/bound.csv; do
    [ -s "$f" ] || continue
    awk 'NR == 1 || !/^file,num_of_item/' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done

rows_after=$(grep -c . result/base.csv 2>/dev/null || echo 0)
# ---------------------------------------------------------------- 汇总
end_all=$(date +%s%N)

echo
echo "实例数: $count    失败: $fail    总耗时: $(( (end_all - start_all) / 1000000 )) ms"
echo "result/base.csv 行数: $rows_after （已清空重跑）"
echo "结果文件: result/base.csv  result/dominance.csv  result/bound.csv"
echo

print_sum()   # $1 = csv, $2 = 显示名
{
    awk -F, -v name="$2" '
        NR > 1 && NF >= 6 {
            tot += $5 + 0
            n++
        }
        END {
            if (n == 0) { printf "  %-6s 无数据\n", name; exit }
            printf "  %-6s 总 %12.3f ms   平均 %10.3f ms   (%d 个实例)\n",
                   name, tot, tot / n, n
        }
    ' "$1"
}

echo "各算法时间汇总（tot_time 之和与平均）:"
print_sum result/base.csv      "DP-1"
print_sum result/dominance.csv "3.4"
print_sum result/bound.csv     "3.5"

# 负时间通常说明计时写反了
if grep -q ',-' result/base.csv 2>/dev/null; then
    echo >&2
    echo "警告: csv 里出现负数时间。检查 main.c 里的" >&2
    echo "      time_base += start - end;   // 应为 end - start" >&2
fi
