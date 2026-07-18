from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.disease import DiseaseDetection
from repositories.disease import disease_repository
from schemas.disease import DiseaseLogResponse, VisionSyncRequest
from services.notification import notification_service


class DiseaseService:
    async def sync_vision(
        self, db: AsyncSession, farmer_id: UUID, payload: VisionSyncRequest
    ) -> DiseaseLogResponse:
        from repositories.plot import plot_repository
        plots = await plot_repository.get_by_h3_index(db, payload.h3_spatial_index)
        if not plots:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No plots found for H3 index {payload.h3_spatial_index}",
            )

        plot = plots[0]
        top_detection = max(payload.detections, key=lambda d: d.get("confidence", 0)) if payload.detections else None

        disease_log = await disease_repository.create(
            db,
            plot_id=plot.id,
            farmer_id=farmer_id,
            h3_spatial_index=payload.h3_spatial_index,
            detected_disease=top_detection.get("class_name") if top_detection else None,
            confidence=payload.confidence,
            detections=payload.detections,
            image_url=payload.image_url,
            raw_payload=payload.raw_payload,
            severity="unknown",
        )

        for detection in payload.detections:
            det = DiseaseDetection(
                disease_log_id=disease_log.id,
                class_name=detection.get("class_name", "unknown"),
                confidence=detection.get("confidence", 0),
                bbox=detection.get("bbox"),
            )
            db.add(det)

        await notification_service.create_notification(
            db,
            user_id=farmer_id,
            title="Disease Detected",
            body=f"Potential disease '{disease_log.detected_disease}' detected in plot {plot.name}",
            notification_type="alert",
            reference_type="disease_log",
            reference_id=disease_log.id,
        )

        await db.flush()
        return await self.get_disease_log(db, disease_log.id)

    async def get_disease_log(
        self, db: AsyncSession, log_id: UUID
    ) -> DiseaseLogResponse:
        log = await disease_repository.get_with_detections(db, log_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disease log not found")
        return DiseaseLogResponse.model_validate(log)

    async def get_logs_by_plot(
        self, db: AsyncSession, plot_id: UUID
    ) -> list[DiseaseLogResponse]:
        logs = await disease_repository.get_by_plot(db, plot_id)
        return [DiseaseLogResponse.model_validate(l) for l in logs]
