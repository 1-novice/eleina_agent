"""医疗RAG专用API路由"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel

from src.rag.medical_knowledge_manager import medical_knowledge_manager
from src.rag.medical_retriever import medical_retriever
from src.rag.medical_response_generator import medical_response_generator

router = APIRouter(prefix="/medical")


class KnowledgeBaseRequest(BaseModel):
    """添加知识库请求"""
    domain: str
    name: str
    description: str
    vector_store_path: str = ""
    document_paths: List[str] = []


class QueryRequest(BaseModel):
    """医疗查询请求"""
    query: str
    top_k: int = 5


class KnowledgeBaseInfo(BaseModel):
    """知识库信息"""
    domain: str
    name: str
    description: str
    activated: bool


class MedicalResponse(BaseModel):
    """医疗回答响应"""
    answer: str
    sources: List[Dict[str, str]]
    has_knowledge: bool
    domain: str


@router.post("/knowledge_base")
async def add_knowledge_base(request: KnowledgeBaseRequest):
    """添加医疗知识库"""
    try:
        result = medical_knowledge_manager.add_knowledge_base(
            domain=request.domain,
            name=request.name,
            description=request.description,
            vector_store_path=request.vector_store_path,
            document_paths=request.document_paths
        )
        if result:
            return {"status": "success", "message": f"知识库 {request.domain} 添加成功"}
        else:
            raise HTTPException(status_code=400, detail=f"知识库 {request.domain} 已存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge_base/{domain}")
async def remove_knowledge_base(domain: str):
    """删除医疗知识库"""
    try:
        result = medical_knowledge_manager.remove_knowledge_base(domain)
        if result:
            return {"status": "success", "message": f"知识库 {domain} 删除成功"}
        else:
            raise HTTPException(status_code=404, detail=f"知识库 {domain} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge_base/{domain}/activate")
async def activate_knowledge_base(domain: str):
    """激活医疗知识库"""
    try:
        result = medical_knowledge_manager.activate_domain(domain)
        if result:
            kb = medical_knowledge_manager.get_knowledge_base(domain)
            return {"status": "success", "message": f"已激活知识库: {kb.name}", "domain": domain}
        else:
            raise HTTPException(status_code=404, detail=f"知识库 {domain} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge_base/deactivate")
async def deactivate_knowledge_base():
    """取消激活医疗知识库"""
    try:
        result = medical_knowledge_manager.deactivate_domain()
        if result:
            return {"status": "success", "message": "已取消激活所有医疗知识库"}
        else:
            raise HTTPException(status_code=400, detail="没有激活的知识库")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge_base/active")
async def get_active_knowledge_base():
    """获取当前激活的知识库"""
    try:
        kb = medical_knowledge_manager.get_active_knowledge_base()
        if kb:
            return {
                "domain": kb.domain,
                "name": kb.name,
                "description": kb.description,
                "activated": kb.activated
            }
        else:
            return {"status": "no_active", "message": "没有激活的医疗知识库"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge_bases")
async def get_all_knowledge_bases():
    """获取所有医疗知识库"""
    try:
        domains = medical_knowledge_manager.get_all_domains()
        kb_list = []
        for domain in domains:
            kb = medical_knowledge_manager.get_knowledge_base(domain)
            if kb:
                kb_list.append({
                    "domain": kb.domain,
                    "name": kb.name,
                    "description": kb.description,
                    "activated": kb.activated
                })
        return {"knowledge_bases": kb_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=MedicalResponse)
async def query_medical_knowledge(request: QueryRequest):
    """直接查询医疗知识库"""
    try:
        # 检查是否有激活的知识库
        active_kb = medical_knowledge_manager.get_active_knowledge_base()
        if not active_kb:
            raise HTTPException(status_code=400, detail="请先激活一个医疗知识库")
        
        # 执行检索
        retrieved_docs = medical_retriever.retrieve(request.query, k=request.top_k)
        
        # 生成回答
        response = medical_response_generator.generate_response(
            query=request.query,
            retrieved_docs=retrieved_docs,
            domain_name=active_kb.name
        )
        
        return MedicalResponse(
            answer=response["answer"],
            sources=response["sources"],
            has_knowledge=response["has_knowledge"],
            domain=active_kb.name
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_medical_rag_stats():
    """获取医疗RAG统计信息"""
    try:
        collection_size = medical_retriever.get_collection_size()
        collection_exists = medical_retriever.check_collection_exists()
        active_kb = medical_knowledge_manager.get_active_knowledge_base()
        
        return {
            "collection_exists": collection_exists,
            "document_count": collection_size,
            "active_knowledge_base": active_kb.name if active_kb else None,
            "total_knowledge_bases": len(medical_knowledge_manager.get_all_domains())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))