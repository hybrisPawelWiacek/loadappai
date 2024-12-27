"""History tracking service implementation.

This module implements history tracking functionality.
It provides:
- Offer history tracking
- Change tracking
- Audit logging
- Analytics
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from uuid import UUID

from src.domain.entities.offer import Offer, OfferStatus
from src.domain.services.common.base import BaseService
from src.domain.value_objects import (
    HistoryEntry,
    ChangeRecord,
    AuditLog,
    Analytics
)

class HistoryTrackingService(BaseService):
    """Service for tracking history and changes.
    
    This service is responsible for:
    - Tracking offer history
    - Recording changes
    - Maintaining audit logs
    - Generating analytics
    """
    
    def __init__(
        self,
        repository: Optional['HistoryRepository'] = None,
        analytics_client: Optional['AnalyticsClient'] = None
    ):
        """Initialize history tracking service.
        
        Args:
            repository: Optional repository for history
            analytics_client: Optional client for analytics
        """
        super().__init__()
        self._repository = repository
        self._analytics_client = analytics_client
    
    def track_offer_history(
        self,
        offer: Offer,
        action: str,
        user: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> HistoryEntry:
        """Track offer history entry.
        
        Args:
            offer: Offer being tracked
            action: Action performed
            user: Optional user identifier
            metadata: Optional metadata
            
        Returns:
            Created history entry
            
        Raises:
            ValueError: If tracking fails
        """
        self._log_entry(
            "track_offer_history",
            offer=offer,
            action=action,
            user=user
        )
        
        try:
            # Create history entry
            entry = HistoryEntry(
                offer_id=offer.id,
                action=action,
                timestamp=datetime.utcnow(),
                user=user or "system",
                data=offer.dict(),
                metadata=metadata or {}
            )
            
            # Save to repository
            if self._repository:
                self._repository.save_history(entry)
            
            # Send to analytics
            if self._analytics_client:
                self._analytics_client.track_event(
                    "offer_action",
                    {
                        "offer_id": str(offer.id),
                        "action": action,
                        "user": entry.user,
                        "timestamp": entry.timestamp.isoformat()
                    }
                )
            
            self._log_exit("track_offer_history", entry)
            return entry
            
        except Exception as e:
            self._log_error("track_offer_history", e)
            raise ValueError(f"Failed to track history: {str(e)}")
    
    def get_offer_history(
        self,
        offer_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        actions: Optional[List[str]] = None
    ) -> List[HistoryEntry]:
        """Get offer history entries.
        
        Args:
            offer_id: Offer ID
            start_time: Optional start time
            end_time: Optional end time
            actions: Optional action filter
            
        Returns:
            List of history entries
            
        Raises:
            ValueError: If retrieval fails
        """
        self._log_entry(
            "get_offer_history",
            offer_id=offer_id,
            start_time=start_time,
            end_time=end_time
        )
        
        try:
            if not self._repository:
                return []
            
            # Get history entries
            entries = self._repository.get_history(
                offer_id,
                start_time,
                end_time,
                actions
            )
            
            self._log_exit("get_offer_history", entries)
            return entries
            
        except Exception as e:
            self._log_error("get_offer_history", e)
            raise ValueError(f"Failed to get history: {str(e)}")
    
    def track_changes(
        self,
        offer: Offer,
        changes: Dict[str, Tuple[any, any]],
        user: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ChangeRecord:
        """Track offer changes.
        
        Args:
            offer: Offer being changed
            changes: Dictionary of field changes
            user: Optional user identifier
            reason: Optional change reason
            
        Returns:
            Created change record
            
        Raises:
            ValueError: If tracking fails
        """
        self._log_entry(
            "track_changes",
            offer=offer,
            changes=changes,
            user=user
        )
        
        try:
            # Create change record
            record = ChangeRecord(
                offer_id=offer.id,
                timestamp=datetime.utcnow(),
                user=user or "system",
                reason=reason or "system update",
                changes={
                    field: {
                        "old": str(old),
                        "new": str(new)
                    }
                    for field, (old, new) in changes.items()
                }
            )
            
            # Save to repository
            if self._repository:
                self._repository.save_changes(record)
            
            # Send to analytics
            if self._analytics_client:
                self._analytics_client.track_event(
                    "offer_changed",
                    {
                        "offer_id": str(offer.id),
                        "user": record.user,
                        "timestamp": record.timestamp.isoformat(),
                        "fields": list(changes.keys())
                    }
                )
            
            self._log_exit("track_changes", record)
            return record
            
        except Exception as e:
            self._log_error("track_changes", e)
            raise ValueError(f"Failed to track changes: {str(e)}")
    
    def get_audit_log(
        self,
        offer_id: UUID,
        window: Optional[timedelta] = None
    ) -> AuditLog:
        """Get offer audit log.
        
        Args:
            offer_id: Offer ID
            window: Optional time window
            
        Returns:
            Audit log
            
        Raises:
            ValueError: If retrieval fails
        """
        self._log_entry(
            "get_audit_log",
            offer_id=offer_id,
            window=window
        )
        
        try:
            window = window or timedelta(days=30)
            end_time = datetime.utcnow()
            start_time = end_time - window
            
            if not self._repository:
                return AuditLog(
                    offer_id=offer_id,
                    entries=[],
                    start_time=start_time,
                    end_time=end_time
                )
            
            # Get history entries
            history = self.get_offer_history(
                offer_id,
                start_time,
                end_time
            )
            
            # Get change records
            changes = self._repository.get_changes(
                offer_id,
                start_time,
                end_time
            )
            
            # Create audit log
            log = AuditLog(
                offer_id=offer_id,
                entries=sorted(
                    history + changes,
                    key=lambda x: x.timestamp
                ),
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "history_count": len(history),
                    "change_count": len(changes)
                }
            )
            
            self._log_exit("get_audit_log", log)
            return log
            
        except Exception as e:
            self._log_error("get_audit_log", e)
            raise ValueError(f"Failed to get audit log: {str(e)}")
    
    def get_analytics(
        self,
        offer_id: UUID,
        metrics: Optional[List[str]] = None
    ) -> Analytics:
        """Get offer analytics.
        
        Args:
            offer_id: Offer ID
            metrics: Optional metrics to include
            
        Returns:
            Analytics data
            
        Raises:
            ValueError: If analysis fails
        """
        self._log_entry(
            "get_analytics",
            offer_id=offer_id,
            metrics=metrics
        )
        
        try:
            if not self._analytics_client:
                return Analytics(
                    offer_id=offer_id,
                    metrics={},
                    timestamp=datetime.utcnow()
                )
            
            # Get analytics data
            data = self._analytics_client.get_metrics(
                offer_id,
                metrics
            )
            
            # Create analytics object
            analytics = Analytics(
                offer_id=offer_id,
                metrics=data.get("metrics", {}),
                timestamp=datetime.utcnow(),
                metadata={
                    "source": data.get("source"),
                    "window": data.get("window"),
                    "confidence": data.get("confidence")
                }
            )
            
            self._log_exit("get_analytics", analytics)
            return analytics
            
        except Exception as e:
            self._log_error("get_analytics", e)
            raise ValueError(f"Failed to get analytics: {str(e)}")
    
    def cleanup_history(
        self,
        offer_id: UUID,
        before: datetime
    ) -> int:
        """Clean up old history entries.
        
        Args:
            offer_id: Offer ID
            before: Timestamp to clean before
            
        Returns:
            Number of entries cleaned
            
        Raises:
            ValueError: If cleanup fails
        """
        self._log_entry(
            "cleanup_history",
            offer_id=offer_id,
            before=before
        )
        
        try:
            if not self._repository:
                return 0
            
            # Clean up old entries
            count = self._repository.delete_history(offer_id, before)
            
            self._log_exit("cleanup_history", count)
            return count
            
        except Exception as e:
            self._log_error("cleanup_history", e)
            raise ValueError(f"Failed to clean history: {str(e)}")
