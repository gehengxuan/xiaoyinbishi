"""Local lexical retrieval and conservative, metadata-assisted discrepancy checks."""

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


def normalized(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def terms(text: str) -> set[str]:
    text = normalized(text)
    tokens = set(re.findall(r"[a-z0-9_]+", text))
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        tokens.update(run[i:i + 2] for i in range(len(run) - 1))
    return tokens


class KnowledgeBase:
    def __init__(self, path: Path, synonyms_path: Path | None = None):
        self.path = Path(path)
        raw = self.path.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        value = json.loads(raw)
        if not isinstance(value, dict) or not isinstance(value.get("documents"), list):
            raise ValueError("知识库必须包含 documents 数组。")
        self.version = value.get("corpus_version", "unspecified")
        self.documents: dict[str, dict[str, Any]] = {}
        for doc in value["documents"]:
            self._validate_document(doc)
            if doc["document_id"] in self.documents:
                raise ValueError("文档 ID 重复。")
            self.documents[doc["document_id"]] = doc
        self.synonyms = []
        if synonyms_path is not None:
            self.synonyms = json.loads(Path(synonyms_path).read_text(encoding="utf-8"))
            if not isinstance(self.synonyms, list) or any(
                not isinstance(group, list)
                or not group
                or any(not isinstance(word, str) or not word for word in group)
                for group in self.synonyms
            ):
                raise ValueError("同义词必须是非空字符串数组的数组。")

    @staticmethod
    def _validate_document(doc: Any) -> None:
        if not isinstance(doc, dict):
            raise ValueError("文档必须是对象。")
        for key in ("document_id", "title", "version_date", "scope"):
            if not isinstance(doc.get(key), str) or not doc[key].strip():
                raise ValueError(f"文档缺少有效字段：{key}")
        date.fromisoformat(doc["version_date"])
        if not isinstance(doc.get("keywords"), list) or any(
            not isinstance(word, str) for word in doc["keywords"]
        ):
            raise ValueError("keywords 必须是字符串数组。")
        chunks = doc.get("chunks")
        if not isinstance(chunks, list) or not chunks:
            raise ValueError("每个文档至少需要一个片段。")
        seen = set()
        for chunk in chunks:
            if not isinstance(chunk, dict) or any(
                not isinstance(chunk.get(key), str) or not chunk[key].strip()
                for key in ("chunk_id", "policy_key", "text")
            ):
                raise ValueError("片段需要 chunk_id、policy_key、text。")
            if chunk["chunk_id"] in seen:
                raise ValueError("同一文档内片段 ID 重复。")
            seen.add(chunk["chunk_id"])

    def related_ids(self, document_id: str) -> list[str]:
        doc = self.documents[document_id]
        keys = {chunk["policy_key"] for chunk in doc["chunks"]}
        return sorted(
            other["document_id"]
            for other in self.documents.values()
            if other["scope"] == doc["scope"]
            and any(chunk["policy_key"] in keys for chunk in other["chunks"])
        )

    def metadata(self, document_id: str) -> dict[str, Any]:
        doc = self.documents[document_id]
        return {
            key: doc[key]
            for key in ("document_id", "title", "version_date", "scope")
        } | {
            "chunk_ids": [chunk["chunk_id"] for chunk in doc["chunks"]],
            "related_document_ids": self.related_ids(document_id),
        }

    def search(self, query: str, limit: int) -> dict[str, Any]:
        query_normalized = normalized(query)
        expanded = query
        for group in self.synonyms:
            if any(normalized(word) in query_normalized for word in group):
                expanded += " " + " ".join(group)
        query_terms = terms(expanded)
        ranked = []
        for doc in self.documents.values():
            heading_terms = terms(doc["title"] + " " + " ".join(doc["keywords"]))
            body_terms = terms(" ".join(chunk["text"] for chunk in doc["chunks"]))
            score = 3 * len(query_terms & heading_terms) + len(query_terms & body_terms)
            # A single generic body match (e.g. 公司) is too weak to be a hit.
            if score >= 3:
                ranked.append((score, doc["document_id"]))
        ranked.sort(key=lambda pair: (-pair[0], pair[1]))
        return {
            "ok": True,
            "query": query,
            "expanded_query": expanded,
            "total": len(ranked),
            "has_more": len(ranked) > limit,
            "hits": [self.metadata(doc_id) | {"score": score} for score, doc_id in ranked[:limit]],
            "note": "命中仅为线索；必须读取原文。版本日期不代表优先级。",
        }

    def read(self, document_id: str) -> dict[str, Any]:
        if document_id not in self.documents:
            return {"ok": False, "error": {"code": "DOCUMENT_NOT_FOUND", "message": "文档不存在。", "retryable": False}}
        return {"ok": True, **self.metadata(document_id), "chunks": self.documents[document_id]["chunks"]}

    def conflicts(self, document_ids: set[str], policy_keys: set[str]) -> list[dict]:
        groups: dict[tuple[str, str], list[dict]] = {}
        for doc_id in sorted(document_ids):
            doc = self.documents[doc_id]
            for chunk in doc["chunks"]:
                if chunk["policy_key"] in policy_keys:
                    groups.setdefault((chunk["policy_key"], doc["scope"]), []).append({
                        "document_id": doc_id,
                        "version_date": doc["version_date"],
                        "chunk_id": chunk["chunk_id"],
                        "quote": chunk["text"],
                    })
        return [
            {"policy_key": key, "scope": scope, "variants": variants}
            for (key, scope), variants in groups.items()
            if len({normalized(item["quote"]) for item in variants}) > 1
        ]
