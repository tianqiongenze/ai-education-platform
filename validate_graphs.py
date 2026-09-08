#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep validate each saved workflow graph via pydantic node entity classes."""
import json, sys, traceback
sys.path.insert(0, "/app/api")
from app_factory import create_app
_socketio_app, flask_app = create_app()
from extensions.ext_database import db
from models.workflow import Workflow
from graphon.nodes.start.entities import StartNodeData
from graphon.nodes.end.entities import EndNodeData
from graphon.nodes.llm.entities import LLMNodeData
from graphon.nodes.code.entities import CodeNodeData
from graphon.nodes.if_else.entities import IfElseNodeData
from graphon.nodes.answer.entities import AnswerNodeData
from core.workflow.nodes.knowledge_retrieval.entities import KnowledgeRetrievalNodeData

CMAP = {
    "start": StartNodeData, "end": EndNodeData, "llm": LLMNodeData,
    "code": CodeNodeData, "if-else": IfElseNodeData, "answer": AnswerNodeData,
    "knowledge-retrieval": KnowledgeRetrievalNodeData,
}

APPS = [
    ("cbd7fa71-d8d1-45b5-bdf7-2c56d575669e", "故障诊断工作流"),
    ("1471e523-fe83-41fe-a2a8-9d56e8800de1", "生产质量评估工作流"),
    ("2307bf62-6cd4-4599-a046-887c57e95387", "代码质量分析工作流"),
    ("4e63c4d7-baf7-41b1-b295-c4565f72877e", "工业互联网智能体"),
    ("15b2a9b9-2823-4d55-8c10-30ff760e7382", "预测性维护智能体"),
    ("2dd72f64-61b6-46e8-8841-8300df3d921a", "安全合规检查员"),
    ("6fe85559-7f51-4849-a3d3-3c596853864a", "生产线优化顾问"),
    ("9e8d3c60-d35c-4cc4-aec6-278e5214ef0b", "编程作业评审智能体"),
    ("e3291494-d3d8-4933-a852-eb605bc8bf83", "软件架构评审智能体"),
]

def main():
  for aid, name in APPS:
    print("\n=== %s ===" % name)
    try:
        wf = db.session.query(Workflow).filter(
            Workflow.app_id == aid, Workflow.version == Workflow.VERSION_DRAFT
        ).first()
        if not wf:
            print("  NO DRAFT WORKFLOW")
            continue
        graph = wf.graph_dict
        errors = []
        for node in graph.get("nodes", []):
            nd = node.get("data", {})
            ntype = nd.get("type")
            ec = CMAP.get(ntype)
            if ec:
                nd2 = dict(nd)
                nd2.setdefault("id", node.get("id"))
                try:
                    ec.model_validate(nd2)
                except Exception as ex:
                    errors.append("%s(%s): %s" % (node.get("id"), ntype, str(ex)[:400]))
            else:
                errors.append("%s: unknown type %s" % (node.get("id"), ntype))
        if errors:
            print("  VALIDATION ERRORS:")
            for e in errors:
                print("   -", e)
        else:
            print("  DEEP VALIDATION OK (%d nodes, %d edges)" % (
                len(graph.get("nodes", [])), len(graph.get("edges", []))))
    except Exception as ex:
        print("  EXCEPTION:", ex)
        traceback.print_exc()

with flask_app.app_context():
    main()

