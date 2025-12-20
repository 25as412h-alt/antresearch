"""
調査イベントモデル
"""
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from datetime import date

logger = logging.getLogger(__name__)


class SurveyEvent:
    """調査イベントモデルクラス"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def create(self, survey_site_id: int, survey_site: str, survey_date: date,
               surveyor_name: Optional[str] = None, weather: Optional[str] = None,
               temperature: Optional[float] = None, remarks: Optional[str] = None) -> Optional[int]:
        """新規調査イベントを作成"""
        try:
            cursor = self.conn.cursor()
            
            # 日付をYYYY-MM-DD形式の文字列に変換
            date_str = survey_date.strftime('%Y-%m-%d') if isinstance(survey_date, date) else survey_date
            
            cursor.execute("""
                INSERT INTO survey_events 
                (survey_site_id, survey_site, survey_date, surveyor_name, weather, temperature, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (survey_site_id, survey_site, date_str, surveyor_name, weather, temperature, remarks))
            
            self.conn.commit()
            event_id = cursor.lastrowid
            
            logger.info(f"Survey event created: Site={survey_site}, Date={date_str} (ID: {event_id})")
            return event_id
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            if "UNIQUE constraint" in str(e):
                logger.error(f"Survey event already exists: Site={survey_site_id}, Date={date_str}")
            elif "FOREIGN KEY constraint" in str(e):
                logger.error(f"Survey site not found: {survey_site_id}")
            else:
                logger.error(f"Integrity error: {e}")
            return None
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to create survey event: {e}")
            return None
    
    def get_by_id(self, event_id: int, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """IDで調査イベントを取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT se.*, ss.name as survey_site_name, ps.name as parent_site_name
                FROM survey_events se
                LEFT JOIN survey_sites ss ON se.survey_site_id = ss.id
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
                WHERE se.id = ?
            """
            
            if not include_deleted:
                query += " AND se.deleted_at IS NULL"
            
            cursor.execute(query, (event_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get survey event by ID: {e}")
            return None
    
    def get_by_site(self, survey_site_id: int, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """調査地IDで調査イベントを取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT se.*, ss.name as survey_site_name, ps.name as parent_site_name
                FROM survey_events se
                LEFT JOIN survey_sites ss ON se.survey_site_id = ss.id
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
                WHERE se.survey_site_id = ?
            """
            
            if not include_deleted:
                query += " AND se.deleted_at IS NULL"
            
            query += " ORDER BY se.survey_date DESC"
            
            cursor.execute(query, (survey_site_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get survey events by site: {e}")
            return []
    
    def get_all(self, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """全ての調査イベントを取得"""
        try:
            cursor = self.conn.cursor()
            
            query = """
                SELECT se.*, ss.name as survey_site_name, ps.name as parent_site_name
                FROM survey_events se
                LEFT JOIN survey_sites ss ON se.survey_site_id = ss.id
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
            """
            
            if not include_deleted:
                query += " WHERE se.deleted_at IS NULL"
            
            query += " ORDER BY se.survey_date DESC, ss.name"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get all survey events: {e}")
            return []
    
    def update(self, event_id: int, **kwargs) -> bool:
        """調査イベントを更新"""
        try:
            allowed_fields = ['survey_site_id', 'survey_site', 'survey_date', 
                            'surveyor_name', 'weather', 'temperature', 'remarks']
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                logger.warning("No valid fields to update")
                return False
            
            # 日付の変換
            if 'survey_date' in update_fields and isinstance(update_fields['survey_date'], date):
                update_fields['survey_date'] = update_fields['survey_date'].strftime('%Y-%m-%d')
            
            set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            values = list(update_fields.values()) + [event_id]
            
            cursor = self.conn.cursor()
            cursor.execute(f"""
                UPDATE survey_events 
                SET {set_clause}
                WHERE id = ? AND deleted_at IS NULL
            """, values)
            
            if cursor.rowcount == 0:
                logger.warning(f"Survey event not found or already deleted: {event_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Survey event updated: ID {event_id}")
            return True
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            logger.error(f"Update failed due to integrity constraint: {e}")
            return False
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update survey event: {e}")
            return False
    
    def delete(self, event_id: int, logical: bool = True) -> bool:
        """調査イベントを削除"""
        try:
            cursor = self.conn.cursor()
            
            if logical:
                cursor.execute("""
                    UPDATE survey_events 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE id = ? AND deleted_at IS NULL
                """, (event_id,))
            else:
                cursor.execute("DELETE FROM survey_events WHERE id = ?", (event_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Survey event not found or already deleted: {event_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Survey event deleted: ID {event_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to delete survey event: {e}")
            return False
    
    def restore(self, event_id: int) -> bool:
        """論理削除された調査イベントを復元"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE survey_events 
                SET deleted_at = NULL 
                WHERE id = ? AND deleted_at IS NOT NULL
            """, (event_id,))
            
            if cursor.rowcount == 0:
                logger.warning(f"Survey event not found or not deleted: {event_id}")
                return False
            
            self.conn.commit()
            logger.info(f"Survey event restored: ID {event_id}")
            return True
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to restore survey event: {e}")
            return False