#!/bin/bash
USERNAME=$(echo $JUPYTERHUB_USER)
WORK=/home/jovyan/work
COMMON=/tmp/notebooks/common
NBB=/tmp/notebooks/b
NBA=/tmp/notebooks/a
NBP=/tmp/notebooks/p
NBI=/tmp/notebooks/industrial
mkdir -p $WORK /home/jovyan/.jupyter $WORK/student_code_framework

# ===== 1. jupyter-ai config (ALL users) =====
cat > /home/jovyan/.jupyter/jupyter_ai_config.py << 'JAIC'
import os
os.environ["OPENAI_API_KEY"] = "ollama"
os.environ["OPENAI_API_BASE"] = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
c = get_config()
c.AiProvider.model_id = "qwen2.5-coder:7b"
c.AiProvider.api_base = "http://ollama-master.ai-platform.svc.cluster.local:11434/v1"
c.AiProvider.api_key = "ollama"
JAIC

# ===== 2. Dual guides + code grader =====
    # Teacher-role users get both guides, Student-role users get student guide only
    case "$USERNAME" in
      admin|teacher-zhang|teacher-*|teacher_*|Lecture-*|lecture-*)
        cp $COMMON/guide_teacher $WORK/JUPYTERHUB-OPERATION-GUIDE.md 2>/dev/null
        cp $COMMON/guide_student $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
        ;;
      *)
        cp $COMMON/guide_student $WORK/JUPYTERHUB-STUDENT-GUIDE.md 2>/dev/null
        ;;
    esac
    cp $COMMON/code_grader $WORK/code_grader.py 2>/dev/null

# ===== 3. Course-specific notebooks + code framework =====
case "$USERNAME" in
  # ===== admin: EVERYTHING (all courses, all roles, all frameworks) =====
  admin)
    for cm_dir in $NBB $NBA $NBP $NBI; do
      [ -d "$cm_dir" ] || continue
      for f in $cm_dir/*_student; do
        [ -f "$f" ] || continue
        base=$(basename "$f" | sed 's/_student$//')
        cp "$f" "$WORK/${base}_学生版.ipynb" 2>/dev/null
      done
      for f in $cm_dir/*_teacher; do
        [ -f "$f" ] || continue
        base=$(basename "$f" | sed 's/_teacher$//')
        cp "$f" "$WORK/${base}_教师版.ipynb" 2>/dev/null
      done
    done
    # All code frameworks with proper .py names
    for cm_dir in $NBB $NBA $NBP $NBI; do
      [ -d "$cm_dir" ] || continue
      for f in $cm_dir/fw_*; do
        [ -f "$f" ] || continue
        base=$(basename "$f" | sed 's/^fw_//')
        case "$base" in
          *.py) ;;
          *) base="${base}.py" ;;
        esac
        cp "$f" "$WORK/student_code_framework/$base" 2>/dev/null
      done
    done ;;
  # ===== 02-程序设计基础 =====
  Lecture-B1|lecture-b1)
    cp $NBB/b1_w01_student "$WORK/w01_设备参数初始化_学生版.ipynb" 2>/dev/null
    cp $NBB/b1_w01_teacher "$WORK/w01_设备参数初始化_教师版.ipynb" 2>/dev/null
    cp $NBB/b1_w02_student "$WORK/w02_实时告警系统_学生版.ipynb" 2>/dev/null
    cp $NBB/b1_w02_teacher "$WORK/w02_实时告警系统_教师版.ipynb" 2>/dev/null
    for f in $NBB/fw_w01 $NBB/fw_w02; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B2|lecture-b2)
    cp $NBB/b2_w01_student "$WORK/w01_数据采集入门_学生版.ipynb" 2>/dev/null
    cp $NBB/b2_w01_teacher "$WORK/w01_数据采集入门_教师版.ipynb" 2>/dev/null
    for f in $NBB/fw_w03 $NBB/fw_w04; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B3|lecture-b3)
    cp $NBB/b3_w01_student "$WORK/w01_数据处理基础_学生版.ipynb" 2>/dev/null
    cp $NBB/b3_w01_teacher "$WORK/w01_数据处理基础_教师版.ipynb" 2>/dev/null
    for f in $NBB/fw_w05 $NBB/fw_w06; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B4|lecture-b4)
    cp $NBB/b4_w01_student "$WORK/w01_可视化入门_学生版.ipynb" 2>/dev/null
    cp $NBB/b4_w01_teacher "$WORK/w01_可视化入门_教师版.ipynb" 2>/dev/null
    for f in $NBB/fw_w07 $NBB/fw_w08; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B5|lecture-b5)
    cp $NBB/b5_w01_student "$WORK/w01_综合项目_学生版.ipynb" 2>/dev/null
    cp $NBB/b5_w01_teacher "$WORK/w01_综合项目_教师版.ipynb" 2>/dev/null
    for f in $NBB/fw_w09 $NBB/fw_w10; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B6|lecture-b6)
    cp $NBB/b6_w01_student "$WORK/w01_结业实战_学生版.ipynb" 2>/dev/null
    cp $NBB/b6_w01_teacher "$WORK/w01_结业实战_教师版.ipynb" 2>/dev/null
    for f in $NBB/fw_w11 $NBB/fw_w12; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  # ===== 05-AI应用基础48课时版（W1~W12 工单 M1-1a..Z）=====
  teacher_ai_01|teacher_ai_02)
    # A-course main instructors: full 12-worksheet set (student + teacher versions)
    cp $NBA/a1_m11_student "$WORK/M1-1a_数据清洗与质量评估_学生版.ipynb" 2>/dev/null
    cp $NBA/a1_m11_teacher "$WORK/M1-1a_数据清洗与质量评估_教师版.ipynb" 2>/dev/null
    cp $NBA/a1_m12_student "$WORK/M1-1b_特征设计与优化_学生版.ipynb" 2>/dev/null
    cp $NBA/a1_m12_teacher "$WORK/M1-1b_特征设计与优化_教师版.ipynb" 2>/dev/null
    cp $NBA/a2_m21_student "$WORK/M2-1a_传统分类逻辑回归_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m21_teacher "$WORK/M2-1a_传统分类逻辑回归_教师版.ipynb" 2>/dev/null
    cp $NBA/a2_m22_student "$WORK/M2-2_XGBoost参数调优_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m22_teacher "$WORK/M2-2_XGBoost参数调优_教师版.ipynb" 2>/dev/null
    cp $NBA/a2_m23_student "$WORK/M2-3a_MLP神经网络_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m23_teacher "$WORK/M2-3a_MLP神经网络_教师版.ipynb" 2>/dev/null
    cp $NBA/a2_m24_student "$WORK/M2-3b_CNN或LSTM二选一_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m24_teacher "$WORK/M2-3b_CNN或LSTM二选一_教师版.ipynb" 2>/dev/null
    cp $NBA/a3_m31_student "$WORK/M3-1_ResNet迁移学习_学生版.ipynb" 2>/dev/null
    cp $NBA/a3_m31_teacher "$WORK/M3-1_ResNet迁移学习_教师版.ipynb" 2>/dev/null
    cp $NBA/a3_m32_student "$WORK/M3-2_YOLO实时缺陷检测_学生版.ipynb" 2>/dev/null
    cp $NBA/a3_m32_teacher "$WORK/M3-2_YOLO实时缺陷检测_教师版.ipynb" 2>/dev/null
    cp $NBA/a4_m41_student "$WORK/M4-1_LLM故障诊断_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m41_teacher "$WORK/M4-1_LLM故障诊断_教师版.ipynb" 2>/dev/null
    cp $NBA/a4_m42_student "$WORK/M4-2_RAG知识库问答_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m42_teacher "$WORK/M4-2_RAG知识库问答_教师版.ipynb" 2>/dev/null
    cp $NBA/a4_m43_student "$WORK/M5-1_多智能体检修调度_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m43_teacher "$WORK/M5-1_多智能体检修调度_教师版.ipynb" 2>/dev/null
    cp $NBA/a4_m44_student "$WORK/Z_综合项目答辩_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m44_teacher "$WORK/Z_综合项目答辩_教师版.ipynb" 2>/dev/null
    [ -f $NBA/fw_m11 ] && cp $NBA/fw_m11 "$WORK/student_code_framework/w1_clean_starter.py" 2>/dev/null
    [ -f $NBA/fw_m12 ] && cp $NBA/fw_m12 "$WORK/student_code_framework/w2_feature_starter.py" 2>/dev/null
    [ -f $NBA/fw_m21 ] && cp $NBA/fw_m21 "$WORK/student_code_framework/w3_classify_starter.py" 2>/dev/null
    [ -f $NBA/fw_m22 ] && cp $NBA/fw_m22 "$WORK/student_code_framework/w4_tuning_starter.py" 2>/dev/null
    [ -f $NBA/fw_m23 ] && cp $NBA/fw_m23 "$WORK/student_code_framework/w5_mlp_starter.py" 2>/dev/null
    [ -f $NBA/fw_m24 ] && cp $NBA/fw_m24 "$WORK/student_code_framework/w6_bidding_starter.py" 2>/dev/null
    [ -f $NBA/fw_m31 ] && cp $NBA/fw_m31 "$WORK/student_code_framework/w7_transfer_starter.py" 2>/dev/null
    [ -f $NBA/fw_m32 ] && cp $NBA/fw_m32 "$WORK/student_code_framework/w8_detect_starter.py" 2>/dev/null
    [ -f $NBA/fw_m41 ] && cp $NBA/fw_m41 "$WORK/student_code_framework/w9_prompt_starter.py" 2>/dev/null
    [ -f $NBA/fw_m42 ] && cp $NBA/fw_m42 "$WORK/student_code_framework/w10_rag_starter.py" 2>/dev/null
    [ -f $NBA/fw_m43 ] && cp $NBA/fw_m43 "$WORK/student_code_framework/w11_multiagent_starter.py" 2>/dev/null
    [ -f $NBA/fw_m44 ] && cp $NBA/fw_m44 "$WORK/student_code_framework/w12_defense_starter.py" 2>/dev/null
    ;;
  Lecture-A1|lecture-a1|stu_a1_*|stu-a1-*|teacher_a1_*)
    cp $NBA/a1_m11_student "$WORK/M1-1a_数据清洗与质量评估_学生版.ipynb" 2>/dev/null
    cp $NBA/a1_m11_teacher "$WORK/M1-1a_数据清洗与质量评估_教师版.ipynb" 2>/dev/null
    cp $NBA/a1_m12_student "$WORK/M1-1b_特征设计与优化_学生版.ipynb" 2>/dev/null
    cp $NBA/a1_m12_teacher "$WORK/M1-1b_特征设计与优化_教师版.ipynb" 2>/dev/null
    [ -f $NBA/fw_m11 ] && cp $NBA/fw_m11 "$WORK/student_code_framework/w1_clean_starter.py" 2>/dev/null
    [ -f $NBA/fw_m12 ] && cp $NBA/fw_m12 "$WORK/student_code_framework/w2_feature_starter.py" 2>/dev/null
    ;;
  Lecture-A2|lecture-a2|stu_a2_*|stu-a2-*|teacher_a2_*)
    cp $NBA/a2_m21_student "$WORK/M2-1a_传统分类逻辑回归_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m21_teacher "$WORK/M2-1a_传统分类逻辑回归_教师版.ipynb" 2>/dev/null
    cp $NBA/a2_m22_student "$WORK/M2-2_XGBoost参数调优_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m22_teacher "$WORK/M2-2_XGBoost参数调优_教师版.ipynb" 2>/dev/null
    cp $NBA/a2_m23_student "$WORK/M2-3a_MLP神经网络_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m23_teacher "$WORK/M2-3a_MLP神经网络_教师版.ipynb" 2>/dev/null
    cp $NBA/a2_m24_student "$WORK/M2-3b_CNN或LSTM二选一_学生版.ipynb" 2>/dev/null
    cp $NBA/a2_m24_teacher "$WORK/M2-3b_CNN或LSTM二选一_教师版.ipynb" 2>/dev/null
    [ -f $NBA/fw_m21 ] && cp $NBA/fw_m21 "$WORK/student_code_framework/w3_classify_starter.py" 2>/dev/null
    [ -f $NBA/fw_m22 ] && cp $NBA/fw_m22 "$WORK/student_code_framework/w4_tuning_starter.py" 2>/dev/null
    [ -f $NBA/fw_m23 ] && cp $NBA/fw_m23 "$WORK/student_code_framework/w5_mlp_starter.py" 2>/dev/null
    [ -f $NBA/fw_m24 ] && cp $NBA/fw_m24 "$WORK/student_code_framework/w6_bidding_starter.py" 2>/dev/null
    ;;
  Lecture-A3|lecture-a3|stu_a3_*|stu-a3-*|teacher_a3_*)
    cp $NBA/a3_m31_student "$WORK/M3-1_ResNet迁移学习_学生版.ipynb" 2>/dev/null
    cp $NBA/a3_m31_teacher "$WORK/M3-1_ResNet迁移学习_教师版.ipynb" 2>/dev/null
    cp $NBA/a3_m32_student "$WORK/M3-2_YOLO实时缺陷检测_学生版.ipynb" 2>/dev/null
    cp $NBA/a3_m32_teacher "$WORK/M3-2_YOLO实时缺陷检测_教师版.ipynb" 2>/dev/null
    [ -f $NBA/fw_m31 ] && cp $NBA/fw_m31 "$WORK/student_code_framework/w7_transfer_starter.py" 2>/dev/null
    [ -f $NBA/fw_m32 ] && cp $NBA/fw_m32 "$WORK/student_code_framework/w8_detect_starter.py" 2>/dev/null
    ;;
  Lecture-A4|lecture-a4|stu_a4_*|stu-a4-*|teacher_a4_*)
    cp $NBA/a4_m41_student "$WORK/M4-1_LLM故障诊断_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m41_teacher "$WORK/M4-1_LLM故障诊断_教师版.ipynb" 2>/dev/null
    cp $NBA/a4_m42_student "$WORK/M4-2_RAG知识库问答_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m42_teacher "$WORK/M4-2_RAG知识库问答_教师版.ipynb" 2>/dev/null
    cp $NBA/a4_m43_student "$WORK/M5-1_多智能体检修调度_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m43_teacher "$WORK/M5-1_多智能体检修调度_教师版.ipynb" 2>/dev/null
    cp $NBA/a4_m44_student "$WORK/Z_综合项目答辩_学生版.ipynb" 2>/dev/null
    cp $NBA/a4_m44_teacher "$WORK/Z_综合项目答辩_教师版.ipynb" 2>/dev/null
    [ -f $NBA/fw_m41 ] && cp $NBA/fw_m41 "$WORK/student_code_framework/w9_prompt_starter.py" 2>/dev/null
    [ -f $NBA/fw_m42 ] && cp $NBA/fw_m42 "$WORK/student_code_framework/w10_rag_starter.py" 2>/dev/null
    [ -f $NBA/fw_m43 ] && cp $NBA/fw_m43 "$WORK/student_code_framework/w11_multiagent_starter.py" 2>/dev/null
    [ -f $NBA/fw_m44 ] && cp $NBA/fw_m44 "$WORK/student_code_framework/w12_defense_starter.py" 2>/dev/null
    ;;


  # ===== P/B 系列直接分发（stu_ 前缀学生账户）=====
  Lecture-P1|lecture-p1|stu_p1_*|stu-p1-*|teacher_p1_*)
    for f in $NBP/p1_p*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBP/p1_p*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBP/fw_p1[0-9]*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-P2|lecture-p2|stu_p2_*|stu-p2-*|teacher_p2_*)
    for f in $NBP/p2_p*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBP/p2_p*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBP/fw_p2[0-9]*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-P3|lecture-p3|stu_p3_*|stu-p3-*|teacher_p3_*)
    for f in $NBP/p3_p*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBP/p3_p*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBP/fw_p3[0-9]*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-P4|lecture-p4|stu_p4_*|stu-p4-*|teacher_p4_*)
    for f in $NBP/p4_p*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBP/p4_p*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBP/fw_p4[0-9]*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-P5|lecture-p5|stu_p5_*|stu-p5-*|teacher_p5_*)
    for f in $NBP/p5_p*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBP/p5_p*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBP/fw_p5[0-9]*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-P6|lecture-p6|stu_p6_*|stu-p6-*|teacher_p6_*)
    for f in $NBP/p6_p*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBP/p6_p*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBP/fw_p6[0-9]*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B1|lecture-b1|stu_b1_*|stu-b1-*|teacher_b1_*)
    for f in $NBB/b1_w*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBB/b1_w*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBB/fw_w01 $NBB/fw_w02; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B2|lecture-b2|stu_b2_*|stu-b2-*|teacher_b2_*)
    for f in $NBB/b2_w*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBB/b2_w*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBB/fw_w03 $NBB/fw_w04; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B3|lecture-b3|stu_b3_*|stu-b3-*|teacher_b3_*)
    for f in $NBB/b3_w*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBB/b3_w*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBB/fw_w05 $NBB/fw_w06; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B4|lecture-b4|stu_b4_*|stu-b4-*|teacher_b4_*)
    for f in $NBB/b4_w*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBB/b4_w*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBB/fw_w07 $NBB/fw_w08; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B5|lecture-b5|stu_b5_*|stu-b5-*|teacher_b5_*)
    for f in $NBB/b5_w*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBB/b5_w*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBB/fw_w09 $NBB/fw_w10; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  Lecture-B6|lecture-b6|stu_b6_*|stu-b6-*|teacher_b6_*)
    for f in $NBB/b6_w*_student; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_student$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBB/b6_w*_teacher; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed s/_teacher$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBB/fw_w11 $NBB/fw_w12; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  # ===== industrial language students (java/go/rust/python) =====
  student-java)
    [ -d "$NBI" ] && for f in $NBI/*java*; do [ -f "$f" ] && cp "$f" "$WORK/"; done 2>/dev/null
    [ -d "$NBI" ] && for f in $NBI/fw_*java*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f | sed 's/^fw_//;s/$/.py/')"; done 2>/dev/null
    ;;
  student-go)
    [ -d "$NBI" ] && for f in $NBI/*go*; do [ -f "$f" ] && cp "$f" "$WORK/"; done 2>/dev/null
    [ -d "$NBI" ] && for f in $NBI/fw_*go*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f | sed 's/^fw_//;s/$/.py/')"; done 2>/dev/null
    ;;
  student-rust)
    [ -d "$NBI" ] && for f in $NBI/*rust*; do [ -f "$f" ] && cp "$f" "$WORK/"; done 2>/dev/null
    [ -d "$NBI" ] && for f in $NBI/fw_*rust*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f | sed 's/^fw_//;s/$/.py/')"; done 2>/dev/null
    ;;
  student-python)
    [ -d "$NBI" ] && for f in $NBI/*python*; do [ -f "$f" ] && cp "$f" "$WORK/"; done 2>/dev/null
    [ -d "$NBI" ] && for f in $NBI/fw_*python*; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f | sed 's/^fw_//;s/$/.py/')"; done 2>/dev/null
    ;;
  # ===== 32-Lecture 扩展段（A5~A12 / B7~B12 / P7~P8）=====
  # 内容已入库 cm-course-a/b/p（a5_m51~a12_z2 / b7_w13~b12_w18 / p7_p77~p8_p88），glob 驱动分发：
  # 后续教研侧新增 key（如 a12_m82_*）只要命名符合 <lecture>_<id>_student/_teacher 即自动生效，无需改脚本
  stu_a[5-9]_*|stu_a1[0-2]_*|teacher_a[5-9]_*|teacher_a1[0-2]_*|Lecture-A5|Lecture-A6|Lecture-A7|Lecture-A8|Lecture-A9|Lecture-A10|Lecture-A11|Lecture-A12|lecture-a5|lecture-a6|lecture-a7|lecture-a8|lecture-a9|lecture-a10|lecture-a11|lecture-a12)
    LEC=$(echo "$USERNAME" | sed -n "s/.*[aA]\([0-9]\+\).*/\1/p")
    for f in $NBA/a${LEC}_*_student $NBA/a${LEC}_*_student.json; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed -e s/_student$// -e s/\.json$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBA/a${LEC}_*_teacher $NBA/a${LEC}_*_teacher.json; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed -e s/_teacher$// -e s/\.json$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBA/fw_m[5-8]* $NBA/fw_z2; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  stu_b[7-9]_*|stu_b1[0-2]_*|teacher_b[7-9]_*|teacher_b1[0-2]_*|Lecture-B7|Lecture-B8|Lecture-B9|Lecture-B10|Lecture-B11|Lecture-B12|lecture-b7|lecture-b8|lecture-b9|lecture-b10|lecture-b11|lecture-b12)
    LEC=$(echo "$USERNAME" | sed -n "s/.*[bB]\([0-9]\+\).*/\1/p")
    for f in $NBB/b${LEC}_w*_student $NBB/b${LEC}_w*_student.json; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed -e s/_student$// -e s/\.json$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBB/b${LEC}_w*_teacher $NBB/b${LEC}_w*_teacher.json; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed -e s/_teacher$// -e s/\.json$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBB/fw_w1[3-8]; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;
  stu_p[78]_*|teacher_p[78]_*|Lecture-P7|Lecture-P8|lecture-p7|lecture-p8)
    LEC=$(echo "$USERNAME" | sed -n "s/.*[pP]\([0-9]\+\).*/\1/p")
    for f in $NBP/p${LEC}_p*_student $NBP/p${LEC}_p*_student.json; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed -e s/_student$// -e s/\.json$//)_学生版.ipynb"; done 2>/dev/null
    for f in $NBP/p${LEC}_p*_teacher $NBP/p${LEC}_p*_teacher.json; do [ -f "$f" ] && cp "$f" "$WORK/$(basename $f | sed -e s/_teacher$// -e s/\.json$//)_教师版.ipynb"; done 2>/dev/null
    for f in $NBP/fw_p77 $NBP/fw_p88; do [ -f "$f" ] && cp "$f" "$WORK/student_code_framework/$(basename $f).py"; done 2>/dev/null
    ;;

esac

# ===== 4. Install dependencies (ALL users) =====
pip install --quiet pycodestyle 2>/dev/null
pip install --quiet nbgrader 2>/dev/null

# Setup nbgrader exchange directory (shared between users)
mkdir -p /srv/nbgrader/exchange 2>/dev/null
mkdir -p /home/jovyan/work/nbgrader 2>/dev/null

# Create nbgrader config for each user
case "$USERNAME" in
  admin|teacher-zhang|teacher-*|teacher_*|Lecture-*|lecture-*)
    # Teachers/admin: full nbgrader config (create/assign/grade)
    mkdir -p /home/jovyan/work/nbgrader
    cat > /home/jovyan/work/nbgrader/nbgrader_config.py << 'NBGC'
import os
c = get_config()
c.Exchange.exchange_dir = '/srv/nbgrader/exchange'
c.Exchange.cache_dir = '/srv/nbgrader/cache'
c.CourseDirectory.course_id = 'default'
c.CourseDirectory.root = '/home/jovyan/work/nbgrader'
c.CourseDirectory.autocreate = True
NBGC
    ;;
  *)
    # Students: simple config (submit only)
    mkdir -p /home/jovyan/work/nbgrader
    cat > /home/jovyan/work/nbgrader/nbgrader_config.py << 'NBGC'
import os
c = get_config()
c.Exchange.exchange_dir = '/srv/nbgrader/exchange'
c.Exchange.cache_dir = '/srv/nbgrader/cache'
c.CourseDirectory.course_id = 'default'
c.CourseDirectory.root = '/home/jovyan/work/nbgrader'
c.CourseDirectory.autocreate = True
NBGC
    ;;
esac 2>/dev/null

# ===== 5. Summary =====
NB_COUNT=$(ls $WORK/*.ipynb 2>/dev/null | wc -l)
FW_COUNT=$(ls $WORK/student_code_framework/*.py 2>/dev/null | wc -l)
echo "Startup complete: $USERNAME"
echo "  Guides: dual-for-teachers | Grader: yes | Notebooks: $NB_COUNT | Code: $FW_COUNT"

# ===== 6. PrairieLearn Autograder Integration =====
if [ -d /tmp/autograder ]; then
    cp /tmp/autograder/README.md $WORK/AUTOGRADER-GUIDE.md 2>/dev/null
fi

# Write autograder helper script
cat > $WORK/submit_grade.py << 'PYEND'
import requests, sys, os, json
AUTOGRADER_URL = "http://10.167.2.175:30093"
API_KEY = "pl-student-2026"
def submit_code(code_file, test_file=None, language="python", assignment_id="ps1", course_id="python-industrial"):
    code = open(code_file).read()
    tests = open(test_file).read() if test_file else ""
    resp = requests.post(f"{AUTOGRADER_URL}/api/grade", headers={"X-API-Key": API_KEY, "Content-Type": "application/json"}, json={"code": code, "language": language, "tests": tests, "assignment_id": assignment_id, "course_id": course_id, "student_name": os.environ.get("JUPYTERHUB_USER", "anonymous")}, verify=False)
    return resp.json()
def check_my_scores(student_name=None):
    if not student_name:
        student_name = os.environ.get("JUPYTERHUB_USER", "anonymous")
    resp = requests.get(f"{AUTOGRADER_URL}/api/student/{student_name}/scores", headers={"X-API-Key": API_KEY}, verify=False)
    return resp.json()
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 submit_grade.py <code_file> [test_file] [assignment_id]")
        sys.exit(1)
    result = submit_code(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None, assignment_id=sys.argv[3] if len(sys.argv) > 3 else "ps1")
    print(f"Score: {result.get('score', 0)}/{result.get('max_score', 100)}")
    print(f"Feedback: {result.get('feedback', '')}")
    print(f"Tests: {result.get('tests', {}).get('passed', 0)}/{result.get('tests', {}).get('total', 0)} passed")
    print(f"Lint errors: {result.get('lint', {}).get('errors', 0)}")
PYEND
chmod +x $WORK/submit_grade.py 2>/dev/null
echo "  Autograder: integrated (submit_grade.py ready)"
