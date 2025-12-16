"""
親調査地モデル
"""
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ParentSite:
    """親調査地モデルクラス"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def create(self, name: str, latitude: float, longitude: float,
               altitude: Optional[float] = None, area: Optional[float] = None,
               remarks: Optional[str] = None) -> Optional[int]:
        """新規親調査地を作成"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO parent_sites (name, latitude, longitude, altitude, area, remarks)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, latitude, longitude, altitude, area, remarks))
            
            self.conn.commit()
            site_id = cursor.lastrowid
            
            # 変更履歴を記録
            self._log_change(site_id, 'INSERT')
            
            logger.info(f"Parent site created: {name} (ID: {site_id})")
            return site_id
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint" in str(e):
                logger.error(f"Parent site name already exists: {name}")
            else:
                logger.error(f"Integrity error: {e}")
            return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create parent site: {e}")
            return None
    
    def get_by_id(self, site_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """IDで親調査地を取得"""
        try:
            cursor = self.conn.cursor()
            
            if include_deleted:
                cursor.execute("SELECT * FROM parent_sites WHERE id = ?", (site_id,))
            else:
                cursor.execute("SELECT * FROM parent_sites WHERE id = ? AND deleted_at IS NULL", (site_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get parent site by ID: {e}")
            return None
    
    def get_by_name(self, name: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """名前で親調査地を取得"""
        try:
            cursor = self.conn.cursor()
            
            if include_deleted:
                cursor.execute("SELECT * FROM parent_sites WHERE name = ?", (name,))
            else:
                cursor.execute("SELECT * FROM parent_sites WHERE name = ? AND deleted_at IS NULL", (name,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get parent site by name: {e}")
            return None
    
    def get_all(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """全ての親調査地を取得"""
        try:
            cursor = self.conn.cursor()
            
            if include_deleted:
                cursor.execute("SELECT * FROM parent_sites ORDER BY name")
            else:
                cursor.execute("SELECT * FROM parent_sites WHERE deleted_at IS NULL ORDER BY name")
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get all parent sites: {e}")
            return []
    
    def update(self, site_id: int, **kwargs) -> bool:
        """親調査地を更新"""
        try:
            # 更新可能なフィールド
            allowed_fields = ['name', 'latitude', 'longitude', 'altitude', 'area', 'remarks']
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return False
            
            # SET句を構築
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(update_fields.values()) + [site_id]
            
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE parent_sites 
                SET {set_clause}
                WHERE id = ? AND deleted_at IS NULL
            """, values)
            
            if cursor.rowcount == 0:
                logger.warning(f"Parent site not found or already deleted: {site_id}")
                return False
            
            self.conn.commit()
            
            # 変更履歴を記録
            self._log_change(site_id, 'UPDATE', update_fields)
            
            logger.info(f"Parent site updated: ID {site_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Update failed due to integrity constraint: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update parent site: {e}")
            return False
    
    def delete(self, site_id: int, logical: bool = True) -> bool:
        """親調査地を削除（デフォルトは論理削除）"""
        try:
            cursor = self.conn.cursor()
            
            if logical:
                # 論理削除
                cursor.execute("""
                    UPDATE parent_sites 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND deleted_at IS NULL
                """, (site_id,))
            else:
                # 物理削除（関連する調査地がないことを確認）
                cursor.execute("""
                    SELECT COUNT(*) FROM survey_sites 
                    WHERE parent_site_id = ? AND deleted_at IS NULL
                """, (site_id,))
                
                if cursor.fetchone()[0] > 0:
                    logger.error(f"Cannot delete parent site {site_id}: has active survey sites")
                    return False
                
                cursor.execute("DELETE FROM parent_sites WHERE id = ?", (site_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Parent site not found or already deleted: {site_id}")
                return False
            
            self.conn.commit()
            
            # 変更履歴を記録
            self._log_change(site_id, 'DELETE')
            
            logger.info(f"Parent site {'logically' if logical else 'physically'} deleted: ID {site_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Delete failed due to foreign key constraint: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete parent site: {e}")
            return False
    
    def restore(self, site_id: int) -> bool:
        """論理削除された親調査地を復元"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE parent_sites 
                SET deleted_at = NULL 
                WHERE id = ? AND deleted_at IS NOT NULL
            """, (site_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Parent site not found or not deleted: {site_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Parent site restored: ID {site_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to restore parent site: {e}")
            return False
    
    def _log_change(self, site_id: int, action: str, changed_fields: Optional[Dict] = None):
        """変更履歴を記録"""
        try:
            import json
            cursor = self.conn.cursor()
            
            fields_json = json.dumps(changed_fields, ensure_ascii=False) if changed_fields else None
            
            cursor.execute("""
                INSERT INTO change_logs (table_name, record_id, action, changed_fields)
                VALUES (?, ?, ?, ?)
            """, ('parent_sites', site_id, action, fields_json))
            
        except Exception as e:
            logger.error(f"Failed to log change: {e}")