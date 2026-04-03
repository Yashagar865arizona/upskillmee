"""
Service for managing database operations, backups, and data exports.
"""

import os
import logging
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import pandas as pd
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models.user import User
from ..models.chat import Message

logger = logging.getLogger(__name__)

class DataManagementService:
    def __init__(self):
        self.backup_dir = Path(settings.DATABASE_BACKUP_DIR)
        self.analytics_dir = Path(settings.ANALYTICS_EXPORT_DIR)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.analytics_dir.mkdir(parents=True, exist_ok=True)

    async def backup_database(self) -> str:
        """Create a backup of the current database."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"ponder_backup_{timestamp}.sql"
            
            if "postgresql" in settings.DATABASE_URL:
                # Extract database connection details from URL
                db_url = settings.DATABASE_URL
                if db_url.startswith("postgresql://"):
                    db_url = db_url[len("postgresql://"):]
                
                user_pass, rest = db_url.split("@", 1) if "@" in db_url else ("", db_url)
                host_db = rest.split("/", 1) if "/" in rest else (rest, "")
                
                if "/" in host_db[1]:
                    dbname = host_db[1].split("/")[0]
                else:
                    dbname = host_db[1]
                
                # Use pg_dump for PostgreSQL
                backup_command = f"pg_dump -d {settings.DATABASE_URL} -f {backup_path}"
                result = os.system(backup_command)
                
                if result != 0:
                    raise Exception(f"pg_dump failed with exit code {result}")
            
            # Clean old backups
            self._cleanup_old_backups()
            
            logger.info(f"Database backed up to {backup_path}")
            return str(backup_path)
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            # Don't raise the error for backup failure
            return ""

    def _cleanup_old_backups(self):
        """Remove old backups based on retention policy."""
        try:
            backups = sorted(self.backup_dir.glob("ponder_backup_*.sql"))
            
            # Remove old backups beyond max count
            while len(backups) > settings.MAX_BACKUP_COUNT:
                oldest = backups.pop(0)
                oldest.unlink()
                logger.info(f"Removed old backup: {oldest}")
            
            # Remove backups older than retention period
            retention_date = datetime.now() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
            for backup in backups:
                if datetime.fromtimestamp(backup.stat().st_mtime) < retention_date:
                    backup.unlink()
                    logger.info(f"Removed expired backup: {backup}")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    async def reset_database(self, db: AsyncSession):
        """Reset the database in development environment."""
        if not settings.is_development:
            raise ValueError("Database reset is only allowed in development environment")
        
        try:
            # Create backup before reset
            backup_path = await self.backup_database()
            if backup_path:
                logger.info(f"Created backup at {backup_path}")
            
            # Drop all tables
            await db.execute(text("DROP TABLE IF EXISTS users CASCADE"))
            await db.execute(text("DROP TABLE IF EXISTS messages CASCADE"))
            await db.execute(text("DROP TABLE IF EXISTS conversations CASCADE"))
            await db.execute(text("DROP TABLE IF EXISTS user_profiles CASCADE"))
            await db.commit()
            
            # Recreate tables
            from ..database.base import Base
            from ..database.engine import engine
            Base.metadata.create_all(bind=engine)
            
            logger.info("Database reset completed")
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            await db.rollback()
            # Don't raise the error for reset failure in development
            if settings.is_development:
                logger.warning("Continuing despite reset failure in development")
            else:
                raise

    async def export_analytics(self, db: AsyncSession, start_date: Optional[datetime] = None):
        """Export analytics data for analysis."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export user data
            user_query = select(User)
            result = await db.execute(user_query)
            users_df = pd.DataFrame([dict(row) for row in result.fetchall()])
            users_df.to_csv(self.analytics_dir / f"users_{timestamp}.csv", index=False)
            
            # Export message data
            message_query = select(Message)
            result = await db.execute(message_query)
            messages_df = pd.DataFrame([dict(row) for row in result.fetchall()])
            messages_df.to_csv(self.analytics_dir / f"messages_{timestamp}.csv", index=False)
            
            # Export aggregated metrics
            metrics = {
                "total_users": len(users_df),
                "total_messages": len(messages_df),
                "avg_messages_per_user": len(messages_df) / len(users_df) if len(users_df) > 0 else 0,
                "export_date": timestamp
            }
            
            with open(self.analytics_dir / f"metrics_{timestamp}.json", "w") as f:
                json.dump(metrics, f, indent=2)
            
            logger.info(f"Analytics data exported to {self.analytics_dir}")
            return metrics
        
        except Exception as e:
            logger.error(f"Failed to export analytics: {e}")
            raise

    async def get_backup_list(self) -> List[dict]:
        """Get list of available backups."""
        try:
            backups = []
            for backup in sorted(self.backup_dir.glob("ponder_backup_*.sql")):
                stats = backup.stat()
                backups.append({
                    "filename": backup.name,
                    "size": stats.st_size,
                    "created_at": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "path": str(backup)
                })
            return backups
        except Exception as e:
            logger.error(f"Failed to get backup list: {e}")
            return []

    async def cleanup_old_data(self, db: AsyncSession, days: int = 30) -> Dict[str, int]:
        """Clean up old data while preserving important information."""
        if not settings.is_production:
            raise ValueError("Data cleanup should only be done in production")
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            stats = {
                "archived_messages": 0,
                "anonymized_users": 0
            }

            # Archive old messages to analytics storage
            result = await db.execute(
                text("SELECT * FROM messages WHERE created_at < :cutoff"),
                {"cutoff": cutoff_date}
            )
            old_messages = result.fetchall()
            
            # Export to analytics before deletion
            messages_df = pd.DataFrame([dict(row) for row in old_messages])
            if not messages_df.empty:
                archive_path = self.analytics_dir / f"archived_messages_{datetime.now().strftime('%Y%m%d')}.csv"
                messages_df.to_csv(archive_path, index=False)
                stats["archived_messages"] = len(messages_df)

            # Delete old messages but keep user data
            await db.execute(
                text("DELETE FROM messages WHERE created_at < :cutoff"),
                {"cutoff": cutoff_date}
            )

            # Anonymize inactive users but keep aggregated data
            result = await db.execute(
                text("""
                    UPDATE users 
                    SET name = 'Anonymous_' || id,
                        email = 'anonymous_' || id || '@example.com'
                    WHERE last_active < :cutoff
                    AND id NOT IN (
                        SELECT DISTINCT user_id 
                        FROM messages 
                        WHERE created_at >= :cutoff
                    )
                    RETURNING id
                """),
                {"cutoff": cutoff_date}
            )
            stats["anonymized_users"] = len(result.fetchall())

            await db.commit()
            logger.info(f"Cleanup completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to clean up old data: {e}")
            await db.rollback()
            raise

    async def get_system_stats(self, db: AsyncSession) -> Dict[str, Union[int, str, Dict[str, Any], None]]:
        """Get current system statistics."""
        try:
            stats = {
                "total_users": (await db.execute(text("SELECT COUNT(*) FROM users"))).scalar(),
                "active_users_24h": (await db.execute(
                    text("SELECT COUNT(DISTINCT user_id) FROM messages WHERE created_at > NOW() - INTERVAL '24 hours'")
                )).scalar(),
                "total_messages": (await db.execute(text("SELECT COUNT(*) FROM messages"))).scalar(),
                "database_size": await self._get_db_size(db),
                "backup_count": len(list(self.backup_dir.glob("ponder_backup_*.sql"))),
                "latest_backup": None
            }
            
            # Get latest backup info
            backups = await self.get_backup_list()
            if backups:
                stats["latest_backup"] = backups[-1]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            raise

    async def _get_db_size(self, db: AsyncSession) -> str:
        """Get database size in human readable format."""
        try:
            if "postgresql" in settings.DATABASE_URL:
                result = await db.execute(text(
                    "SELECT pg_size_pretty(pg_database_size(current_database()))"
                ))
                size = result.scalar()
                return str(size) if size is not None else "Unknown"
            elif "mysql" in settings.DATABASE_URL:
                result = await db.execute(text(
                    "SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) FROM information_schema.tables"
                ))
                size = result.scalar()
                return f"{str(size)} MB" if size is not None else "Unknown"
            else:
                # SQLite
                size = Path("app.db").stat().st_size
                return f"{size / (1024*1024):.2f} MB"
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return "Unknown"
