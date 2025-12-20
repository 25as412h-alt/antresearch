"""
種名マスタモデル
"""
import sqlite3
import logging
import re
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Species:
    """種名マスタモデルクラス"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def create(self, scientific_name: str, genus: Optional[str] = None,
               subfamily: Optional[str] = None, ja_name: Optional[str] = None,
               ja_genus: Optional[str] = None, ja_subfamily: Optional[str] = None,
               remarks: Optional[str] = None) -> Optional[int]:
        """新規種を作成"""
        try:
            # 学名形式のバリデーション（簡易版）
            if not self._validate_scientific_name(scientific_name):
                logger.error(f"Invalid scientific name format: {scientific_name}")
                return None
            
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO species_master 
                (scientific_name, genus, subfamily, ja_name, ja_genus, ja_subfamily, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (scientific_name, genus, subfamily, ja_name, ja_genus, ja_subfamily, remarks))
            
            self.conn.commit()
            species_id = cursor.lastrowid
            
            logger.info(f"Species created: {scientific_name} (ID: {species_id})")
            return species_id
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint" in str(e):
                logger.error(f"Species already exists: {scientific_name}")
            else:
                logger.error(f"Integrity error: {e}")
            return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create species: {e}")
            return None
    
    def _validate_scientific_name(self, name: str) -> bool:
        """学名形式のバリデーション"""
        # 基本形式: "Genus species" または "Genus species subspecies"
        pattern = r'^[A-Z][a-z]+\s[a-z]+(\s[a-z]+)?$'
        return bool(re.match(pattern, name.strip()))
    
    def get_by_id(self, species_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """IDで種を取得"""
        try:
            cursor = self.conn.cursor()
            
            if include_deleted:
                cursor.execute("SELECT * FROM species_master WHERE id = ?", (species_id,))
            else:
                cursor.execute("SELECT * FROM species_master WHERE id = ? AND deleted_at IS NULL", (species_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get species by ID: {e}")
            return None
    
    def get_by_scientific_name(self, scientific_name: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """学名で種を取得"""
        try:
            cursor = self.conn.cursor()
            
            if include_deleted:
                cursor.execute("SELECT * FROM species_master WHERE scientific_name = ?", (scientific_name,))
            else:
                cursor.execute("SELECT * FROM species_master WHERE scientific_name = ? AND deleted_at IS NULL", (scientific_name,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get species by scientific name: {e}")
            return None
    
    def get_all(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """全ての種を取得"""
        try:
            cursor = self.conn.cursor()
            
            if include_deleted:
                cursor.execute("SELECT * FROM species_master ORDER BY scientific_name")
            else:
                cursor.execute("SELECT * FROM species_master WHERE deleted_at IS NULL ORDER BY scientific_name")
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get all species: {e}")
            return []
    
    def search(self, keyword: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """キーワードで種を検索"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT * FROM species_master 
                WHERE (scientific_name LIKE ? OR ja_name LIKE ? OR genus LIKE ?)
            """
            
            if not include_deleted:
                query += " AND deleted_at IS NULL"
            
            query += " ORDER BY scientific_name"
            
            search_term = f"%{keyword}%"
            cursor.execute(query, (search_term, search_term, search_term))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to search species: {e}")
            return []
    
    def update(self, species_id: int, **kwargs) -> bool:
        """種を更新"""
        try:
            allowed_fields = ['scientific_name', 'genus', 'subfamily', 
                            'ja_name', 'ja_genus', 'ja_subfamily', 'remarks']
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return False
            
            # 学名を更新する場合はバリデーション
            if 'scientific_name' in update_fields:
                if not self._validate_scientific_name(update_fields['scientific_name']):
                    logger.error(f"Invalid scientific name format: {update_fields['scientific_name']}")
                    return False
            
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(update_fields.values()) + [species_id]
            
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE species_master 
                SET {set_clause}
                WHERE id = ? AND deleted_at IS NULL
            """, values)
            
            if cursor.rowcount == 0:
                logger.warning(f"Species not found or already deleted: {species_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Species updated: ID {species_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Update failed due to integrity constraint: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update species: {e}")
            return False
    
    def delete(self, species_id: int, logical: bool = True) -> bool:
        """種を削除"""
        try:
            cursor = self.conn.cursor()
            
            if logical:
                cursor.execute("""
                    UPDATE species_master 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND deleted_at IS NULL
                """, (species_id,))
            else:
                # 物理削除（アリ類記録がないことを確認）
                cursor.execute("""
                    SELECT COUNT(*) FROM ant_records 
                    WHERE species_id = ? AND deleted_at IS NULL
                """, (species_id,))
                
                if cursor.fetchone()[0] > 0:
                    logger.error(f"Cannot delete species {species_id}: has active ant records")
                    return False
                
                cursor.execute("DELETE FROM species_master WHERE id = ?", (species_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Species not found or already deleted: {species_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Species deleted: ID {species_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Delete failed due to foreign key constraint: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete species: {e}")
            return False
    
    def restore(self, species_id: int) -> bool:
        """論理削除された種を復元"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE species_master 
                SET deleted_at = NULL 
                WHERE id = ? AND deleted_at IS NOT NULL
            """, (species_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Species not found or not deleted: {species_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Species restored: ID {species_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to restore species: {e}")
            return False